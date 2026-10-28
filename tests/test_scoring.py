from datetime import date

import pandas as pd

from score_prospects import score_row

REF = date(2026, 10, 28)


def test_industry_only_prospect_scores_low_and_is_tier_c(make_row):
    r = score_row(pd.Series(make_row(workflow_evidence_strength="weak")), REF)
    assert r["score_workflow"] == 5
    assert r["tier"] == "C"
    assert r["is_high_priority"] == "no"


def test_unverified_business_cannot_qualify(make_row):
    r = score_row(pd.Series(make_row(verification_status="unverified", workflow_evidence_strength="strong",
                                     workflow_evidence_url="https://j/1")), REF)
    assert r["score_fit"] <= 8
    assert r["is_qualified"] == "no" and r["tier"] == "C"


def test_strong_recent_evidence_with_contact_reaches_tier_a(make_row):
    row = make_row(
        company_size="25", company_size_source="https://acmefreight.in/about",
        workflow_evidence="Hiring 3 data entry operators", workflow_evidence_strength="strong",
        workflow_evidence_url="https://jobs.example/1", evidence_date="2026-10-01",
        value_signals="4 offices; 500 shipments/month claimed; ISO certified",
        software_signals="Tally (job post)", buying_signals="Hiring data entry",
        buying_signal_url="https://jobs.example/1", buying_signal_date="2026-10-01",
        decision_maker_name="R. Kumar", decision_maker_role="Director",
        decision_maker_source_url="https://acmefreight.in/team",
        public_email="info@acmefreight.in", public_email_source="https://acmefreight.in/contact",
        contact_page_url="https://acmefreight.in/contact")
    r = score_row(pd.Series(row), REF)
    assert r["qualification_score"] >= 70
    assert r["tier"] == "A" and r["confidence"] == "high"
    assert r["qualification_score"] == sum(r[k] for k in
                                           ["score_fit", "score_workflow", "score_value", "score_reach", "score_recency"])


def test_components_never_exceed_caps(make_row):
    row = make_row(value_signals="a;b;c;d;e;f", software_signals="x", buying_signals="y",
                   decision_maker_name="A", decision_maker_source_url="https://x/t", public_email="a@b.com",
                   public_email_source="https://x/c", public_phone="1", public_phone_source="https://x/c",
                   contact_page_url="https://x/c", linkedin_url="https://linkedin.com/in/a",
                   workflow_evidence_strength="strong", workflow_evidence_url="https://x/j")
    r = score_row(pd.Series(row), REF)
    assert r["score_value"] <= 20 and r["score_reach"] <= 15 and r["score_workflow"] <= 25


def test_email_without_source_earns_no_reach_points(make_row):
    r = score_row(pd.Series(make_row(public_email="info@acmefreight.in")), REF)
    assert "published business email" not in r["score_explanation"]


def test_access_date_is_not_treated_as_publication_date(make_row):
    dated = score_row(pd.Series(make_row(evidence_date="2026-10-20", last_verified="2026-10-28")), REF)
    accessed = score_row(pd.Series(make_row(evidence_date="2026-10-28", last_verified="2026-10-28")), REF)
    assert dated["score_recency"] == 8 and accessed["score_recency"] == 3


def test_moderate_site_evidence_without_signal_is_not_tier_a(make_row):
    row = make_row(company_size="25", company_size_source="https://a/x", workflow_evidence_strength="moderate",
                   workflow_evidence_url="https://a/w", evidence_date="2026-10-01",
                   value_signals="a;b;c", software_signals="Tally", decision_maker_name="A",
                   decision_maker_source_url="https://a/t", public_email="a@a.com", public_email_source="https://a/c",
                   contact_page_url="https://a/c")
    r = score_row(pd.Series(row), REF)
    assert r["qualification_score"] >= 70 and r["tier"] == "B"


def test_snippet_only_signal_earns_nothing(make_row):
    base = dict(buying_signal_url="https://j/1", buying_signal_date="2026-10-01")
    real = score_row(pd.Series(make_row(buying_signals="Hiring data entry operator", **base)), REF)
    snip = score_row(pd.Series(make_row(buying_signals="Hiring (snippet-only)", **base)), REF)
    unopened = score_row(pd.Series(make_row(buying_signals="Careers page exists (not opened)", **base)), REF)
    assert real["score_value"] == 4 and snip["score_value"] == 0 and unopened["score_value"] == 0


def test_old_evidence_scores_less_recency(make_row):
    new = score_row(pd.Series(make_row(evidence_date="2026-10-01")), REF)
    old = score_row(pd.Series(make_row(evidence_date="2023-01-01")), REF)
    assert new["score_recency"] > old["score_recency"]
