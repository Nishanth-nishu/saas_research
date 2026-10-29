from datetime import timedelta

import pytest
from conftest import T0

from leadpilot.services import demos, followups, leads, orgs
from leadpilot.services.templates import context, fill, unknown_placeholders


def _lead(conn, org, **extra):
    data = {"phone": "9876543210", "name": "Priya", "exam": "IELTS", "preferred_slot": "evening",
            "mode": "offline", "consent": True, **extra}
    return leads.capture(conn, org["id"], data, "web_form", T0)[0]


def _drafts(conn, lead_id):
    return [r["rule_key"].split("@")[0] for r in
            conn.execute("SELECT rule_key FROM messages WHERE lead_id = ? AND status = 'draft'", (lead_id,))]


def test_book_demo_moves_stage_and_counts_as_contact(conn, org):
    lead_id = _lead(conn, org)
    demos.book(conn, org["id"], lead_id, T0 + timedelta(days=2), "offline", T0 + timedelta(minutes=5))
    lead = leads.get(conn, org["id"], lead_id)
    assert lead["stage"] == "demo_booked" and lead["first_contacted_at"]


def test_cannot_book_in_past_or_for_closed_lead(conn, org):
    lead_id = _lead(conn, org)
    with pytest.raises(ValueError):
        demos.book(conn, org["id"], lead_id, T0 - timedelta(hours=1), "offline", T0)
    leads.set_stage(conn, org["id"], lead_id, "lost", T0, lost_reason="Fees")
    with pytest.raises(ValueError):
        demos.book(conn, org["id"], lead_id, T0 + timedelta(days=1), "offline", T0)


def test_reminders_day_before_then_two_hours_before(conn, org):
    lead_id = _lead(conn, org)
    demo_at = T0 + timedelta(days=3)
    demos.book(conn, org["id"], lead_id, demo_at, "offline", T0)
    followups.run(conn, demo_at - timedelta(hours=30))
    assert _drafts(conn, lead_id) == []
    followups.run(conn, demo_at - timedelta(hours=23))
    assert _drafts(conn, lead_id) == ["demo_reminder_day"]
    followups.run(conn, demo_at - timedelta(hours=1))
    assert _drafts(conn, lead_id) == ["demo_reminder_2h"]  # day-before draft replaced, not stacked
    body = conn.execute("SELECT body FROM messages WHERE status = 'draft'").fetchone()[0]
    assert "IELTS demo class" in body and "Sky Overseas" in body


def test_short_notice_booking_skips_stale_reminder(conn, org):
    lead_id = _lead(conn, org)
    demo_at = T0 + timedelta(hours=5)  # booked 5h ahead: the day-before reminder was never due after booking
    demos.book(conn, org["id"], lead_id, demo_at, "offline", T0)
    followups.run(conn, T0 + timedelta(minutes=1))
    assert _drafts(conn, lead_id) == []
    followups.run(conn, demo_at - timedelta(minutes=90))
    assert _drafts(conn, lead_id) == ["demo_reminder_2h"]


def test_no_reminder_after_class_started_but_attendance_task(conn, org):
    lead_id = _lead(conn, org)
    demo_at = T0 + timedelta(days=1)
    demos.book(conn, org["id"], lead_id, demo_at, "offline", T0)
    followups.run(conn, demo_at + timedelta(hours=2))
    assert _drafts(conn, lead_id) == []
    titles = [r[0] for r in conn.execute("SELECT title FROM tasks WHERE lead_id = ? AND done_at = ''", (lead_id,))]
    assert "Mark whether the student attended the demo" in titles


def test_no_show_returns_to_contacted_with_reschedule_task(conn, org):
    lead_id = _lead(conn, org)
    demo_at = T0 + timedelta(days=1)
    demo_id = demos.book(conn, org["id"], lead_id, demo_at, "offline", T0)
    with pytest.raises(ValueError):
        demos.mark(conn, org["id"], demo_id, "no_show", T0)  # class hasn't happened yet
    demos.mark(conn, org["id"], demo_id, "no_show", demo_at + timedelta(hours=1))
    assert leads.get(conn, org["id"], lead_id)["stage"] == "contacted"
    assert conn.execute("SELECT COUNT(*) FROM tasks WHERE title = 'Call to reschedule missed demo'").fetchone()[0] == 1


def test_attended_then_post_demo_followup_mentions_batch(conn, org):
    demos.add_batch(conn, org["id"], "IELTS", "2026-11-03", "morning", "offline", "7-9 AM", 20, T0)
    demos.add_batch(conn, org["id"], "IELTS", "2026-11-10", "evening", "offline", "6-8 PM", 20, T0)
    lead_id = _lead(conn, org)
    demo_at = T0 + timedelta(days=1)
    demo_id = demos.book(conn, org["id"], lead_id, demo_at, "offline", T0)
    demos.mark(conn, org["id"], demo_id, "attended", demo_at + timedelta(hours=1))
    assert leads.get(conn, org["id"], lead_id)["stage"] == "demo_attended"
    followups.run(conn, demo_at + timedelta(days=1, hours=2))
    body = conn.execute("SELECT body FROM messages WHERE status = 'draft'").fetchone()[0]
    assert "Tue 10 Nov (evening offline, 6-8 PM)" in body  # preferred slot beats the earlier morning batch


def test_next_batch_ignores_past_inactive_and_other_exams(conn, org):
    demos.add_batch(conn, org["id"], "IELTS", "2026-10-01", "evening", "offline", "", 0, T0)
    b = demos.add_batch(conn, org["id"], "IELTS", "2026-11-20", "evening", "offline", "", 0, T0)
    demos.add_batch(conn, org["id"], "PTE", "2026-11-01", "evening", "offline", "", 0, T0)
    lead = leads.get(conn, org["id"], _lead(conn, org))
    assert demos.next_batch(conn, lead, "2026-10-28")["id"] == b
    demos.set_batch_active(conn, org["id"], b, False)
    assert demos.next_batch(conn, lead, "2026-10-28") is None


def test_add_batch_validates(conn, org):
    with pytest.raises(ValueError):
        demos.add_batch(conn, org["id"], "GRE", "2026-11-03", "morning", "offline", "", 0, T0)
    with pytest.raises(ValueError):
        demos.add_batch(conn, org["id"], "IELTS", "next monday", "morning", "offline", "", 0, T0)


def test_lost_cancels_booked_demo(conn, org):
    lead_id = _lead(conn, org)
    demos.book(conn, org["id"], lead_id, T0 + timedelta(days=1), "offline", T0)
    leads.set_stage(conn, org["id"], lead_id, "lost", T0 + timedelta(hours=1), lost_reason="Joined another centre")
    assert demos.current_demo(conn, lead_id) is None


def test_funnel(conn, org):
    a, b, _ = (_lead(conn, org, phone=f"98765000{i}") for i in range(3))
    for lid in (a, b):
        demos.book(conn, org["id"], lid, T0 + timedelta(days=1), "offline", T0)
    da = demos.current_demo(conn, a)["id"]
    db = demos.current_demo(conn, b)["id"]
    demos.mark(conn, org["id"], da, "attended", T0 + timedelta(days=1, hours=1))
    demos.mark(conn, org["id"], db, "no_show", T0 + timedelta(days=1, hours=1))
    leads.set_stage(conn, org["id"], a, "enrolled", T0 + timedelta(days=2))
    f = demos.funnel(conn, org["id"], "2026-01-01")
    assert (f["leads"], f["booked"], f["attended"], f["no_show"], f["enrolled_after_demo"]) == (3, 2, 1, 1, 1)
    assert f["show_rate"] == 50 and f["close_rate"] == 100


def test_templates_never_guess(conn, org):
    lead = leads.get(conn, org["id"], _lead(conn, org, exam="", name=""))
    ctx = context(conn, lead, orgs.get_org(conn, org["id"]), T0)
    text = fill("Hi {first_name}, {exam} prep. {next_batch_line} {unknown}", ctx)
    assert text == "Hi there, English test prep."
    assert unknown_placeholders("Hi {first_name} {fees}") == ["fees"]


def test_rule_with_unknown_placeholder_rejected(conn, org):
    rule = conn.execute("SELECT id FROM followup_rules WHERE key = 'contacted_d1'").fetchone()[0]
    with pytest.raises(ValueError):
        orgs.update_rule(conn, org["id"], rule, 1440, True, "Fees are {fees}")
