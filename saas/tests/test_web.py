import hashlib
import hmac
import json

from conftest import csrf_of


def signup(client, email="owner@sky.test", org="Sky Overseas"):
    r = client.post("/signup", data={"org_name": org, "name": "Owner", "email": email, "password": "password123"})
    assert r.status_code == 200 and "Last 30 days" in r.text
    return r


def test_signup_login_logout(client):
    signup(client)
    client.post("/logout")
    assert "Log in to LeadPilot" in client.get("/dashboard").text
    assert client.post("/login", data={"email": "owner@sky.test", "password": "wrong"}).status_code == 401
    assert "Last 30 days" in client.post("/login", data={"email": "owner@sky.test", "password": "password123"}).text


def test_pages_render(client):
    signup(client)
    for path in ["/dashboard", "/leads", "/tasks", "/tasks?everyone=1", "/outbox", "/settings"]:
        assert client.get(path).status_code == 200, path


def test_csrf_required(client):
    signup(client)
    r = client.post("/leads", data={"phone": "9876543210"})
    assert r.status_code == 403


def test_manual_lead_and_actions(client):
    signup(client)
    token = csrf_of(client.get("/leads").text)
    r = client.post("/leads", data={"csrf": token, "name": "Priya", "phone": "9876543210", "consent": "1"})
    assert "Lead added" in r.text
    lead_url = str(r.url).split("?")[0]
    assert "Draft ready" in client.post(lead_url + "/draft", data={"csrf": token, "purpose": "first_reply"}).text
    page = client.post(lead_url + "/contact", data={"csrf": token, "kind": "call", "body": "Spoke to her"}).text
    assert "contacted" in page
    assert "Give a reason" in client.post(lead_url + "/stage", data={"csrf": token, "stage": "lost"}).text


def test_public_form_and_honeypot(client):
    signup(client)
    slug = "sky-overseas"
    assert client.get(f"/f/{slug}").status_code == 200
    no_consent = client.post(f"/f/{slug}", data={"name": "A", "phone": "9876543210"})
    assert no_consent.status_code == 400
    ok = client.post(f"/f/{slug}", data={"name": "A", "phone": "9876543210", "consent": "1"})
    assert "Thank you" in ok.text
    client.post(f"/f/{slug}", data={"name": "Bot", "phone": "9876500000", "consent": "1", "website": "spam.example"})
    assert client.get("/leads").text.count("/leads/") - client.get("/leads").text.count('href="/leads"') >= 1
    assert "Bot" not in client.get("/leads").text


def test_api_key_and_validation(client):
    signup(client)
    key = client.get("/settings").text.split("lp_", 1)[1].split("<", 1)[0]
    key = "lp_" + key.strip()
    assert client.post("/api/v1/leads", json={"phone": "9876543210"}).status_code == 401
    assert client.post("/api/v1/leads", json={"name": "x"}, headers={"X-API-Key": key}).status_code == 422
    r = client.post("/api/v1/leads", json={"phone": "9876543210"}, headers={"X-API-Key": key})
    assert r.status_code == 201 and r.json()["created"] is True
    assert client.post("/api/v1/leads", json={"phone": "98765 43210"}, headers={"X-API-Key": key}).status_code == 200


def test_cross_tenant_lead_is_404(client):
    signup(client)
    token = csrf_of(client.get("/leads").text)
    lead_url = str(client.post("/leads", data={"csrf": token, "phone": "9876543210"}).url).split("?")[0]
    client.post("/logout")
    signup(client, email="other@else.test", org="Else")
    assert client.get(lead_url).status_code == 404


def test_whatsapp_webhook_verify_and_signature(client, settings):
    assert client.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "verify-me",
                                                    "hub.challenge": "42"}).text == "42"
    assert client.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "nope"}).status_code == 403


def test_whatsapp_webhook_signed(tmp_path):
    from fastapi.testclient import TestClient

    from leadpilot.config import load_settings
    from leadpilot.db import connect
    from leadpilot.services import orgs
    from leadpilot.web import create_app

    s = load_settings(db_path=str(tmp_path / "w.db"), secret_key="k", tick_seconds=0, wa_app_secret="appsecret")
    with TestClient(create_app(s)) as c:
        conn = connect(s.db_path)
        org_id, _ = orgs.create_org(conn, "Sky", "A", "a@sky.test", "password123")
        orgs.update_org(conn, org_id, wa_phone_number_id="PNID")
        body = json.dumps({"entry": [{"changes": [{"value": {"metadata": {"phone_number_id": "PNID"},
                           "messages": [{"from": "919876543210", "id": "w1", "type": "text", "text": {"body": "hi"}}]}}]}]}).encode()
        assert c.post("/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": "sha256=bad"}).status_code == 401
        sig = "sha256=" + hmac.new(b"appsecret", body, hashlib.sha256).hexdigest()
        assert c.post("/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": sig}).status_code == 200
        assert conn.execute("SELECT COUNT(*) FROM leads WHERE org_id = ?", (org_id,)).fetchone()[0] == 1
        # Meta retries deliveries: the same message id must not be stored twice
        c.post("/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": sig})
        assert conn.execute("SELECT COUNT(*) FROM messages WHERE direction = 'in'").fetchone()[0] == 1


def test_counsellor_cannot_open_settings(client):
    signup(client)
    token = csrf_of(client.get("/settings").text)
    client.post("/settings/users", data={"csrf": token, "name": "Ravi", "email": "ravi@sky.test",
                                         "password": "password123", "role": "counsellor"})
    client.post("/logout")
    client.post("/login", data={"email": "ravi@sky.test", "password": "password123"})
    assert client.get("/settings").status_code == 403
