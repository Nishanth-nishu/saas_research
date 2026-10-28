"""Settings from environment variables. Nothing secret is hard-coded or committed.

LEADPILOT_DB           path to the SQLite file (default saas/leadpilot.db)
LEADPILOT_SECRET       key for signing session cookies (generated into saas/.secret_key if unset)
LEADPILOT_TICK         seconds between follow-up engine runs (default 60; 0 disables the scheduler)
LEADPILOT_BASE_URL     public URL used in embed snippets (default: the URL the request came in on)
ANTHROPIC_API_KEY      enables AI drafting; without it, templates are used
LEADPILOT_AI_MODEL     Claude model for drafting (default claude-opus-5-5)
WA_ACCESS_TOKEN        WhatsApp Cloud API token; without it messages go to the dry-run outbox
WA_VERIFY_TOKEN        token Meta sends when verifying the webhook
WA_APP_SECRET          app secret for checking X-Hub-Signature-256 on webhook posts
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

SAAS_DIR = Path(__file__).resolve().parent.parent


def _secret_key() -> str:
    if os.environ.get("LEADPILOT_SECRET"):
        return os.environ["LEADPILOT_SECRET"]
    path = SAAS_DIR / ".secret_key"
    if not path.exists():
        path.write_text(secrets.token_hex(32), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


@dataclass
class Settings:
    db_path: str
    secret_key: str
    tick_seconds: int
    base_url: str
    ai_model: str
    anthropic_key: str
    wa_access_token: str
    wa_verify_token: str
    wa_app_secret: str


def load_settings(**overrides) -> Settings:
    s = Settings(
        db_path=os.environ.get("LEADPILOT_DB", str(SAAS_DIR / "leadpilot.db")),
        secret_key=_secret_key(),
        tick_seconds=int(os.environ.get("LEADPILOT_TICK", "60")),
        base_url=os.environ.get("LEADPILOT_BASE_URL", "").rstrip("/"),  # empty: taken from each request
        ai_model=os.environ.get("LEADPILOT_AI_MODEL", "claude-opus-5-5"),
        anthropic_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        wa_access_token=os.environ.get("WA_ACCESS_TOKEN", ""),
        wa_verify_token=os.environ.get("WA_VERIFY_TOKEN", ""),
        wa_app_secret=os.environ.get("WA_APP_SECRET", ""),
    )
    for k, v in overrides.items():
        setattr(s, k, v)
    return s
