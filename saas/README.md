# LeadPilot

Enquiry-to-enrolment autopilot for **IELTS and PTE coaching centres** (built first for the Ameerpet,
Hyderabad cluster). It follows how these centres actually sell:

**enquiry → call within 15 min → free demo class → reminders so the student shows up → follow-up
after the demo with the next matching batch → enrolled.**

Every enquiry from the website form, WhatsApp, CSV or API gets an owner (round robin) and a follow-up
plan; messages are drafted for counsellors to review and send.

Stack: FastAPI + Jinja templates + SQLite, standard-library auth, Anthropic SDK for optional AI drafting.

## Run it
```bash
python saas/run.py
```
Open http://127.0.0.1:8000, create an organisation, then share the form link from **Settings**.

## Tests
```bash
python -m pytest saas/tests -q
```

## Configuration (environment variables; never commit secrets)
| Variable | Effect |
|---|---|
| `LEADPILOT_DB` | SQLite path (default `saas/leadpilot.db`) |
| `LEADPILOT_SECRET` | Cookie-signing key (otherwise generated into `saas/.secret_key`, git-ignored) |
| `LEADPILOT_TICK` | Seconds between follow-up engine runs (default 60; 0 = off) |
| `LEADPILOT_BASE_URL` | Public URL for embed snippets (default: the request URL) |
| `ANTHROPIC_API_KEY` | Turns on AI drafts (otherwise templates) |
| `LEADPILOT_AI_MODEL` | Claude model for drafts (default `claude-opus-5-5`) |
| `WA_ACCESS_TOKEN`, `WA_VERIFY_TOKEN`, `WA_APP_SECRET` | WhatsApp Cloud API; without a token every send is a recorded dry run |

## Built for test prep
- **Student fields:** exam (IELTS, PTE, TOEFL, Duolingo, Spoken English), target score, planned exam month,
  preferred timing (morning/afternoon/evening/weekend), classroom or online. "Exam soon" flag when the exam month
  is within 60 days.
- **Free demo classes:** book from the lead page; reminders are drafted the day before and 2 hours before; an
  attendance task an hour after; "didn't come" sends the lead back with a reschedule call task.
- **Batches:** add upcoming batches in Settings. Follow-ups name the next batch that matches the student's exam,
  timing and mode, and say nothing about batches when none is set up.
- **Dashboard:** demo funnel (booked → attended → enrolled, show-up and close rates), demos in the next 48 hours,
  and conversion by exam.

## How it behaves
- **Nothing is sent without a person pressing Send**, unless an admin turns on auto-send for rule drafts.
- **Dry runs never count as contact.** Without WhatsApp credentials a send is recorded as "dry run, not delivered"
  and the lead stays uncontacted.
- **WhatsApp 24-hour rule enforced:** free text only within 24 h of the student's last message.
- **Follow-up engine** (`leadpilot/services/followups.py`): rules fire once per lead per contact; a new contact
  re-arms them; only the latest overdue rule fires, so students never get three messages at once; demo reminders
  count back from the class time and are skipped if the booking came too late or the class has started; leads
  without consent get call tasks, not message drafts; a student's reply suppresses chasers and creates a reply
  task; "STOP" opts the student out.
- **Database:** schema version is checked at start-up. There are no migrations yet, so an old dev database must be
  deleted (the app says so instead of failing strangely).

## Layout
```
saas/
  run.py                    start the server
  leadpilot/
    web.py                  routes: UI, public form, /api/v1/leads, /webhooks/whatsapp
    db.py                   schema
    security.py             password hashing, signed cookies, CSRF, Meta signature check
    services/               orgs, leads, demos (demo classes + batches), followups, messaging, ai, metrics, templates
    templates/, static/     server-rendered UI
  tests/                    57 tests
  KNOWN_ISSUES.md           what is broken or missing, in priority order
```
