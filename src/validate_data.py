"""Validate prospect rows: required fields, formats, and evidence rules.

Errors break the evidence rules (e.g. an email with no source). Warnings are research gaps.
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd

from common import CHANNEL_TYPES, SEGMENTS, STRENGTHS, blank

REQUIRED = ["company_name", "website", "country", "segment", "fit_evidence", "fit_evidence_url",
            "verification_status"]
URL_FIELDS = ["website", "fit_evidence_url", "workflow_evidence_url", "software_source_url",
              "decision_maker_source_url", "linkedin_url", "contact_page_url", "buying_signal_url"]
DATE_FIELDS = ["evidence_date", "buying_signal_date", "last_verified"]
URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)
DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def _urls(value: str) -> list[str]:
    return [u.strip() for u in re.split(r"[|;\s]+", value or "") if u.strip()]


def validate_row(row: pd.Series) -> list[tuple[str, str, str]]:
    """Return a list of (level, field, message)."""
    issues: list[tuple[str, str, str]] = []
    for f in REQUIRED:
        if blank(row.get(f)):
            issues.append(("error", f, "required field missing"))
    for f in URL_FIELDS:
        for u in _urls(row.get(f, "")):
            if not URL_RE.match(u):
                issues.append(("error", f, f"not a URL: {u[:60]}"))
    for f in DATE_FIELDS:
        v = str(row.get(f, "")).strip()
        if v and not DATE_RE.match(v):
            issues.append(("error", f, f"date not YYYY-MM-DD: {v}"))
        elif v and v > date.today().isoformat():
            issues.append(("error", f, f"date in the future: {v}"))
    seg = row.get("segment", "")
    if seg and seg not in SEGMENTS:
        issues.append(("error", "segment", f"unknown segment {seg}"))
    strength = row.get("workflow_evidence_strength", "")
    if strength and strength not in STRENGTHS:
        issues.append(("error", "workflow_evidence_strength", f"unknown value {strength}"))
    if strength in {"moderate", "strong"} and blank(row.get("workflow_evidence_url")):
        issues.append(("error", "workflow_evidence_url", f"'{strength}' evidence needs a source URL"))
    ch = row.get("contact_channel_type", "")
    if ch and ch not in CHANNEL_TYPES:
        issues.append(("error", "contact_channel_type", f"unknown value {ch}"))
    # Evidence rules for people and contacts
    email = str(row.get("public_email", "")).strip()
    if email:
        for e in re.split(r"[;,| ]+", email):
            if e and not EMAIL_RE.match(e):
                issues.append(("error", "public_email", f"malformed email {e}"))
        if blank(row.get("public_email_source")):
            issues.append(("error", "public_email_source", "email recorded without a source"))
    if not blank(row.get("public_phone")) and blank(row.get("public_phone_source")):
        issues.append(("error", "public_phone_source", "phone recorded without a source"))
    if not blank(row.get("decision_maker_name")):
        if blank(row.get("decision_maker_source_url")):
            issues.append(("error", "decision_maker_source_url", "decision-maker named without a source"))
        if blank(row.get("decision_maker_role")):
            issues.append(("warning", "decision_maker_role", "person named but role missing"))
    if row.get("outreach_status") == "contacted" and blank(row.get("next_action")):
        issues.append(("warning", "next_action", "contacted but no next action"))
    # Research gaps
    if blank(row.get("workflow_evidence")) or strength in {"", "none", "weak"}:
        issues.append(("warning", "workflow_evidence", "no direct workflow evidence yet"))
    if blank(row.get("decision_maker_name")):
        issues.append(("warning", "decision_maker_name", "decision-maker not identified"))
    if blank(row.get("public_email")) and blank(row.get("contact_page_url")):
        issues.append(("warning", "contact", "no verified contact channel"))
    if blank(row.get("evidence_date")):
        issues.append(("warning", "evidence_date", "evidence undated"))
    return issues


def validate(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        for level, field, msg in validate_row(r):
            rows.append({"prospect_id": r.get("prospect_id", ""), "company_name": r.get("company_name", ""),
                         "level": level, "field": field, "message": msg})
    return pd.DataFrame(rows, columns=["prospect_id", "company_name", "level", "field", "message"])


if __name__ == "__main__":
    from common import DATA, PROSPECTS_CSV, read_csv

    report = validate(read_csv(PROSPECTS_CSV))
    report.to_csv(DATA / "validation_report.csv", index=False)
    print(report["level"].value_counts().to_string() if len(report) else "no issues")
    print(report[report.level == "error"].to_string(index=False))
