"""Lead capture, de-duplication, round-robin assignment, stage changes and the activity timeline."""
from __future__ import annotations

import csv
import io
import re
import sqlite3
from datetime import datetime

from ..db import OPEN_STAGES, SOURCES, STAGES, iso

CONTACT_KINDS = {"call", "whatsapp", "email", "meeting"}  # kinds that count as real contact
LEAD_FIELDS = ["name", "phone", "email", "course_interest", "country_interest", "intake", "message"]
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def normalize_phone(raw: str, default_cc: str = "91") -> str:
    """Digits-only E.164 without '+'. A bare 10-digit number is assumed to be Indian."""
    digits = re.sub(r"\D", "", raw or "")
    if (raw or "").strip().startswith("00"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10:
        digits = default_cc + digits
    return digits if 8 <= len(digits) <= 15 else ""


def normalize_email(raw: str) -> str:
    email = (raw or "").strip().lower()
    return email if _EMAIL.match(email) else ""


def log(conn: sqlite3.Connection, org_id: int, lead_id: int, kind: str, body: str, now: datetime,
        user_id: int | None = None) -> None:
    conn.execute("INSERT INTO activities (org_id, lead_id, user_id, kind, body, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                 (org_id, lead_id, user_id, kind, body, iso(now)))


def next_assignee(conn: sqlite3.Connection, org_id: int, now: datetime) -> int | None:
    """Round robin: the active counsellor assigned least recently. Falls back to admins."""
    for role in ("counsellor", "admin"):
        row = conn.execute("SELECT id FROM users WHERE org_id = ? AND role = ? AND active = 1 "
                           "ORDER BY last_assigned_at, id LIMIT 1", (org_id, role)).fetchone()
        if row:
            conn.execute("UPDATE users SET last_assigned_at = ? WHERE id = ?", (iso(now), row["id"]))
            return row["id"]
    return None


def find_duplicate(conn: sqlite3.Connection, org_id: int, phone: str, email: str) -> sqlite3.Row | None:
    if phone:
        row = conn.execute("SELECT * FROM leads WHERE org_id = ? AND phone = ? ORDER BY id LIMIT 1",
                           (org_id, phone)).fetchone()
        if row:
            return row
    if email:
        return conn.execute("SELECT * FROM leads WHERE org_id = ? AND email = ? ORDER BY id LIMIT 1",
                            (org_id, email)).fetchone()
    return None


def capture(conn: sqlite3.Connection, org_id: int, data: dict, source: str, now: datetime,
            user_id: int | None = None) -> tuple[int, bool]:
    """Create a lead, or merge into an existing one with the same phone/email.

    Returns (lead_id, created). Raises ValueError when there is no usable phone or email.
    """
    if source not in SOURCES:
        raise ValueError(f"Unknown source {source!r}")
    phone, email = normalize_phone(data.get("phone", "")), normalize_email(data.get("email", ""))
    if not phone and not email:
        raise ValueError("A valid phone number or email is required")
    clean = {f: str(data.get(f, "") or "").strip()[:2000] for f in LEAD_FIELDS}
    clean.update(phone=phone, email=email)
    consent = 1 if data.get("consent") in (True, 1, "1", "on", "yes", "true") else 0

    existing = find_duplicate(conn, org_id, phone, email)
    if existing:
        updates = {f: clean[f] for f in LEAD_FIELDS if clean[f] and not existing[f]}
        updates["inquiry_count"] = existing["inquiry_count"] + 1
        updates["updated_at"] = iso(now)
        updates["consent"] = max(existing["consent"], consent)
        if existing["stage"] == "lost":
            updates["stage"] = "new"  # a lost lead asking again is a fresh opportunity
            updates["lost_reason"] = ""
        conn.execute(f"UPDATE leads SET {', '.join(f'{k} = ?' for k in updates)} WHERE id = ?",
                     (*updates.values(), existing["id"]))
        note = f"Asked again via {source}" + (f": {clean['message'][:200]}" if clean["message"] else "")
        if updates.get("stage") == "new":
            note += " (reopened from lost)"
        log(conn, org_id, existing["id"], "re_inquiry", note, now, user_id)
        return existing["id"], False

    owner = next_assignee(conn, org_id, now)
    cur = conn.execute(
        "INSERT INTO leads (org_id, name, phone, email, source, course_interest, country_interest, intake, "
        "message, owner_id, consent, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (org_id, clean["name"], phone, email, source, clean["course_interest"], clean["country_interest"],
         clean["intake"], clean["message"], owner, consent, iso(now), iso(now)))
    lead_id = cur.lastrowid
    log(conn, org_id, lead_id, "created", f"New inquiry via {source}", now, user_id)
    if owner:
        name = conn.execute("SELECT name FROM users WHERE id = ?", (owner,)).fetchone()["name"]
        log(conn, org_id, lead_id, "assigned", f"Assigned to {name} (round robin)", now)
    return lead_id, True


def get(conn: sqlite3.Connection, org_id: int, lead_id: int) -> sqlite3.Row | None:
    """Tenant-scoped fetch: a lead from another org is treated as missing."""
    return conn.execute("SELECT * FROM leads WHERE id = ? AND org_id = ?", (lead_id, org_id)).fetchone()


def search(conn: sqlite3.Connection, org_id: int, stage: str = "", owner_id: str = "", source: str = "",
           q: str = "", limit: int = 200) -> list[sqlite3.Row]:
    sql = ("SELECT l.*, u.name AS owner_name FROM leads l LEFT JOIN users u ON u.id = l.owner_id "
           "WHERE l.org_id = ?")
    args: list = [org_id]
    if stage == "open":
        sql += f" AND l.stage IN ({','.join('?' * len(OPEN_STAGES))})"
        args += OPEN_STAGES
    elif stage:
        sql += " AND l.stage = ?"
        args.append(stage)
    if owner_id:
        sql += " AND l.owner_id = ?"
        args.append(int(owner_id))
    if source:
        sql += " AND l.source = ?"
        args.append(source)
    if q:
        sql += " AND (l.name LIKE ? OR l.phone LIKE ? OR l.email LIKE ? OR l.course_interest LIKE ?)"
        args += [f"%{q}%"] * 4
    sql += " ORDER BY l.updated_at DESC LIMIT ?"
    args.append(limit)
    return conn.execute(sql, args).fetchall()


def set_stage(conn: sqlite3.Connection, org_id: int, lead_id: int, stage: str, now: datetime,
              user_id: int | None = None, lost_reason: str = "") -> None:
    if stage not in STAGES:
        raise ValueError(f"Unknown stage {stage!r}")
    lead = get(conn, org_id, lead_id)
    if lead is None:
        raise LookupError("Lead not found")
    if stage == "lost" and not lost_reason.strip():
        raise ValueError("Give a reason when marking a lead lost")
    if lead["stage"] == stage:
        return
    conn.execute("UPDATE leads SET stage = ?, lost_reason = ?, updated_at = ? WHERE id = ?",
                 (stage, lost_reason.strip() if stage == "lost" else "", iso(now), lead_id))
    log(conn, org_id, lead_id, "stage", f"{lead['stage']} → {stage}" + (f" ({lost_reason})" if stage == "lost" else ""),
        now, user_id)
    if stage in ("lost", "enrolled"):
        _close_open_work(conn, lead_id, now)


def _close_open_work(conn: sqlite3.Connection, lead_id: int, now: datetime) -> None:
    conn.execute("UPDATE tasks SET done_at = ? WHERE lead_id = ? AND done_at = ''", (iso(now), lead_id))
    conn.execute("UPDATE messages SET status = 'discarded' WHERE lead_id = ? AND status = 'draft'", (lead_id,))


def record_contact(conn: sqlite3.Connection, org_id: int, lead_id: int, kind: str, body: str, now: datetime,
                   user_id: int | None = None) -> None:
    """Log a call/meeting/message that actually happened. 'note' does not count as contact."""
    lead = get(conn, org_id, lead_id)
    if lead is None:
        raise LookupError("Lead not found")
    log(conn, org_id, lead_id, kind, body, now, user_id)
    if kind not in CONTACT_KINDS:
        return
    updates = {"last_contacted_at": iso(now), "updated_at": iso(now)}
    if not lead["first_contacted_at"]:
        updates["first_contacted_at"] = iso(now)
    if lead["stage"] == "new":
        updates["stage"] = "contacted"
    conn.execute(f"UPDATE leads SET {', '.join(f'{k} = ?' for k in updates)} WHERE id = ?",
                 (*updates.values(), lead_id))
    if lead["stage"] == "new":
        log(conn, org_id, lead_id, "stage", "new → contacted", now, user_id)
    # Contact satisfies any open follow-up task for this lead that is already due
    conn.execute("UPDATE tasks SET done_at = ? WHERE lead_id = ? AND done_at = '' AND due_at <= ?",
                 (iso(now), lead_id, iso(now)))


def reassign(conn: sqlite3.Connection, org_id: int, lead_id: int, owner_id: int, now: datetime,
             user_id: int | None = None) -> None:
    owner = conn.execute("SELECT * FROM users WHERE id = ? AND org_id = ? AND active = 1",
                         (owner_id, org_id)).fetchone()
    if owner is None or get(conn, org_id, lead_id) is None:
        raise LookupError("Lead or user not found")
    conn.execute("UPDATE leads SET owner_id = ?, updated_at = ? WHERE id = ?", (owner_id, iso(now), lead_id))
    conn.execute("UPDATE tasks SET user_id = ? WHERE lead_id = ? AND done_at = ''", (owner_id, lead_id))
    log(conn, org_id, lead_id, "assigned", f"Reassigned to {owner['name']}", now, user_id)


def opt_out(conn: sqlite3.Connection, org_id: int, lead_id: int, now: datetime, user_id: int | None = None,
            reason: str = "Asked not to be contacted") -> None:
    if get(conn, org_id, lead_id) is None:
        raise LookupError("Lead not found")
    conn.execute("UPDATE leads SET opted_out = 1, updated_at = ? WHERE id = ?", (iso(now), lead_id))
    conn.execute("UPDATE messages SET status = 'discarded' WHERE lead_id = ? AND status = 'draft'", (lead_id,))
    log(conn, org_id, lead_id, "opt_out", reason, now, user_id)


def timeline(conn: sqlite3.Connection, lead_id: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT a.*, u.name AS user_name FROM activities a LEFT JOIN users u ON u.id = a.user_id "
                        "WHERE a.lead_id = ? ORDER BY a.id DESC", (lead_id,)).fetchall()


CSV_ALIASES = {
    "name": ["name", "full name", "student name", "lead name"],
    "phone": ["phone", "mobile", "phone number", "whatsapp", "contact"],
    "email": ["email", "email address", "e-mail"],
    "course_interest": ["course", "course interest", "program", "programme", "exam"],
    "country_interest": ["country", "destination", "country interest"],
    "intake": ["intake", "session", "batch"],
    "message": ["message", "notes", "remarks", "query"],
    "consent": ["consent", "opt in", "opt-in"],
}


def import_csv(conn: sqlite3.Connection, org_id: int, text: str, now: datetime,
               user_id: int | None = None) -> dict:
    """Import leads from a spreadsheet export. Returns counts and per-row errors."""
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    headers = {h.strip().lower(): h for h in (reader.fieldnames or [])}
    mapping = {field: headers[a] for field, aliases in CSV_ALIASES.items() for a in aliases if a in headers}
    if "phone" not in mapping and "email" not in mapping:
        raise ValueError("CSV needs a phone or email column")
    result = {"created": 0, "merged": 0, "errors": []}
    for i, row in enumerate(reader, start=2):
        data = {field: row.get(col, "") for field, col in mapping.items()}
        try:
            _, created = capture(conn, org_id, data, "csv", now, user_id)
            result["created" if created else "merged"] += 1
        except ValueError as e:
            result["errors"].append(f"Row {i}: {e}")
    return result
