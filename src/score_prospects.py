"""Transparent 100-point qualification score. See research/PROSPECT_SCORING.md.

fit 25 + workflow evidence 25 + financial value 20 + reachability 15 + recency/quality 15.
Every point awarded is explained in `score_explanation`; missing evidence scores zero.
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd

from common import blank

WORKFLOW_POINTS = {"none": 0, "weak": 5, "moderate": 14, "strong": 22}


def _days_old(value: str, ref: date) -> int | None:
    v = str(value or "").strip()
    if not v:
        return None
    try:
        d = date.fromisoformat(v if len(v) == 10 else v + "-01")
    except ValueError:
        return None
    return (ref - d).days


_UNOPENED = re.compile(r"not opened|snippet[- ]only|page exists|careers page exists", re.IGNORECASE)


def has_real_signal(r: pd.Series) -> bool:
    """A buying signal counts only if its source was actually opened (not a snippet or an unopened page)."""
    sig = str(r.get("buying_signals") or "")
    return bool(sig.strip()) and not _UNOPENED.search(sig) and not blank(r.get("buying_signal_url"))


def _count_items(value: str) -> int:
    return len([x for x in str(value or "").replace("|", ";").split(";") if x.strip()])


def score_row(r: pd.Series, ref: date | None = None) -> dict:
    ref = ref or date.today()
    why: list[str] = []

    # 1. Customer-profile fit (25)
    fit = 0
    if r.get("verification_status") == "verified":
        fit += 10; why.append("fit+10 verified official site")
    else:
        why.append("fit+0 existence not verified")
    if not blank(r.get("fit_evidence")) and not blank(r.get("fit_evidence_url")):
        fit += 8; why.append("fit+8 profile evidence with URL")
    if not blank(r.get("niche")):
        fit += 3; why.append("fit+3 niche identified")
    if not blank(r.get("company_size")) and not blank(r.get("company_size_source")):
        fit += 4; why.append("fit+4 size sourced")
    if r.get("verification_status") != "verified":
        fit = min(fit, 8)

    # 2. Evidence of relevant workflow (25)
    strength = r.get("workflow_evidence_strength") or "none"
    wf = WORKFLOW_POINTS.get(strength, 0)
    if wf and not blank(r.get("workflow_evidence_url")):
        wf += 3
    why.append(f"workflow+{min(wf, 25)} evidence '{strength}'")
    wf = min(wf, 25)

    # 3. Likely financial value (20)
    n_val = min(_count_items(r.get("value_signals")), 3)
    val = 4 * n_val
    if n_val:
        why.append(f"value+{4 * n_val} {n_val} value signal(s)")
    if not blank(r.get("software_signals")):
        val += 4; why.append("value+4 already pays for/uses software")
    if has_real_signal(r):
        val += 4; why.append("value+4 buying signal (source opened)")
    elif not blank(r.get("buying_signals")):
        why.append("value+0 buying signal snippet-only/unopened")
    val = min(val, 20)

    # 4. Reachability (15)
    reach = 0
    if not blank(r.get("decision_maker_name")) and not blank(r.get("decision_maker_source_url")):
        reach += 6; why.append("reach+6 named decision-maker with source")
    if not blank(r.get("public_email")) and not blank(r.get("public_email_source")):
        reach += 4; why.append("reach+4 published business email")
    if not blank(r.get("public_phone")) and not blank(r.get("public_phone_source")):
        reach += 2; why.append("reach+2 published phone")
    if not blank(r.get("contact_page_url")):
        reach += 2; why.append("reach+2 contact page")
    if not blank(r.get("linkedin_url")):
        reach += 1; why.append("reach+1 public profile URL")
    reach = min(reach, 15)

    # 5. Recency and quality of evidence (15)
    rec = 0
    age = _days_old(r.get("evidence_date"), ref)
    # An evidence_date equal to the access date means the page was live but its publication date is unknown
    access_only = age is not None and str(r.get("evidence_date")).strip() == str(r.get("last_verified")).strip()
    if access_only:
        age = None
        rec += 3; why.append("recency+3 page live on access, publication date unknown")
    elif age is not None:
        pts = 8 if age <= 90 else 5 if age <= 365 else 2
        rec += pts; why.append(f"recency+{pts} evidence {age}d old")
    else:
        why.append("recency+0 evidence undated")
    if not blank(r.get("fit_evidence_url")) and not blank(r.get("workflow_evidence_url")):
        rec += 4; why.append("recency+4 primary URLs for fit and workflow")
    sig_age = _days_old(r.get("buying_signal_date"), ref)
    if sig_age is not None and sig_age <= 180 and has_real_signal(r):
        rec += 3; why.append("recency+3 buying signal <180d")
    rec = min(rec, 15)

    total = fit + wf + val + reach + rec
    qualified = r.get("verification_status") == "verified" and fit >= 18
    high_priority = qualified and strength in {"moderate", "strong"}
    # Tier A needs direct evidence of the workflow: a strong signal, or moderate plus a buying signal
    direct = strength == "strong" or (strength == "moderate" and has_real_signal(r))
    if total >= 70 and high_priority and direct:
        tier = "A"
    elif total >= 45 and qualified:
        tier = "B"
    else:
        tier = "C"
    confidence = "high" if strength == "strong" and age is not None and age <= 180 else \
        "medium" if strength in {"moderate", "strong"} else "low"
    return {
        "score_fit": fit, "score_workflow": wf, "score_value": val, "score_reach": reach,
        "score_recency": rec, "qualification_score": total, "tier": tier,
        "is_qualified": "yes" if qualified else "no",
        "is_high_priority": "yes" if high_priority else "no",
        "confidence": confidence, "score_explanation": "; ".join(why),
    }


def score(df: pd.DataFrame, ref: date | None = None) -> pd.DataFrame:
    df = df.copy()
    scored = df.apply(lambda r: pd.Series(score_row(r, ref)), axis=1)
    for col in scored.columns:
        df[col] = scored[col]
    return df.sort_values("qualification_score", ascending=False, kind="stable")


if __name__ == "__main__":
    from common import PROSPECTS_CSV, read_csv

    out = score(read_csv(PROSPECTS_CSV))
    out.to_csv(PROSPECTS_CSV, index=False)
    print(out.groupby(["segment", "tier"]).size().unstack(fill_value=0))
