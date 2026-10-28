from datetime import timedelta

from conftest import T0

from leadpilot.config import load_settings
from leadpilot.services import followups, leads, messaging


def _new_lead(conn, org, consent=True, **extra):
    data = {"phone": "9876543210", "name": "priya sharma", "course_interest": "MS CS", "country_interest": "Germany",
            "consent": consent, **extra}
    return leads.capture(conn, org["id"], data, "web_form", T0)[0]


def test_first_response_task_after_15_minutes(conn, org):
    lead_id = _new_lead(conn, org)
    assert followups.run(conn, T0 + timedelta(minutes=10))["tasks"] == 0
    assert followups.run(conn, T0 + timedelta(minutes=16))["tasks"] == 1
    task = conn.execute("SELECT * FROM tasks WHERE lead_id = ?", (lead_id,)).fetchone()
    assert task["user_id"] == leads.get(conn, org["id"], lead_id)["owner_id"]


def test_engine_is_idempotent(conn, org):
    _new_lead(conn, org)
    now = T0 + timedelta(hours=2)
    first = followups.run(conn, now)
    again = followups.run(conn, now + timedelta(minutes=1))
    assert first["tasks"] == 1 and first["drafts"] == 1
    assert again == {"tasks": 0, "drafts": 0, "skipped_no_consent": 0}


def test_draft_uses_lead_fields(conn, org):
    lead_id = _new_lead(conn, org)
    followups.run(conn, T0 + timedelta(hours=2))
    body = conn.execute("SELECT body FROM messages WHERE lead_id = ? AND status = 'draft'", (lead_id,)).fetchone()[0]
    assert body.startswith("Hi Priya,") and "MS CS in Germany" in body and "Sky Overseas" in body


def test_no_consent_no_draft_but_task(conn, org):
    _new_lead(conn, org, consent=False)
    s = followups.run(conn, T0 + timedelta(hours=2))
    assert s["drafts"] == 0 and s["tasks"] == 1 and s["skipped_no_consent"] == 1


def test_contact_rearms_sequence_and_only_latest_fires(conn, org):
    lead_id = _new_lead(conn, org)
    t_call = T0 + timedelta(minutes=5)
    leads.record_contact(conn, org["id"], lead_id, "call", "spoke", t_call)
    # 8 days of silence: day-1 and day-3 are both overdue, only day-3 draft should exist
    followups.run(conn, t_call + timedelta(days=8))
    keys = [r[0].split("@")[0] for r in conn.execute("SELECT rule_key FROM messages WHERE lead_id = ?", (lead_id,))]
    assert keys == ["contacted_d3"]
    tasks = [r[0].split("@")[0] for r in conn.execute("SELECT rule_key FROM tasks WHERE lead_id = ?", (lead_id,))]
    assert tasks == ["contacted_d7"]


def test_opted_out_and_closed_leads_are_ignored(conn, org):
    a = _new_lead(conn, org)
    b = leads.capture(conn, org["id"], {"phone": "9876500000", "consent": True}, "web_form", T0)[0]
    leads.opt_out(conn, org["id"], a, T0)
    leads.set_stage(conn, org["id"], b, "enrolled", T0)
    assert followups.run(conn, T0 + timedelta(days=3)) == {"tasks": 0, "drafts": 0, "skipped_no_consent": 0}


def test_inbound_reply_suppresses_chaser(conn, org):
    lead_id = _new_lead(conn, org)
    leads.record_contact(conn, org["id"], lead_id, "call", "spoke", T0)
    messaging.record_inbound(conn, org["id"], "919876543210", "", "Can you send fees?", T0 + timedelta(hours=1))
    followups.run(conn, T0 + timedelta(days=2))
    assert conn.execute("SELECT COUNT(*) FROM messages WHERE lead_id = ? AND status = 'draft'", (lead_id,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM tasks WHERE lead_id = ? AND title = 'Reply to WhatsApp message'",
                        (lead_id,)).fetchone()[0] == 1


def test_simulated_send_does_not_count_as_contact(conn, org, settings):
    lead_id = _new_lead(conn, org)
    followups.run(conn, T0 + timedelta(hours=2))
    msg_id = conn.execute("SELECT id FROM messages WHERE lead_id = ? AND status = 'draft'", (lead_id,)).fetchone()[0]
    assert messaging.send(conn, settings, org["id"], msg_id, T0 + timedelta(hours=2)) == "simulated"
    lead = leads.get(conn, org["id"], lead_id)
    assert lead["first_contacted_at"] == "" and lead["stage"] == "new"


def test_whatsapp_24h_window_blocks_freeform(conn, org, settings):
    live = load_settings(**{**settings.__dict__, "wa_access_token": "token"})
    conn.execute("UPDATE orgs SET wa_phone_number_id = 'PNID' WHERE id = ?", (org["id"],))
    lead_id = _new_lead(conn, org)
    msg_id = messaging.create_draft(conn, org["id"], lead_id, "whatsapp", "hello", T0)
    assert messaging.send(conn, live, org["id"], msg_id, T0) == "failed"
    assert "24-hour" in conn.execute("SELECT error FROM messages WHERE id = ?", (msg_id,)).fetchone()[0]


def test_whatsapp_send_within_window(conn, org, settings):
    import httpx

    def handler(request):
        assert request.headers["authorization"] == "Bearer token"
        return httpx.Response(200, json={"messages": [{"id": "wamid.1"}]})

    live = load_settings(**{**settings.__dict__, "wa_access_token": "token"})
    conn.execute("UPDATE orgs SET wa_phone_number_id = 'PNID' WHERE id = ?", (org["id"],))
    lead_id = messaging.record_inbound(conn, org["id"], "919876543210", "Priya", "hi", T0)
    msg_id = messaging.create_draft(conn, org["id"], lead_id, "whatsapp", "Hi Priya!", T0)
    http = httpx.Client(transport=httpx.MockTransport(handler))
    assert messaging.send(conn, live, org["id"], msg_id, T0 + timedelta(hours=1), http=http) == "sent"
    assert leads.get(conn, org["id"], lead_id)["stage"] == "contacted"


def test_stop_reply_opts_out(conn, org):
    lead_id = messaging.record_inbound(conn, org["id"], "919876543210", "", "STOP", T0)
    assert leads.get(conn, org["id"], lead_id)["opted_out"] == 1


def test_parse_whatsapp_webhook():
    payload = {"entry": [{"changes": [{"value": {
        "metadata": {"phone_number_id": "PNID"},
        "contacts": [{"wa_id": "919876543210", "profile": {"name": "Priya"}}],
        "messages": [{"from": "919876543210", "id": "wamid.X", "type": "text", "text": {"body": "Hi"}}]}}]}]}
    assert messaging.parse_whatsapp_webhook(payload) == [
        {"phone_number_id": "PNID", "from": "919876543210", "name": "Priya", "text": "Hi", "id": "wamid.X"}]


def test_ai_falls_back_to_template_without_key(conn, org, settings):
    from leadpilot.services import ai
    lead_id = _new_lead(conn, org)
    text, by = ai.draft(settings, leads.get(conn, org["id"], lead_id), "Sky Overseas", [], "first_reply")
    assert by == "template" and text.startswith("Hi Priya")


def test_ai_uses_client_and_handles_refusal(conn, org, settings):
    from types import SimpleNamespace

    from leadpilot.services import ai

    class Fake:
        def __init__(self, stop):
            self.stop, self.kwargs = stop, None
            self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(stop_reason=self.stop, content=[SimpleNamespace(type="text", text="Hi Priya, AI here.")])

    lead = leads.get(conn, org["id"], _new_lead(conn, org))
    ok = Fake("end_turn")
    assert ai.draft(settings, lead, "Sky", [], client=ok) == ("Hi Priya, AI here.", settings.ai_model)
    assert ok.kwargs["model"] == "claude-opus-5-5" and ok.kwargs["fallbacks"] == "default"
    assert ai.draft(settings, lead, "Sky", [], client=Fake("refusal"))[1] == "template"
