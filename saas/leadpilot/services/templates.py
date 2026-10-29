"""Fill message templates from lead, demo and batch data without inventing anything that isn't stored."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from ..db import parse

PLACEHOLDERS = ["first_name", "org_name", "exam", "demo_time", "next_batch", "next_batch_line", "target_score"]


class _Blank(dict):
    def __missing__(self, key):  # unknown placeholders render empty rather than crash a run
        return ""


def first_name(lead) -> str:
    name = (lead["name"] or "").strip()
    return name.split()[0].title() if name else "there"


def exam_label(lead) -> str:
    exam = lead["exam"]
    return exam if exam and exam != "Not sure" else "English test"


def _when(ts: str, tz: str) -> str:
    dt = parse(ts).astimezone(ZoneInfo(tz))
    return dt.strftime("%a %d %b, %I:%M %p").replace(" 0", " ")


def batch_text(batch, tz: str = "Asia/Kolkata") -> str:
    d = datetime.fromisoformat(batch["starts_on"]).strftime("%a %d %b").replace(" 0", " ")
    timing = f", {batch['timing']}" if batch["timing"] else ""
    return f"{d} ({batch['slot']} {batch['mode']}{timing})"


def context(conn: sqlite3.Connection, lead, org, now: datetime) -> dict:
    """Values a template may use. Anything unknown is left empty so templates never state a guess."""
    from . import demos  # local import: demos imports leads, which is fine, but keep module load order simple
    ctx = {"first_name": first_name(lead), "org_name": org["name"], "exam": exam_label(lead),
           "target_score": lead["target_score"], "demo_time": "", "next_batch": "", "next_batch_line": ""}
    demo = demos.current_demo(conn, lead["id"])
    if demo:
        ctx["demo_time"] = _when(demo["scheduled_at"], org["timezone"])
    batch = demos.next_batch(conn, lead, now.astimezone(ZoneInfo(org["timezone"])).date().isoformat())
    if batch:
        ctx["next_batch"] = batch_text(batch)
        ctx["next_batch_line"] = f"Our next {batch['exam']} batch starts {ctx['next_batch']}."
    return ctx


def fill(template: str, ctx: dict) -> str:
    text = template.format_map(_Blank(ctx))
    return " ".join(text.split())  # tidy spaces left by empty placeholders


def unknown_placeholders(template: str) -> list[str]:
    import string
    return [f for _, f, _, _ in string.Formatter().parse(template) if f and f not in PLACEHOLDERS]
