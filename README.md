# Evidence-Driven B2B Market Research & Client Acquisition

Research workspace for finding a profitable, underserved B2B workflow, real businesses that may have it,
legitimate contact routes, and evidence-backed outreach drafts. Messages are sent only by you, and only after you approve each one (see below).

## Layout
```
research/   reports (start with FINAL_RECOMMENDATION.md), RESEARCH_RULES.md, parts/ (raw agent outputs)
data/       prospects.csv, contacts.csv, prospects.db (SQLite + change_log), parts/ (raw prospect CSVs)
outreach/   OUTREACH_DRAFTS.md, OUTREACH_QUEUE.csv, OUTREACH_POLICY.md, INTERVIEW_GUIDE.md
src/        pipeline scripts
tests/      pytest suite
```

## Pipeline
Requires Python 3.11+, pandas, pytest.
```bash
python src/import_prospects.py        # parts/*.csv -> dedupe -> IDs -> score -> prospects.csv, contacts.csv, prospects.db
python src/validate_data.py           # evidence-rule errors + research gaps -> data/validation_report.csv
python src/score_prospects.py         # re-score prospects.csv in place (after manual edits)
python src/generate_outreach.py       # drafts for Tier A/B -> outreach/ (pending_review, not_sent)
python src/outreach_bot.py draft --limit 10   # tailored email + demo sketch per prospect -> data/bot_queue.csv
python src/build_daily_queue.py 15    # today's prioritised research/outreach queue
python -m pytest -q
```
Set `SENDER_NAME` and `SENDER_AFFILIATION` environment variables before generating drafts.

## Adding research
Append rows to a CSV in `data/parts/` using the exact header in `research/RESEARCH_RULES.md`, then rerun
`import_prospects.py`. IDs are derived from the domain so they stay stable; human-edited
`research_status`, `outreach_status`, `next_action` are preserved, and every field change is logged in
the `change_log` table of `prospects.db`.

## Rules
See `research/RESEARCH_RULES.md` (evidence) and `outreach/OUTREACH_POLICY.md` (contact). No guessed emails,
no invented people, nothing sent without your approval.

## Outreach bot, website and profiles
- `src/outreach_bot.py`: reads each prospect's public homepage, picks the matching service, drafts a tailored
  email and a one-page demo sketch (`data/demos/`). You read, edit and `approve`; `send --send` uses free Gmail
  SMTP with a daily cap, pacing, opt-out line and suppression list. Run it with no arguments for help.
- `site/`: the services website (free on GitHub Pages; see `site/README.md`).
- `brand/PROFILE_COPY.md`: LinkedIn, company page, X and GitHub profile text for you to paste.
