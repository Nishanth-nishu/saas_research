"""Free demo classes and upcoming batches: how IELTS/PTE centres actually convert inquiries.

Funnel: inquiry → demo booked → demo attended → enrolled in a batch. A no-show sends the lead back
to 'contacted' with a call-to-reschedule task, so it re-enters the follow-up sequence.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

from ..db import EXAMS, MODES, SLOTS, iso, parse
from . import leads as leads_svc


# ---------- batches ----------
def add_batch(conn: sqlite3.Connection, org_id: int, exam: str, starts_on: str, slot: str, mode: str,
              timing: str, seats: int, now: datetime) -> int:
    if exam not in EXAMS or slot not in SLOTS or mode not in MODES:
        raise ValueError("Pick an exam, slot and mode from the lists")
    try:
        date.fromisoformat(starts_on)
    except ValueError:
        raise ValueError("Start date must be a date") from None
    cur = conn.execute("INSERT INTO batches (org_id, exam, starts_on, slot, mode, timing, seats, created_at) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (org_id, exam, starts_on, slot, mode, timing.strip()[:80], max(0, seats), iso(now)))
    return cur.lastrowid


def set_batch_active(conn: sqlite3.Connection, org_id: int, batch_id: int, active: bool) -> None:
    conn.execute("UPDATE batches SET active = ? WHERE id = ? AND org_id = ?", (int(active), batch_id, org_id))


def batches(conn: sqlite3.Connection, org_id: int, upcoming_from: str | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM batches WHERE org_id = ?"
    args: list = [org_id]
    if upcoming_from:
        sql += " AND active = 1 AND starts_on >= ?"
        args.append(upcoming_from)
    return conn.execute(sql + " ORDER BY starts_on, slot", args).fetchall()


def next_batch(conn: sqlite3.Connection, lead: sqlite3.Row, today: str) -> sqlite3.Row | None:
    """The soonest active batch for the lead's exam, preferring their slot and mode when known."""
    if not lead["exam"]:
        return None
    rows = conn.execute("SELECT * FROM batches WHERE org_id = ? AND exam = ? AND active = 1 AND starts_on >= ? "
                        "ORDER BY starts_on", (lead["org_id"], lead["exam"], today)).fetchall()

    def fit(b):
        return ((lead["preferred_slot"] or b["slot"]) == b["slot"], (lead["mode"] or b["mode"]) == b["mode"])
    preferred = [b for b in rows if all(fit(b))]
    return (preferred or rows or [None])[0]


# ---------- demos ----------
def current_demo(conn: sqlite3.Connection, lead_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM demos WHERE lead_id = ? AND status = 'booked' ORDER BY id DESC LIMIT 1",
                        (lead_id,)).fetchone()


def for_lead(conn: sqlite3.Connection, lead_id: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM demos WHERE lead_id = ? ORDER BY scheduled_at DESC", (lead_id,)).fetchall()


def book(conn: sqlite3.Connection, org_id: int, lead_id: int, scheduled_at: datetime, mode: str, now: datetime,
         user_id: int | None = None) -> int:
    lead = leads_svc.get(conn, org_id, lead_id)
    if lead is None:
        raise LookupError("Lead not found")
    if lead["stage"] in ("enrolled", "lost"):
        raise ValueError(f"Lead is {lead['stage']}; reopen it before booking a demo")
    if scheduled_at <= now:
        raise ValueError("Demo time must be in the future")
    if mode not in MODES:
        raise ValueError("Pick online or offline")
    # Rebooking replaces the previous booking
    conn.execute("UPDATE demos SET status = 'cancelled', updated_at = ? WHERE lead_id = ? AND status = 'booked'",
                 (iso(now), lead_id))
    cur = conn.execute("INSERT INTO demos (org_id, lead_id, scheduled_at, mode, status, created_at, updated_at) "
                       "VALUES (?, ?, ?, ?, 'booked', ?, ?)", (org_id, lead_id, iso(scheduled_at), mode, iso(now), iso(now)))
    # Booking a demo means someone spoke to the student
    leads_svc.record_contact(conn, org_id, lead_id, "call", f"Demo booked ({mode})", now, user_id)
    leads_svc.set_stage(conn, org_id, lead_id, "demo_booked", now, user_id)
    return cur.lastrowid


def mark(conn: sqlite3.Connection, org_id: int, demo_id: int, status: str, now: datetime,
         user_id: int | None = None) -> None:
    demo = conn.execute("SELECT * FROM demos WHERE id = ? AND org_id = ?", (demo_id, org_id)).fetchone()
    if demo is None or demo["status"] != "booked":
        raise LookupError("No open demo booking")
    if status not in ("attended", "no_show", "cancelled"):
        raise ValueError("Unknown demo status")
    if status != "cancelled" and parse(demo["scheduled_at"]) > now + timedelta(minutes=30):
        raise ValueError("The demo hasn't happened yet")
    conn.execute("UPDATE demos SET status = ?, updated_at = ? WHERE id = ?", (status, iso(now), demo_id))
    lead_id = demo["lead_id"]
    if status == "attended":
        leads_svc.record_contact(conn, org_id, lead_id, "meeting", "Attended demo class", now, user_id)
        leads_svc.set_stage(conn, org_id, lead_id, "demo_attended", now, user_id)
    else:
        label = "Did not attend demo" if status == "no_show" else "Demo cancelled"
        leads_svc.log(conn, org_id, lead_id, "demo", label, now, user_id)
        leads_svc.set_stage(conn, org_id, lead_id, "contacted", now, user_id)
        if status == "no_show":
            lead = leads_svc.get(conn, org_id, lead_id)
            conn.execute("INSERT INTO tasks (org_id, lead_id, user_id, title, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                         (org_id, lead_id, lead["owner_id"], "Call to reschedule missed demo",
                          iso(now + timedelta(hours=2)), iso(now)))
    conn.execute("UPDATE messages SET status = 'discarded' WHERE lead_id = ? AND status = 'draft' AND rule_key LIKE 'demo_%'",
                 (lead_id,))


def upcoming(conn: sqlite3.Connection, org_id: int, now: datetime, hours: int = 48) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT d.*, l.name AS lead_name, l.phone AS lead_phone, l.exam, u.name AS owner_name FROM demos d "
        "JOIN leads l ON l.id = d.lead_id LEFT JOIN users u ON u.id = l.owner_id "
        "WHERE d.org_id = ? AND d.status = 'booked' AND d.scheduled_at <= ? ORDER BY d.scheduled_at",
        (org_id, iso(now + timedelta(hours=hours)))).fetchall()


def funnel(conn: sqlite3.Connection, org_id: int, since: str) -> dict:
    """Demo funnel for leads created since `since`: booked, attended, no-show, enrolled after demo."""
    rows = conn.execute(
        "SELECT l.id, l.stage, l.exam, MAX(d.status = 'attended') AS attended, MAX(d.status = 'no_show') AS no_show, "
        "COUNT(d.id) AS demos FROM leads l LEFT JOIN demos d ON d.lead_id = l.id AND d.status != 'cancelled' "
        "WHERE l.org_id = ? AND l.created_at >= ? GROUP BY l.id", (org_id, since)).fetchall()
    booked = [r for r in rows if r["demos"]]
    attended = [r for r in booked if r["attended"]]
    by_exam: dict[str, dict] = {}
    for r in rows:
        e = by_exam.setdefault(r["exam"] or "Not given", {"leads": 0, "demos": 0, "attended": 0, "enrolled": 0})
        e["leads"] += 1
        e["demos"] += bool(r["demos"])
        e["attended"] += bool(r["attended"])
        e["enrolled"] += r["stage"] == "enrolled"
    no_show = sum(1 for r in booked if r["no_show"] and not r["attended"])
    resolved = len(attended) + no_show  # demos still upcoming don't count against the show-up rate
    return {
        "leads": len(rows), "booked": len(booked), "attended": len(attended), "no_show": no_show,
        "enrolled_after_demo": sum(1 for r in attended if r["stage"] == "enrolled"),
        "show_rate": round(100 * len(attended) / resolved) if resolved else None,
        "close_rate": round(100 * sum(1 for r in attended if r["stage"] == "enrolled") / len(attended)) if attended else None,
        "by_exam": dict(sorted(by_exam.items(), key=lambda kv: -kv[1]["leads"])),
    }
