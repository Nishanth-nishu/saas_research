from common import make_prospect_id, normalize_domain, normalize_name
from deduplicate import deduplicate


def test_normalize_domain_strips_scheme_www_path_and_case():
    assert normalize_domain("https://WWW.Foo.co.in/about?x=1") == "foo.co.in"
    assert normalize_domain("foo.com") == "foo.com"
    assert normalize_domain("") == ""
    assert normalize_domain(None) == ""


def test_normalize_name_drops_legal_suffixes_and_punctuation():
    assert normalize_name("Acme Freight Pvt. Ltd.") == "acme freight"
    assert normalize_name("A&B Logistics LLP") == "a and b logistics"


def test_same_domain_rows_merge_and_keep_both_evidence(make_row, frame):
    a = make_row(workflow_evidence="Job post: data entry", workflow_evidence_strength="strong",
                 workflow_evidence_url="https://jobs.example/1")
    b = make_row(website="http://acmefreight.in", workflow_evidence="Many shipments",
                 workflow_evidence_strength="moderate", public_email="info@acmefreight.in")
    out, log = deduplicate(frame(a, b))
    assert len(out) == 1 and len(log) == 1
    r = out.iloc[0]
    assert r["workflow_evidence_strength"] == "strong"
    assert "Job post: data entry" in r["workflow_evidence"] and "Many shipments" in r["workflow_evidence"]
    assert r["public_email"] == "info@acmefreight.in"


def test_same_name_and_country_without_domain_merge(make_row, frame):
    a = make_row(website="")
    b = make_row(company_name="ACME Freight Private Limited", website="")
    out, _ = deduplicate(frame(a, b))
    assert len(out) == 1


def test_different_companies_are_not_merged(make_row, frame):
    a = make_row()
    b = make_row(company_name="Beta Cargo", website="https://betacargo.com")
    out, log = deduplicate(frame(a, b))
    assert len(out) == 2 and log == []


def test_prospect_id_is_stable():
    assert make_prospect_id("foo.com", "x") == make_prospect_id("foo.com", "y")
    assert make_prospect_id("", "Foo Ltd") == make_prospect_id("", "foo")
