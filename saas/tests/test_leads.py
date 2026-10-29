from datetime import timedelta

import pytest
from conftest import T0

from leadpilot.services import leads


@pytest.mark.parametrize("raw,expected", [
    ("98765 43210", "919876543210"),
    ("+91-98765-43210", "919876543210"),
    ("09876543210", "919876543210"),
    ("0044 7700 900123", "447700900123"),
    ("12345", ""),
    ("", ""),
])
def test_normalize_phone(raw, expected):
    assert leads.normalize_phone(raw) == expected


def test_capture_requires_phone_or_email(conn, org):
    with pytest.raises(ValueError):
        leads.capture(conn, org["id"], {"name": "No Contact"}, "manual", T0)


def test_round_robin_alternates_counsellors(conn, org):
    owners = [conn.execute("SELECT owner_id FROM leads WHERE id = ?",
                           (leads.capture(conn, org["id"], {"phone": f"98765000{i:02d}"}, "web_form", T0 + timedelta(seconds=i))[0],)).fetchone()[0]
              for i in range(4)]
    assert set(owners) == {org["c1"], org["c2"]}
    assert owners[0] != owners[1] and owners[0] == owners[2]


def test_duplicate_merges_and_counts(conn, org):
    a, created = leads.capture(conn, org["id"], {"phone": "9876543210", "name": "Priya"}, "web_form", T0)
    b, created2 = leads.capture(conn, org["id"], {"phone": "+91 98765 43210", "exam": "ielts general"}, "whatsapp", T0)
    assert created and not created2 and a == b
    lead = leads.get(conn, org["id"], a)
    assert lead["inquiry_count"] == 2 and lead["exam"] == "IELTS" and lead["name"] == "Priya"


def test_lost_lead_reopens_on_new_inquiry(conn, org):
    a, _ = leads.capture(conn, org["id"], {"email": "x@y.com"}, "web_form", T0)
    leads.set_stage(conn, org["id"], a, "lost", T0, lost_reason="No budget")
    leads.capture(conn, org["id"], {"email": "X@Y.com"}, "web_form", T0 + timedelta(days=30))
    assert leads.get(conn, org["id"], a)["stage"] == "new"


def test_lost_requires_reason(conn, org):
    a, _ = leads.capture(conn, org["id"], {"email": "x@y.com"}, "web_form", T0)
    with pytest.raises(ValueError):
        leads.set_stage(conn, org["id"], a, "lost", T0)


def test_note_is_not_contact_but_call_is(conn, org):
    a, _ = leads.capture(conn, org["id"], {"phone": "9876543210"}, "web_form", T0)
    leads.record_contact(conn, org["id"], a, "note", "rang, no answer", T0)
    assert leads.get(conn, org["id"], a)["first_contacted_at"] == ""
    leads.record_contact(conn, org["id"], a, "call", "spoke", T0 + timedelta(minutes=5))
    lead = leads.get(conn, org["id"], a)
    assert lead["stage"] == "contacted" and lead["first_contacted_at"]


def test_tenant_isolation(conn, org):
    from leadpilot.services import orgs
    other, _ = orgs.create_org(conn, "Other Org", "O", "o@other.test", "password123")
    a, _ = leads.capture(conn, org["id"], {"phone": "9876543210"}, "web_form", T0)
    assert leads.get(conn, other, a) is None
    # same phone in another org is a separate lead
    b, created = leads.capture(conn, other, {"phone": "9876543210"}, "web_form", T0)
    assert created and b != a


def test_csv_import(conn, org):
    text = "Name,Mobile,Exam,Exam date,Consent\nAnil,9876500001,PTE-A,2027-02,yes\nBad,123,PTE,,\nAnil again,98765 00001,,,\n"
    r = leads.import_csv(conn, org["id"], text, T0)
    assert r["created"] == 1 and r["merged"] == 1 and len(r["errors"]) == 1
    lead = conn.execute("SELECT * FROM leads").fetchone()
    assert lead["exam"] == "PTE" and lead["exam_date"] == "2027-02"


@pytest.mark.parametrize("raw,expected", [("2027-03", "2027-03"), ("2027-3", ""), ("March", ""), ("2027-03-15", "2027-03")])
def test_normalize_month(raw, expected):
    assert leads.normalize_month(raw) == expected


def test_exam_soon(conn, org):
    a, _ = leads.capture(conn, org["id"], {"phone": "9876543210", "exam_date": "2026-12"}, "web_form", T0)
    b, _ = leads.capture(conn, org["id"], {"phone": "9876543211", "exam_date": "2027-06"}, "web_form", T0)
    assert leads.exam_soon(leads.get(conn, org["id"], a), T0)
    assert not leads.exam_soon(leads.get(conn, org["id"], b), T0)
