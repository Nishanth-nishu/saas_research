"""SQLite schema and connection helper. All timestamps are UTC ISO-8601 strings."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

STAGES = ["new", "contacted", "demo_booked", "demo_attended", "enrolled", "lost"]
OPEN_STAGES = ["new", "contacted", "demo_booked", "demo_attended"]
SOURCES = ["web_form", "whatsapp", "api", "csv", "manual"]
EXAMS = ["IELTS", "PTE", "TOEFL", "Duolingo", "Spoken English", "Not sure"]
SLOTS = ["morning", "afternoon", "evening", "weekend"]
MODES = ["offline", "online"]
DEMO_STATUSES = ["booked", "attended", "no_show", "cancelled"]
SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS orgs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    api_key TEXT NOT NULL UNIQUE,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    wa_phone_number_id TEXT NOT NULL DEFAULT '',
    auto_send INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES orgs(id),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'counsellor')),
    active INTEGER NOT NULL DEFAULT 1,
    last_assigned_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES orgs(id),
    name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL,
    exam TEXT NOT NULL DEFAULT '',
    target_score TEXT NOT NULL DEFAULT '',
    exam_date TEXT NOT NULL DEFAULT '',  -- YYYY-MM (month the student plans to sit the exam)
    preferred_slot TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL DEFAULT '',
    country_interest TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL DEFAULT '',
    stage TEXT NOT NULL DEFAULT 'new',
    owner_id INTEGER REFERENCES users(id),
    consent INTEGER NOT NULL DEFAULT 0,
    opted_out INTEGER NOT NULL DEFAULT 0,
    lost_reason TEXT NOT NULL DEFAULT '',
    inquiry_count INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    first_contacted_at TEXT NOT NULL DEFAULT '',
    last_contacted_at TEXT NOT NULL DEFAULT '',
    last_inbound_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_leads_org_stage ON leads(org_id, stage);
CREATE INDEX IF NOT EXISTS ix_leads_org_phone ON leads(org_id, phone);
CREATE INDEX IF NOT EXISTS ix_leads_org_email ON leads(org_id, email);
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    user_id INTEGER,
    kind TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_activities_lead ON activities(lead_id);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    user_id INTEGER,
    title TEXT NOT NULL,
    due_at TEXT NOT NULL,
    done_at TEXT NOT NULL DEFAULT '',
    rule_key TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_tasks_rule ON tasks(lead_id, rule_key) WHERE rule_key != '';
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    channel TEXT NOT NULL CHECK (channel IN ('whatsapp', 'email', 'sms')),
    direction TEXT NOT NULL CHECK (direction IN ('out', 'in')),
    body TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'sent', 'simulated', 'failed', 'received', 'discarded')),
    rule_key TEXT NOT NULL DEFAULT '',
    drafted_by TEXT NOT NULL DEFAULT '',
    provider_ref TEXT NOT NULL DEFAULT '',
    error TEXT NOT NULL DEFAULT '',
    created_by INTEGER,
    created_at TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_messages_rule ON messages(lead_id, rule_key) WHERE rule_key != '';
CREATE TABLE IF NOT EXISTS followup_rules (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    name TEXT NOT NULL,
    stage TEXT NOT NULL,
    delay_minutes INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('task', 'draft_message')),
    template TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (org_id, key)
);
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES orgs(id),
    exam TEXT NOT NULL,
    starts_on TEXT NOT NULL,             -- YYYY-MM-DD
    slot TEXT NOT NULL,
    mode TEXT NOT NULL,
    timing TEXT NOT NULL DEFAULT '',     -- free text shown to students, e.g. "7-9 AM, Mon-Fri"
    seats INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS demos (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    scheduled_at TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('booked', 'attended', 'no_show', 'cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_demos_lead ON demos(lead_id);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse(ts: str) -> datetime | None:
    return datetime.fromisoformat(ts) if ts else None


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    has_tables = conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'orgs'").fetchone()
    if has_tables and version != SCHEMA_VERSION:
        raise RuntimeError(f"Database schema v{version} is older than v{SCHEMA_VERSION} and there are no migrations "
                           "yet. For a dev database, delete the file and restart.")
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
