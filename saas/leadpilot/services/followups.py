"""Follow-up engine: turns rules into tasks and message drafts for IELTS/PTE inquiries.

Run on a timer. It is idempotent: each rule fires at most once per lead per "anchor", so a new
contact re-arms the sequence. Anchors:
- new: when the inquiry arrived
- demo_booked: the demo's start time (negative delays are reminders before the class)
- other stages: the last real contact
When several rules of the same action are overdue for one lead (after downtime, a CSV import of
old leads, or a demo booked at short notice), only the latest fires, so a student never gets a
burst of messages.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from ..db import OPEN_STAGES, iso, parse
from . import demos as demos_svc
from . import leads as leads_svc
from .templates import context, fill


def _anchor(conn: sqlite3.Connection, lead: sqlite3.Row) -> tuple[str, sqlite3.Row | None]:
    if lead["stage"] == "demo_booked":
        demo = demos_svc.current_demo(conn, lead["id"])
        if demo:
            return demo["scheduled_at"], demo
    if lead["stage"] == "new" or not lead["last_contacted_at"]:
        return lead["created_at"], None
    return lead["last_contacted_at"], None


def _channel(lead: sqlite3.Row) -> str | None:
    return "whatsapp" if lead["phone"] else ("email" if lead["email"] else None)


def run(conn: sqlite3.Connection, now: datetime, org_id: int | None = None) -> dict:
    stats = {"tasks": 0, "drafts": 0, "skipped_no_consent": 0}
    orgs = conn.execute("SELECT * FROM orgs" + (" WHERE id = ?" if org_id else ""),
                        (org_id,) if org_id else ()).fetchall()
    for org in orgs:
        rules = conn.execute("SELECT * FROM followup_rules WHERE org_id = ? AND active = 1", (org["id"],)).fetchall()
        by_stage: dict[str, list] = {}
        for r in rules:
            by_stage.setdefault(r["stage"], []).append(r)
        open_leads = conn.execute(
            f"SELECT * FROM leads WHERE org_id = ? AND opted_out = 0 AND stage IN ({','.join('?' * len(OPEN_STAGES))})",
            (org["id"], *OPEN_STAGES)).fetchall()
        for lead in open_leads:
            anchor, demo = _anchor(conn, lead)
            anchor_dt = parse(anchor)
            for action in ("task", "draft_message"):
                due = [r for r in by_stage.get(lead["stage"], []) if r["action"] == action
                       and anchor_dt + timedelta(minutes=r["delay_minutes"]) <= now]
                if demo is not None:
                    # A reminder that fell due before the booking was made is never sent,
                    # and a reminder is pointless once the class has started
                    booked_at = parse(demo["created_at"])
                    due = [r for r in due if anchor_dt + timedelta(minutes=r["delay_minutes"]) >= booked_at
                           and (r["delay_minutes"] >= 0 or now < anchor_dt)]
                if not due:
                    continue
                rule = max(due, key=lambda r: r["delay_minutes"])
                key = f"{rule['key']}@{anchor}"
                if action == "task":
                    stats["tasks"] += _make_task(conn, org, lead, rule, key, anchor_dt, now)
                else:
                    # The student wrote after our last contact: we owe a reply, not a chaser
                    if demo is None and lead["last_inbound_at"] and lead["last_inbound_at"] > anchor:
                        continue
                    # Demo reminders are part of a booking the student agreed to on a call
                    if not (lead["consent"] or lead["source"] == "whatsapp" or demo is not None):
                        stats["skipped_no_consent"] += 1
                        continue
                    stats["drafts"] += _make_draft(conn, org, lead, rule, key, now)
    return stats


def _make_task(conn, org, lead, rule, key, anchor_dt, now) -> int:
    due = anchor_dt + timedelta(minutes=rule["delay_minutes"])
    cur = conn.execute(
        "INSERT OR IGNORE INTO tasks (org_id, lead_id, user_id, title, due_at, rule_key, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (org["id"], lead["id"], lead["owner_id"], rule["name"], iso(due), key, iso(now)))
    if cur.rowcount:
        leads_svc.log(conn, org["id"], lead["id"], "task", f"Task created: {rule['name']}", now)
    return cur.rowcount


def _make_draft(conn, org, lead, rule, key, now) -> int:
    channel = _channel(lead)
    if channel is None or not rule["template"]:
        return 0
    body = fill(rule["template"], context(conn, lead, org, now))
    cur = conn.execute(
        "INSERT OR IGNORE INTO messages (org_id, lead_id, channel, direction, body, status, rule_key, drafted_by, created_at) "
        "VALUES (?, ?, ?, 'out', ?, 'draft', ?, 'template', ?)",
        (org["id"], lead["id"], channel, body, key, iso(now)))
    if cur.rowcount:
        leads_svc.log(conn, org["id"], lead["id"], "draft", f"Follow-up drafted ({rule['name']})", now)
        # Older unsent rule drafts for this lead are now stale (drafts a person wrote are kept)
        conn.execute("UPDATE messages SET status = 'discarded' WHERE lead_id = ? AND status = 'draft' "
                     "AND rule_key != '' AND id != ?", (lead["id"], cur.lastrowid))
    return cur.rowcount


def complete_task(conn: sqlite3.Connection, org_id: int, task_id: int, now: datetime,
                  user_id: int | None = None) -> None:
    task = conn.execute("SELECT * FROM tasks WHERE id = ? AND org_id = ?", (task_id, org_id)).fetchone()
    if task is None:
        raise LookupError("Task not found")
    if not task["done_at"]:
        conn.execute("UPDATE tasks SET done_at = ? WHERE id = ?", (iso(now), task_id))
        leads_svc.log(conn, org_id, task["lead_id"], "task_done", f"Done: {task['title']}", now, user_id)


def add_task(conn: sqlite3.Connection, org_id: int, lead_id: int, title: str, due: datetime, now: datetime,
             user_id: int | None = None) -> int:
    lead = leads_svc.get(conn, org_id, lead_id)
    if lead is None:
        raise LookupError("Lead not found")
    cur = conn.execute("INSERT INTO tasks (org_id, lead_id, user_id, title, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (org_id, lead_id, lead["owner_id"] or user_id, title.strip() or "Follow up", iso(due), iso(now)))
    return cur.lastrowid


def open_tasks(conn: sqlite3.Connection, org_id: int, user_id: int | None = None, limit: int = 200):
    sql = ("SELECT t.*, l.name AS lead_name, l.phone AS lead_phone, l.stage AS lead_stage, u.name AS user_name "
           "FROM tasks t JOIN leads l ON l.id = t.lead_id LEFT JOIN users u ON u.id = t.user_id "
           "WHERE t.org_id = ? AND t.done_at = ''")
    args: list = [org_id]
    if user_id:
        sql += " AND t.user_id = ?"
        args.append(user_id)
    sql += " ORDER BY t.due_at LIMIT ?"
    args.append(limit)
    return conn.execute(sql, args).fetchall()
