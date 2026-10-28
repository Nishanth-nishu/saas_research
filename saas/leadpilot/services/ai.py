"""AI-drafted follow-up messages with Claude. Falls back to the rule template when no API key is set
or the call fails, so the product works without AI and a human always reviews before sending."""
from __future__ import annotations

import logging
import sqlite3

from ..config import Settings
from .templates import fill, first_name, topic

log = logging.getLogger("leadpilot.ai")

SYSTEM_PROMPT = """You write short WhatsApp follow-up messages for counsellors at an Indian study-abroad \
consultancy or test-prep institute. A counsellor reviews every message before it is sent.

Rules:
- Under 60 words, warm and plain, one clear question or next step. No emojis unless the student used them.
- Use only facts given about the student and the conversation. Never invent course details, fees, deadlines, \
scholarships, university names or visa outcomes, and never promise admission or a visa.
- If the student wrote in Hindi, Telugu, Malayalam, Tamil or another language, reply in that language.
- Sign off with the organisation name only. Output the message text and nothing else."""

PURPOSES = {
    "first_reply": "first reply to a new inquiry, offering a call with a counsellor",
    "follow_up": "polite follow-up because the student has gone quiet",
    "reply": "reply to the student's latest message",
    "book_session": "invite the student to book a free counselling session",
}


def _context(lead: sqlite3.Row, org_name: str, history: list[sqlite3.Row], purpose: str) -> str:
    lines = [f"Organisation: {org_name}", f"Student first name: {first_name(lead)}",
             f"Interest: {topic(lead)}", f"Intake: {lead['intake'] or 'unknown'}",
             f"Stage: {lead['stage']}", f"Original inquiry text: {lead['message'] or '(none)'}",
             f"Purpose of this message: {PURPOSES.get(purpose, purpose)}", "", "Recent messages (oldest first):"]
    sent = [m for m in history if m["status"] in ("sent", "received")][:8]
    for m in reversed(sent):
        who = "Student" if m["direction"] == "in" else "Us"
        lines.append(f"{who}: {m['body'][:500]}")
    if not sent:
        lines.append("(no messages exchanged yet)")
    return "\n".join(lines)


FALLBACK_TEMPLATES = {
    "first_reply": "Hi {first_name}, thanks for your inquiry with {org_name}{about}. When is a good time for a quick call with one of our counsellors?",
    "follow_up": "Hi {first_name}, following up from {org_name}. Did you get a chance to think about {topic}? Happy to answer any questions.",
    "reply": "Hi {first_name}, thanks for your message. A counsellor from {org_name} will get back to you shortly.",
    "book_session": "Hi {first_name}, would you like to book a free counselling session with {org_name} this week?",
}


def draft(settings: Settings, lead: sqlite3.Row, org_name: str, history: list[sqlite3.Row],
          purpose: str = "follow_up", client=None) -> tuple[str, str]:
    """Return (text, drafted_by) where drafted_by is the model id or 'template'."""
    fallback = fill(FALLBACK_TEMPLATES.get(purpose, FALLBACK_TEMPLATES["follow_up"]), lead, org_name)
    if not settings.anthropic_key and client is None:
        return fallback, "template"
    try:
        import anthropic
        client = client or anthropic.Anthropic(api_key=settings.anthropic_key, timeout=30.0)
        response = client.beta.messages.create(
            model=settings.ai_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": _context(lead, org_name, history, purpose)}],
        )
        if response.stop_reason == "refusal":
            log.warning("AI draft refused for lead %s", lead["id"])
            return fallback, "template"
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        return (text, settings.ai_model) if text else (fallback, "template")
    except Exception as e:  # any API/network failure degrades to the template, never blocks the counsellor
        log.warning("AI draft failed: %s", e)
        return fallback, "template"
