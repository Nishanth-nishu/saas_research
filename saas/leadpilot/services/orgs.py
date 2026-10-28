"""Organisations (tenants), users and the default follow-up rules every new org starts with."""
from __future__ import annotations

import re
import sqlite3

from ..db import STAGES, iso, utcnow
from ..security import hash_password, new_api_key, verify_password

# key, name, stage, delay (minutes), action, template
DEFAULT_RULES = [
    ("first_response", "Call new inquiry within 15 minutes", "new", 15, "task", ""),
    ("new_intro", "WhatsApp intro if still not reached after 1 hour", "new", 60, "draft_message",
     "Hi {first_name}, thanks for your inquiry with {org_name}{about}. When is a good time for a "
     "quick call with one of our counsellors?"),
    ("contacted_d1", "Day-1 follow-up after last contact", "contacted", 1440, "draft_message",
     "Hi {first_name}, following up from {org_name}. Did you get a chance to think about {topic}? "
     "Happy to answer any questions."),
    ("contacted_d3", "Day-3 follow-up after last contact", "contacted", 4320, "draft_message",
     "Hi {first_name}, just checking in from {org_name}. Would you like to book a free counselling "
     "session this week?"),
    ("contacted_d7", "Day-7: call once more or mark lost", "contacted", 10080, "task", ""),
    ("counselling_d2", "Nudge after 2 quiet days in counselling", "counselling", 2880, "draft_message",
     "Hi {first_name}, hope the counselling session was useful. Is there anything else you need "
     "from us to decide on {topic}?"),
    ("application_d5", "Check application status after 5 quiet days", "application", 7200, "task", ""),
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
    if delay_minutes < 1:
        raise ValueError("Delay must be at least 1 minute")
    conn.execute("UPDATE followup_rules SET delay_minutes = ?, active = ?, template = COALESCE(?, template) "
                 "WHERE id = ? AND org_id = ?", (delay_minutes, int(active), template, rule_id, org_id))
