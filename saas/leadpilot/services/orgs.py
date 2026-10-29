"""Organisations (tenants), users and the default follow-up rules every new org starts with."""
from __future__ import annotations

import re
import sqlite3

from ..db import STAGES, iso, utcnow
from ..security import hash_password, new_api_key, verify_password

# key, name, stage, delay (minutes; negative = before the demo for demo_booked), action, template
DEFAULT_RULES = [
    ("first_response", "Call new inquiry within 15 minutes", "new", 15, "task", ""),
    ("new_intro", "WhatsApp intro if not reached in 1 hour", "new", 60, "draft_message",
     "Hi {first_name}, thanks for your enquiry about {exam} coaching at {org_name}. Would you like to attend "
     "a free demo class? Tell us a time that suits you. {next_batch_line}"),
    ("contacted_d1", "Day 1: invite to a free demo class", "contacted", 1440, "draft_message",
     "Hi {first_name}, this is {org_name}. A free {exam} demo class is the easiest way to see if our coaching "
     "suits you. Shall I book you a slot?"),
    ("contacted_d3", "Day 3: share the next batch", "contacted", 4320, "draft_message",
     "Hi {first_name}, just checking in from {org_name}. {next_batch_line} Would you like to try a free demo "
     "class first?"),
    ("contacted_d7", "Day 7: call once more or mark lost", "contacted", 10080, "task", ""),
    ("demo_reminder_day", "Demo reminder the day before", "demo_booked", -1440, "draft_message",
     "Hi {first_name}, a reminder of your free {exam} demo class at {org_name} on {demo_time}. Reply here if "
     "you need to change the time."),
    ("demo_reminder_2h", "Demo reminder 2 hours before", "demo_booked", -120, "draft_message",
     "Hi {first_name}, see you at {demo_time} for your {exam} demo class at {org_name}."),
    ("demo_mark", "Mark whether the student attended the demo", "demo_booked", 60, "task", ""),
    ("attended_d1", "Day after demo: ask how it went", "demo_attended", 1440, "draft_message",
     "Hi {first_name}, thanks for attending the {exam} demo class at {org_name}. How did you find it? "
     "{next_batch_line}"),
    ("attended_d3", "Day 3 after demo: call to close", "demo_attended", 4320, "task", ""),
    ("attended_d7", "Day 7 after demo: last follow-up", "demo_attended", 10080, "draft_message",
     "Hi {first_name}, {org_name} here. Are you still planning to prepare for {exam}? Happy to help you pick a "
     "batch timing that works for you."),
]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "org"


def _unique_slug(conn: sqlite3.Connection, name: str) -> str:
    base, n = slugify(name), 1
    slug = base
    while conn.execute("SELECT 1 FROM orgs WHERE slug = ?", (slug,)).fetchone():
        n += 1
        slug = f"{base}-{n}"
    return slug


def create_org(conn: sqlite3.Connection, org_name: str, admin_name: str, email: str,
               password: str) -> tuple[int, int]:
    """Create a tenant, its admin user and default rules. Returns (org_id, user_id)."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not org_name.strip():
        raise ValueError("Organisation name is required")
    now = iso(utcnow())
    conn.execute("BEGIN")
    try:
        cur = conn.execute(
            "INSERT INTO orgs (name, slug, api_key, created_at) VALUES (?, ?, ?, ?)",
            (org_name.strip(), _unique_slug(conn, org_name), new_api_key(), now))
        org_id = cur.lastrowid
        user_id = _insert_user(conn, org_id, admin_name, email, password, "admin", now)
        conn.executemany(
            "INSERT INTO followup_rules (org_id, key, name, stage, delay_minutes, action, template) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", [(org_id, *r) for r in DEFAULT_RULES])
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return org_id, user_id


def _insert_user(conn, org_id, name, email, password, role, now) -> int:
    email = email.strip().lower()
    if "@" not in email:
        raise ValueError("A valid email is required")
    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        raise ValueError("That email is already registered")
    cur = conn.execute(
        "INSERT INTO users (org_id, name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, name.strip() or email, email, hash_password(password), role, now))
    return cur.lastrowid


def add_user(conn: sqlite3.Connection, org_id: int, name: str, email: str, password: str,
             role: str = "counsellor") -> int:
    if role not in ("admin", "counsellor"):
        raise ValueError("Unknown role")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    return _insert_user(conn, org_id, name, email, password, role, iso(utcnow()))


def set_user_active(conn: sqlite3.Connection, org_id: int, user_id: int, active: bool) -> None:
    conn.execute("UPDATE users SET active = ? WHERE id = ? AND org_id = ?", (int(active), user_id, org_id))


def authenticate(conn: sqlite3.Connection, email: str, password: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM users WHERE email = ? AND active = 1",
                       (email.strip().lower(),)).fetchone()
    return row if row and verify_password(password, row["password_hash"]) else None


def get_org(conn: sqlite3.Connection, org_id: int) -> sqlite3.Row:
    return conn.execute("SELECT * FROM orgs WHERE id = ?", (org_id,)).fetchone()


def org_by_slug(conn: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM orgs WHERE slug = ?", (slug,)).fetchone()


def org_by_api_key(conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM orgs WHERE api_key = ?", (key,)).fetchone() if key else None


def org_by_wa_number(conn: sqlite3.Connection, phone_number_id: str) -> sqlite3.Row | None:
    if not phone_number_id:
        return None
    return conn.execute("SELECT * FROM orgs WHERE wa_phone_number_id = ?", (phone_number_id,)).fetchone()


def users(conn: sqlite3.Connection, org_id: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM users WHERE org_id = ? ORDER BY role, name", (org_id,)).fetchall()


def update_org(conn: sqlite3.Connection, org_id: int, **fields) -> None:
    allowed = {"name", "timezone", "wa_phone_number_id", "auto_send"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if sets:
        conn.execute(f"UPDATE orgs SET {', '.join(f'{k} = ?' for k in sets)} WHERE id = ?",
                     (*sets.values(), org_id))


def rotate_api_key(conn: sqlite3.Connection, org_id: int) -> str:
    key = new_api_key()
    conn.execute("UPDATE orgs SET api_key = ? WHERE id = ?", (key, org_id))
    return key


def rules(conn: sqlite3.Connection, org_id: int) -> list[sqlite3.Row]:
    order = "CASE stage " + " ".join(f"WHEN '{s}' THEN {i}" for i, s in enumerate(STAGES)) + " END"
    return conn.execute(f"SELECT * FROM followup_rules WHERE org_id = ? ORDER BY {order}, delay_minutes",
                        (org_id,)).fetchall()


def update_rule(conn: sqlite3.Connection, org_id: int, rule_id: int, delay_minutes: int, active: bool,
                template: str | None = None) -> None:
    rule = conn.execute("SELECT * FROM followup_rules WHERE id = ? AND org_id = ?", (rule_id, org_id)).fetchone()
    if rule is None:
        raise LookupError("Rule not found")
    if rule["stage"] != "demo_booked" and delay_minutes < 1:
        raise ValueError("Delay must be at least 1 minute")
    if template:
        from .templates import unknown_placeholders
        bad = unknown_placeholders(template)
        if bad:
            raise ValueError(f"Unknown placeholder(s): {', '.join('{' + b + '}' for b in bad)}")
    conn.execute("UPDATE followup_rules SET delay_minutes = ?, active = ?, template = COALESCE(?, template) "
                 "WHERE id = ? AND org_id = ?", (delay_minutes, int(active), template, rule_id, org_id))
