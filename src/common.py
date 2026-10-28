"""Shared schema, paths and normalisation helpers for the prospect research pipeline."""
from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PARTS = DATA / "parts"
RESEARCH = ROOT / "research"
OUTREACH = ROOT / "outreach"
DB_PATH = DATA / "prospects.db"
PROSPECTS_CSV = DATA / "prospects.csv"
CONTACTS_CSV = DATA / "contacts.csv"

# Raw research fields, in the order defined in research/RESEARCH_RULES.md
RAW_COLUMNS = [
    "company_name", "website", "country", "city_region", "segment", "niche",
    "company_size", "company_size_source", "products_services", "fit_evidence",
    "fit_evidence_url", "workflow_hypothesis", "workflow_evidence", "workflow_evidence_url",
    "workflow_evidence_strength", "evidence_date", "value_signals", "software_signals",
    "software_source_url", "decision_maker_name", "decision_maker_role",
    "decision_maker_source_url", "linkedin_url", "contact_page_url", "public_email",
    "public_email_source", "public_phone", "public_phone_source", "contact_channel_type",
    "buying_signals", "buying_signal_url", "buying_signal_date", "verification_status",
    "research_gaps", "last_verified",
]

# Fields added by the pipeline (never typed by hand)
DERIVED_COLUMNS = [
    "prospect_id", "domain", "is_qualified", "is_high_priority",
    "score_fit", "score_workflow", "score_value", "score_reach", "score_recency",
    "qualification_score", "tier", "confidence", "score_explanation",
    "opening_angle", "research_status", "outreach_status", "next_action",
]

# Tracking fields a human edits; preserved across re-imports
TRACKING_COLUMNS = ["research_status", "outreach_status", "next_action"]

ALL_COLUMNS = ["prospect_id"] + RAW_COLUMNS + [c for c in DERIVED_COLUMNS if c != "prospect_id"]

SEGMENTS = {"A_education", "B_documents_logistics", "C_agency_b2b_services", "D_saas_ecommerce"}
STRENGTHS = ["none", "weak", "moderate", "strong"]
CHANNEL_TYPES = {
    "verified_public_business_contact", "public_professional_profile",
    "official_contact_form", "third_party_unverified", "unknown",
}
OUTREACH_STATUSES = {
    "not_contacted", "draft_ready", "approved", "contacted", "replied",
    "meeting_booked", "pilot_proposed", "won", "lost", "do_not_contact",
}

_LEGAL_SUFFIXES = re.compile(
    r"\b(private|pvt|limited|ltd|llp|llc|inc|incorporated|corp|corporation|co|company|"
    r"plc|gmbh|pty|the)\b\.?",
    re.IGNORECASE,
)


def today() -> str:
    return date.today().isoformat()


def normalize_domain(url: str | None) -> str:
    """Return the bare registrable-ish host: 'https://www.Foo.co.in/x' -> 'foo.co.in'."""
    if not url or not isinstance(url, str) or not url.strip():
        return ""
    url = url.strip()
    if "://" not in url:
        url = "http://" + url
    host = (urlparse(url).hostname or "").lower().strip(".")
    for prefix in ("www.", "www2.", "m."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    return host


def normalize_name(name: str | None) -> str:
    """Lower-case company name without legal suffixes or punctuation, for fuzzy matching."""
    if not name or not isinstance(name, str):
        return ""
    s = name.lower().replace("&", " and ")
    s = _LEGAL_SUFFIXES.sub(" ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def make_prospect_id(domain: str, name: str) -> str:
    """Stable ID derived from domain (or name if no domain) so re-imports keep the same ID."""
    key = domain or normalize_name(name)
    return "P-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:8].upper()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df


def blank(value) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == ""
