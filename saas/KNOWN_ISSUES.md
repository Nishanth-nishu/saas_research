# LeadPilot — where it goes wrong (fix list)

Status on 2026-10-28: v0.1 built from scratch in one session. 38 automated tests pass, and the main
flow was clicked through in a browser (sign up → public form inquiry → lead → draft → send (dry run)
→ settings). **No real customer has used it, and no real WhatsApp message or Claude API call has been made.**

Work through this list top to bottom; each item says why it matters.

## Fixed during the build
| Problem found | Fix |
|---|---|
| Embed/form links on Settings pointed at port 8000 while the app ran on 8001 | Base URL now comes from the request unless `LEADPILOT_BASE_URL` is set |
| Refreshing the "Thank you" page re-submitted the inquiry (inflating `inquiry_count`) | Redirect after POST to `/f/<slug>/thanks` |
| Follow-up rules listed alphabetically (application before new) | Sorted by pipeline stage |
| Blank gap at the top of draft bubbles | CSS whitespace fix |
| "Draft" defaulted to *Follow-up* even for brand-new leads | Defaults to first reply / reply / follow-up by lead state |

## P0 — blocks a paying pilot
1. **WhatsApp templates are not supported.** Meta only allows free-text messages within 24 h of the
   student's last message. Day-1/3/7 follow-ups are almost always outside that window, so today they can
   only be sent by a counsellor from their own phone (then logged). Needs: template creation/approval
   flow, template sending, and a WhatsApp Business Platform account (Meta business verification + per-message
   charges, or a BSP like Interakt/Wati/Gupshup — decide which; that is a cost decision for you).
2. **Not deployed.** Runs on a laptop. The webhook and public form need a public HTTPS URL
   (e.g. a ₹500–1,000/month VPS or Render/Railway + domain). Needs your approval before paying.
3. **Real lead sources aren't connected.** Study-abroad firms get leads from Meta Lead Ads, Google Ads
   forms, JustDial, Shiksha/Leverage-style portals and Instagram DMs. Only the hosted form, CSV import,
   JSON API and WhatsApp inbound exist. Meta Lead Ads webhook is the first connector to build.
4. **No email/SMS provider.** Email "sends" are simulated. Add SMTP or a transactional provider.

## P1 — will bite in the first weeks of use
5. **No password reset, no email verification, open sign-up.** Anyone can create an org.
6. **No rate limiting** on the public form and API (honeypot only) → spam leads.
7. **Business hours ignored.** A 2 a.m. inquiry creates a "call within 15 minutes" task that is overdue by morning
   and skews the response-time KPI. Add per-org working hours and pause SLA clocks outside them.
8. **Single process only.** The follow-up engine runs inside the web process. Unique indexes stop duplicate
   tasks/drafts, but running 2+ workers could double auto-send. Move the engine to one scheduled job.
9. **No schema migrations or backups.** Changing `db.py` will not upgrade an existing database. Add a
   migration step and nightly SQLite backups (or move to Postgres when there are several customers).
10. **De-duplication is exact-match only** (normalised phone or lower-cased email). The same student using two
    numbers becomes two leads. Add a "merge leads" action.
11. **10-digit numbers are assumed Indian** (+91). Wrong for UAE/UK branches; make the default country per org.

## P2 — quality and compliance
12. **DPDP Act:** no per-student data export/delete, no retention period, consent text isn't versioned or stored
    with the lead. Needed before handling real student data at scale (core obligations from ~May 2027).
13. **Everyone in an org sees every lead.** Some owners will want counsellors limited to their own leads.
14. **AI drafting is untested against the live API** (no key in this environment). The prompt hasn't been
    evaluated on real conversations, and cost per draft is unmeasured. Default model is `claude-opus-5-5`;
    set `LEADPILOT_AI_MODEL` if you want a cheaper one.
15. **Rule delays are entered in minutes** (e.g. 7200). Show hours/days.
16. **Mobile nav** scrolls sideways to reach Outbox/Settings; fine but clumsy on phones, where counsellors live.
17. **Dry-run mode shows low "contacted" numbers** by design (simulated sends are not contact). Counsellors must
    log calls; onboarding should say so.
18. Logout has no CSRF token (low risk: cookies are SameSite=Lax).

## Product risk (bigger than any bug)
The research recommended **interviews before building**. This build skips that, so the biggest open question
isn't technical: will 2–3 study-abroad/test-prep owners pay ₹25–50k for this, and is follow-up really their
pain? Show this build in those interviews and let their answers re-order this list.
