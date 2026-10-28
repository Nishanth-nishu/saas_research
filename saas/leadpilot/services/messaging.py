"""Outbound and inbound messages.

Sending is always an explicit action (a person clicks Send, or the org has turned on auto-send).
Without WhatsApp credentials every send is *simulated*: it is recorded as such and does NOT count
as contact with the lead, so the timeline never claims a message went out when it didn't.

WhatsApp rule enforced here: free-form text is only allowed within 24 hours of the student's last
message to you. Outside that window Meta requires a pre-approved template, which is not built yet.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta

import httpx

from ..config import Settings
from ..db import iso, parse
from . import leads as leads_svc

log = logging.getLogger("leadpilot.messaging")
WHATSAPP_WINDOW = timedelta(hours=24)
GRAPH_URL = "https://graph.facebook.com/v21.0/{phone_number_id}/messages"
STOP_WORDS = {"stop", "unsubscribe", "stop all", "opt out", "optout"}


def in_whatsapp_window(lead: sqlite3.Row, now: datetime) -> bool:
    last_in = parse(lead["last_inbound_at"])
    return bool(last_in and now - last_in <= WHATSAPP_WINDOW)


def create_draft(conn: sqlite3.Connection, org_id: int, lead_id: int, channel: str, body: str, now: datetime,
                 user_id: int | None = None, drafted_by: str = "human") -> int:
    lead = leads_svc.get(conn, org_id, lead_id)
    if lead is None:
        raise LookupError("Lead not found")
    if not body.strip():
        raise ValueError("Message is empty")
    cur = conn.execute(
        "INSERT INTO messages (org_id, lead_id, channel, direction, body, status, drafted_by, created_by, created_at) "
        "VALUES (?, ?, ?, 'out', ?, 'draft', ?, ?, ?)", (org_id, lead_id, channel, body.strip(), drafted_by, user_id, iso(now)))
    return cur.lastrowid


def update_draft(conn: sqlite3.Connection, org_id: int, msg_id: int, body: str) -> None:
    conn.execute("UPDATE messages SET body = ? WHERE id = ? AND org_id = ? AND status = 'draft'",
                 (body.strip(), msg_id, org_id))


def discard(conn: sqlite3.Connection, org_id: int, msg_id: int) -> None:
    conn.execute("UPDATE messages SET status = 'discarded' WHERE id = ? AND org_id = ? AND status = 'draft'",
                 (msg_id, org_id))


def send(conn: sqlite3.Connection, settings: Settings, org_id: int, msg_id: int, now: datetime,
         user_id: int | None = None, http: httpx.Client | None = None) -> str:
    """Send one draft. Returns the resulting status: sent, simulated or failed."""
    msg = conn.execute("SELECT * FROM messages WHERE id = ? AND org_id = ?", (msg_id, org_id)).fetchone()
    if msg is None or msg["status"] != "draft":
        raise LookupError("Draft not found")
    lead = leads_svc.get(conn, org_id, msg["lead_id"])
    org = conn.execute("SELECT * FROM orgs WHERE id = ?", (org_id,)).fetchone()

    status, ref, error = "failed", "", ""
    if lead["opted_out"]:
        error = "Lead has opted out"
    elif msg["channel"] == "whatsapp":
        if not lead["phone"]:
            error = "Lead has no phone number"
        elif not (settings.wa_access_token and org["wa_phone_number_id"]):
            status = "simulated"
        elif not in_whatsapp_window(lead, now):
            error = ("Outside WhatsApp's 24-hour reply window: an approved template message is required "
                     "(not supported yet). Call the student instead.")
        else:
            status, ref, error = _send_whatsapp(settings, org["wa_phone_number_id"], lead["phone"], msg["body"], http)
    else:
        status = "simulated"  # email/SMS providers are not connected yet

    conn.execute("UPDATE messages SET status = ?, provider_ref = ?, error = ?, sent_at = ? WHERE id = ?",
                 (status, ref, error, iso(now) if status in ("sent", "simulated") else "", msg_id))
    if status == "sent":
        leads_svc.record_contact(conn, org_id, lead["id"], msg["channel"], msg["body"], now, user_id)
    elif status == "simulated":
        leads_svc.log(conn, org_id, lead["id"], "simulated",
                      f"[Dry run, not delivered] {msg['channel']}: {msg['body']}", now, user_id)
    else:
        leads_svc.log(conn, org_id, lead["id"], "send_failed", error, now, user_id)
    return status


def _send_whatsapp(settings: Settings, phone_number_id: str, to: str, body: str,
                   http: httpx.Client | None) -> tuple[str, str, str]:
    client = http or httpx.Client(timeout=15)
    try:
        r = client.post(GRAPH_URL.format(phone_number_id=phone_number_id),
                        headers={"Authorization": f"Bearer {settings.wa_access_token}"},
                        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}})
        if r.status_code >= 400:
            return "failed", "", f"WhatsApp API {r.status_code}: {r.text[:300]}"
        return "sent", (r.json().get("messages") or [{}])[0].get("id", ""), ""
    except httpx.HTTPError as e:
        log.warning("WhatsApp send failed: %s", e)
        return "failed", "", f"Network error: {e}"
    finally:
        if http is None:
            client.close()


def parse_whatsapp_webhook(payload: dict) -> list[dict]:
    """Extract inbound text messages from a Meta webhook payload."""
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            pnid = value.get("metadata", {}).get("phone_number_id", "")
            names = {c.get("wa_id"): c.get("profile", {}).get("name", "") for c in value.get("contacts", [])}
            for m in value.get("messages", []):
                text = m.get("text", {}).get("body", "") if m.get("type") == "text" else f"[{m.get('type')} message]"
                out.append({"phone_number_id": pnid, "from": m.get("from", ""), "name": names.get(m.get("from"), ""),
                            "text": text, "id": m.get("id", "")})
    return out


def record_inbound(conn: sqlite3.Connection, org_id: int, phone: str, name: str, text: str, now: datetime,
                   provider_ref: str = "") -> int:
    """Store an inbound WhatsApp message, creating or merging the lead, and queue a reply task."""
    if provider_ref and conn.execute("SELECT 1 FROM messages WHERE provider_ref = ? AND direction = 'in'",
                                     (provider_ref,)).fetchone():
        return conn.execute("SELECT lead_id FROM messages WHERE provider_ref = ?", (provider_ref,)).fetchone()[0]
    lead_id, _ = leads_svc.capture(conn, org_id, {"phone": phone, "name": name, "message": text}, "whatsapp", now)
    conn.execute("INSERT INTO messages (org_id, lead_id, channel, direction, body, status, provider_ref, created_at) "
                 "VALUES (?, ?, 'whatsapp', 'in', ?, 'received', ?, ?)", (org_id, lead_id, text, provider_ref, iso(now)))
    conn.execute("UPDATE leads SET last_inbound_at = ?, updated_at = ? WHERE id = ?", (iso(now), iso(now), lead_id))
    leads_svc.log(conn, org_id, lead_id, "inbound", f"WhatsApp: {text[:500]}", now)
    if text.strip().lower() in STOP_WORDS:
        leads_svc.opt_out(conn, org_id, lead_id, now, reason=f"Replied '{text.strip()}' on WhatsApp")
        return lead_id
    lead = leads_svc.get(conn, org_id, lead_id)
    conn.execute("INSERT OR IGNORE INTO tasks (org_id, lead_id, user_id, title, due_at, rule_key, created_at) "
                 "VALUES (?, ?, ?, 'Reply to WhatsApp message', ?, ?, ?)",
                 (org_id, lead_id, lead["owner_id"], iso(now + timedelta(minutes=15)), f"inbound@{iso(now)}", iso(now)))
    return lead_id


def for_lead(conn: sqlite3.Connection, lead_id: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM messages WHERE lead_id = ? AND status != 'discarded' ORDER BY id DESC",
                        (lead_id,)).fetchall()


def drafts(conn: sqlite3.Connection, org_id: int, user_id: int | None = None) -> list[sqlite3.Row]:
    sql = ("SELECT m.*, l.name AS lead_name, l.phone AS lead_phone, l.last_inbound_at, l.owner_id, u.name AS owner_name "
           "FROM messages m JOIN leads l ON l.id = m.lead_id LEFT JOIN users u ON u.id = l.owner_id "
           "WHERE m.org_id = ? AND m.status = 'draft'")
    args: list = [org_id]
    if user_id:
        sql += " AND l.owner_id = ?"
        args.append(user_id)
    return conn.execute(sql + " ORDER BY m.created_at", args).fetchall()


def auto_send_due(conn: sqlite3.Connection, settings: Settings, now: datetime) -> int:
    """For orgs that opted into auto-send, send drafts the engine created (never human drafts)."""
    sent = 0
    for m in conn.execute("SELECT m.id, m.org_id FROM messages m JOIN orgs o ON o.id = m.org_id "
                          "WHERE o.auto_send = 1 AND m.status = 'draft' AND m.rule_key != ''").fetchall():
        sent += send(conn, settings, m["org_id"], m["id"], now) in ("sent", "simulated")
    return sent
