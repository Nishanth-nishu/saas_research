import pandas as pd

from validate_data import validate, validate_row


def _errors(row):
    return {f for level, f, _ in validate_row(pd.Series(row)) if level == "error"}


def test_clean_row_has_no_errors(make_row):
    assert _errors(make_row()) == set()


def test_missing_required_field_is_error(make_row):
    assert "fit_evidence_url" in _errors(make_row(fit_evidence_url=""))


def test_email_without_source_is_error(make_row):
    assert "public_email_source" in _errors(make_row(public_email="info@acmefreight.in"))


def test_guessed_malformed_email_is_error(make_row):
    assert "public_email" in _errors(make_row(public_email="firstname.lastname@", public_email_source="https://x/c"))


def test_decision_maker_without_source_is_error(make_row):
    assert "decision_maker_source_url" in _errors(make_row(decision_maker_name="A Person"))


def test_strong_evidence_requires_url(make_row):
    assert "workflow_evidence_url" in _errors(make_row(workflow_evidence_strength="strong"))


def test_bad_enums_dates_and_urls(make_row):
    errs = _errors(make_row(segment="Z", evidence_date="28/10/2026", website="acme dot com",
                            contact_channel_type="guess"))
    assert {"segment", "evidence_date", "website", "contact_channel_type"} <= errs


def test_future_date_is_error(make_row):
    assert "last_verified" in _errors(make_row(last_verified="2999-01-01"))


def test_report_lists_research_gaps_as_warnings(make_row):
    rep = validate(pd.DataFrame([make_row()]))
    warn_fields = set(rep[rep.level == "warning"]["field"])
    assert {"workflow_evidence", "decision_maker_name"} <= warn_fields
