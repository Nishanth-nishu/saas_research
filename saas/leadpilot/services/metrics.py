"""Dashboard numbers: the ones an owner needs to see whether inquiries are being followed up."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from statistics import median

from ..db import OPEN_STAGES, STAGES, iso, parse


def dashboard(conn: sqlite3.Connection, org_id: int, now: datetime, days: int = 30) -> dict:
    since = iso(now - timedelta(days=days))
    leads = conn.execute("SELECT * FROM leads WHERE org_id = ? AND created_at >= ?", (org_id, since)).fetchall()

    response_mins = [(parse(l["first_contacted_at"]) - parse(l["created_at"])).total_seconds() / 60
                     for l in leads if l["first_contacted_at"]]
    open_ph = ",".join("?" * len(OPEN_STAGES))
    untouched = conn.execute(f"SELECT COUNT(*) FROM leads WHERE org_id = ? AND first_contacted_at = '' "
                             f"AND opted_out = 0 AND stage IN ({open_ph})", (org_id, *OPEN_STAGES)).fetchone()[0]
    overdue = conn.execute("SELECT COUNT(*) FROM tasks WHERE org_id = ? AND done_at = '' AND due_at < ?",
                           (org_id, iso(now))).fetchone()[0]
    drafts = conn.execute("SELECT COUNT(*) FROM messages WHERE org_id = ? AND status = 'draft'", (org_id,)).fetchone()[0]

    by_source: dict[str, dict] = {}
    for l in leads:
        s = by_source.setdefault(l["source"], {"leads": 0, "contacted": 0, "enrolled": 0})
        s["leads"] += 1
        s["contacted"] += bool(l["first_contacted_at"])
        s["enrolled"] += l["stage"] == "enrolled"

    by_counsellor = conn.execute(
        f"""SELECT u.name, COUNT(l.id) AS open_leads,
                   SUM(CASE WHEN l.first_contacted_at = '' THEN 1 ELSE 0 END) AS untouched,
                   (SELECT COUNT(*) FROM tasks t WHERE t.user_id = u.id AND t.done_at = '' AND t.due_at < ?) AS overdue
            FROM users u LEFT JOIN leads l ON l.owner_id = u.id AND l.stage IN ({open_ph}) AND l.opted_out = 0
            WHERE u.org_id = ? AND u.active = 1 GROUP BY u.id ORDER BY u.name""",
        (iso(now), *OPEN_STAGES, org_id)).fetchall()

    return {
        "days": days,
        "new_leads": len(leads),
        "today": sum(1 for l in leads if parse(l["created_at"]) >= now - timedelta(hours=24)),
        "median_response_min": round(median(response_mins)) if response_mins else None,
        "within_15_min_pct": round(100 * sum(m <= 15 for m in response_mins) / len(leads)) if leads else None,
        "untouched": untouched,
        "overdue_tasks": overdue,
        "drafts_waiting": drafts,
        "stages": {s: sum(1 for l in leads if l["stage"] == s) for s in STAGES},
        "by_source": by_source,
        "by_counsellor": by_counsellor,
    }
