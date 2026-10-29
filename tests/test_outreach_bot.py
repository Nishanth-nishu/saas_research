from datetime import timedelta

import pandas as pd
import pytest

import outreach_bot as bot

COACHING_HTML = """<html><head><title>Sky IELTS &amp; PTE Academy</title></head><body>
<form action="/enquire"></form><a href="https://wa.me/919000000000">WhatsApp</a><a href="tel:+91900">Call</a>
<p>Free demo class for IELTS and PTE</p></body></html>"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    prospects = tmp_path / "prospects.csv"
    rows = [
        dict(prospect_id="P-1", company_name="Sky Academy", website="https://sky.example", segment="A_education",
             niche="test prep", public_email="info@sky.example", public_email_source="https://sky.example/contact",
             contact_channel_type="verified_public_business_contact", outreach_status="not_contacted",
             qualification_score="70", decision_maker_name="", opening_angle="", next_action=""),
        dict(prospect_id="P-2", company_name="Cargo Co", website="https://cargo.example", segment="B_documents_logistics",
             niche="freight forwarder", public_email="ops@cargo.example", public_email_source="https://cargo.example",
             contact_channel_type="verified_public_business_contact", outreach_status="not_contacted",
             qualification_score="80", decision_maker_name="Ravi Kumar", opening_angle="Ask which documents take longest",
             next_action=""),
        dict(prospect_id="P-3", company_name="No Email Ltd", website="", segment="C_agency_b2b_services", niche="",
             public_email="", public_email_source="", contact_channel_type="official_contact_form",
             outreach_status="not_contacted", qualification_score="90", decision_maker_name="", opening_angle="",
             next_action=""),
    ]
    pd.DataFrame(rows).to_csv(prospects, index=False)
    monkeypatch.setattr(bot, "PROSPECTS_CSV", prospects)
    monkeypatch.setattr(bot, "QUEUE", tmp_path / "queue.csv")
    monkeypatch.setattr(bot, "SUPPRESSION", tmp_path / "suppression.csv")
    monkeypatch.setattr(bot, "DEMOS", tmp_path / "demos")
    monkeypatch.setattr(bot, "DATA", tmp_path)
    monkeypatch.setenv("SENDER_EMAIL", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "test-app-password")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    pages = {"https://sky.example": COACHING_HTML, "https://cargo.example": "<html><p>Customs clearing, invoices, Tally</p></html>"}
    return lambda url: pages.get(url, "")


class FakeSMTP:
    def __init__(self):
        self.sent = []

    def login(self, user, pw):
        pass

    def send_message(self, msg):
        self.sent.append(msg)

    def quit(self):
        pass


def test_signals_and_service_choice():
    s = bot.extract_signals(COACHING_HTML)
    assert {"WhatsApp", "web forms", "phone calls"} <= set(s["channels"])
    assert {"IELTS", "PTE", "demo class"} <= set(s["topics"])
    assert s["title"] == "Sky IELTS & PTE Academy"
    assert bot.choose_service({"segment": "C_agency_b2b_services"}, s) == "followup"
    assert bot.choose_service({"segment": "D_saas_ecommerce"}, {"topics": []}) == "support"


def test_draft_only_verified_emails_highest_score_first(env):
    made = bot.draft(10, fetch=env)
    assert [r["prospect_id"] for r in made] == ["P-2", "P-1"]  # P-3 has no published email
    assert all(r["status"] == "pending_review" for r in made)
    cargo, sky = made
    assert cargo["service"] == "extraction" and "Tally" in cargo["body"] and cargo["body"].startswith("Hi Ravi,")
    assert sky["service"] == "followup" and "WhatsApp" in sky["body"] and "free" in sky["body"]
    assert (bot.DEMOS / "P-1.html").exists()
    assert bot.draft(10, fetch=env) == []  # never drafts the same prospect twice


def test_email_makes_no_result_claims(env):
    for r in bot.draft(10, fetch=env):
        assert not any(w in r["body"].lower() for w in ("guarantee", "we helped", "clients like", "% more"))


def test_nothing_sends_without_approval(env):
    bot.draft(10, fetch=env)
    smtp = FakeSMTP()
    assert bot.send(True, smtp_factory=lambda: smtp, sleep=lambda s: None) == []
    assert smtp.sent == []


def test_send_approved_with_optout_and_records_contact(env):
    bot.draft(10, fetch=env)
    bot.set_status(["P-1"], "approved")
    assert bot.send(False) and bot.load_queue()[1]["status"] == "approved"  # dry run changes nothing
    smtp = FakeSMTP()
    sent = bot.send(True, smtp_factory=lambda: smtp, sleep=lambda s: None)
    assert len(sent) == 1 and len(smtp.sent) == 1
    msg = smtp.sent[0]
    assert msg["To"] == "info@sky.example" and "stop" in msg["List-Unsubscribe"]
    assert 'Reply "stop"' in msg.get_content()
    row = next(r for r in bot.load_queue() if r["prospect_id"] == "P-1")
    assert row["status"] == "sent" and row["sent_utc"].endswith("UTC") and row["sent_ist"].endswith("IST")
    df = pd.read_csv(bot.PROSPECTS_CSV, dtype=str, keep_default_na=False)
    assert df.set_index("prospect_id").loc["P-1", "outreach_status"] == "contacted"
    assert df.set_index("prospect_id").loc["P-2", "outreach_status"] == "not_contacted"


def test_daily_cap_and_suppression(env, monkeypatch):
    bot.draft(10, fetch=env)
    bot.set_status(["P-1", "P-2"], "approved")
    bot.add_suppression(["OPS@cargo.example"])
    monkeypatch.setattr(bot, "DAILY_CAP", 1)
    smtp = FakeSMTP()
    assert len(bot.send(True, smtp_factory=lambda: smtp, sleep=lambda s: None)) == 1
    assert smtp.sent[0]["To"] == "info@sky.example"  # suppressed address skipped
    assert bot.send(True, smtp_factory=lambda: smtp, sleep=lambda s: None) == []  # cap reached for today


def test_followup_once_after_silence_and_not_after_reply(env, monkeypatch):
    bot.draft(10, fetch=env)
    bot.set_status(["P-1", "P-2"], "approved")
    bot.send(True, smtp_factory=FakeSMTP, sleep=lambda s: None)
    assert bot.followups() == []  # too soon
    later = bot.now_utc() + timedelta(days=7)
    monkeypatch.setattr(bot, "now_utc", lambda: later)
    bot.set_status(["P-2"], "replied")
    made = bot.followups()
    assert [r["prospect_id"] for r in made] == ["P-1"] and made[0]["status"] == "pending_review"
    assert bot.followups() == []  # never a second follow-up


def test_not_interested_suppresses_and_cancels(env):
    bot.draft(10, fetch=env)
    bot.set_status(["P-1"], "approved")
    bot.set_status(["P-1"], "not_interested")
    assert "info@sky.example" in bot.suppressed()
    assert next(r for r in bot.load_queue() if r["prospect_id"] == "P-1")["status"] == "cancelled"
