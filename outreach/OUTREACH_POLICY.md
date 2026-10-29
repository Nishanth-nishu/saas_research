# Outreach Policy

Applies to every message prepared in this project. Drafts are produced by `src/generate_outreach.py`
and by hand; **nothing is sent automatically**.

## 1. Approval gate
1. Every draft starts as `approval_status = pending_review`, `sent_status = not_sent` in `OUTREACH_QUEUE.csv`.
2. You read the evidence URL, edit the draft, and change `approval_status` to `approved`.
3. You choose the channel and send it yourself (or explicitly approve one specific send per message).
4. Only after a message is actually sent is `outreach_status` in `data/prospects.csv` changed to `contacted`, with the date in `next_action`.
5. No subagent or scheduled task may send anything. The one exception is `src/outreach_bot.py send --send`, run by you:
   it emails only rows you approved, at most 20 a day (hard cap 30), 2–4 minutes apart, never to opted-out
   addresses. LinkedIn, WhatsApp and contact forms stay manual.

## 2. What messages must never claim
- That you used their product, spoke to their customers, or know their internal workflow.
- That they have a problem — only that a public signal *suggests* a question worth asking.
- Client results, case studies or numbers you have not achieved.
- Endorsement by, or partnership with, IIIT Hyderabad. State your affiliation accurately (e.g. "IIIT Hyderabad alumnus/student/researcher") and only where relevant. Do not use the IIITH logo.

## 3. Volume and cadence
- Hand-send only. Start at **≤10 new messages per working day**, personalised.
- One initial message + **at most one** follow-up 5–7 days later. Then stop.
- If anyone replies "not interested" / "stop", set `outreach_status = do_not_contact` immediately.
- Never evade platform limits (LinkedIn weekly invites, email provider limits), never use automation tools on LinkedIn.

## 4. Channel rules
| Channel | Allowed use | Notes |
|---|---|---|
| Published business email (info@, sales@, founder email shown on official site) | Yes, 1:1 | Include who you are, why you wrote, and an easy opt-out line |
| Official contact form | Yes, 1:1, manual | Keep it short; do not paste marketing blocks |
| LinkedIn connection note / InMail | Yes, from your own account, manual | ≤300 chars note; respect LinkedIn User Agreement (no scraping/automation) |
| WhatsApp business number | Only if the business advertises WhatsApp for business enquiries; one message, manual | Never add people to groups or broadcasts |
| Phone | Only published business numbers, business hours IST/local | Introduce yourself; ask permission to continue |
| Guessed emails (pattern-based) | **Not allowed** | Unverified addresses are never used |

## 5. Legal and privacy notes (not legal advice)
- **India – DPDP Act 2023 & Rules**: you collect only business contact data from public sources for a B2B purpose; keep it minimal, honour deletion/opt-out requests, and do not share the dataset.
- **India – TRAI TCCCPR (2018)**: unsolicited commercial voice calls/SMS to numbers on DND are restricted; prefer email/LinkedIn; do not bulk-call or SMS.
- **EU/UK – GDPR / PECR**: B2B email to corporate addresses can rely on legitimate interest (UK PECR allows corporate-subscriber email with opt-out); include identity and an opt-out; keep a record of the source of each address.
- **US – CAN-SPAM**: truthful subject line, physical postal address, working opt-out honoured within 10 business days.
- **Australia – Spam Act 2003**: requires consent (inferred consent may apply to conspicuously published business addresses relevant to the message), identification, and unsubscribe.
- Store the prospect database locally; never commit it to a public repository.

## 6. Record keeping
For each sent message record: date (UTC and IST), channel, exact text, evidence URL used, and outcome. Keep replies' content out of Git if it contains personal data.
