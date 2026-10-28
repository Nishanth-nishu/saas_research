# Environment Audit

Audit date: 2026-10-28, 10:53 UTC / 16:23 IST
Auditor: Claude Code (desktop app, Code tab), model Opus 5.5

## 1. Project directory

`C:\Users\HP\Desktop\MArketing_researchg` was **empty** at the start (no prior files, config or docs).
A git repository was initialised here during this session. Nothing has been committed or pushed.

## 2. Tools actually available (verified, not assumed)

| # | Capability | Tool | Verified how | Auth needed | Cost to you | Restrictions |
|---|---|---|---|---|---|---|
| 1 | Web search | `WebSearch` | Ran a live query on 2026-10-28; results returned | No | Included in Claude subscription | US-indexed results; returns titles/URLs + summary, not full pages; quality varies for India-local queries |
| 2 | Page fetch | `WebFetch` | Loaded | No | Included | Public pages only; fails on login walls (LinkedIn, most G2 review pages, Google Maps); a small model summarises the page, so exact quotes must be re-checked |
| 3 | Browser automation (built-in pane) | `mcp__Claude_Browser__*` | Tools present in session | No (you may be asked to allow sites) | Included | Isolated from your Chrome; no logged-in sessions. Must not bypass CAPTCHAs/anti-bot. Slow for bulk work |
| 4 | Browser automation (your Chrome) | `mcp__claude-in-chrome__*` | Deferred tools listed | Your Chrome profile | Included | Would act inside your logged-in accounts (e.g. LinkedIn). **Not used** without your explicit approval |
| 5 | Search engine API (SerpAPI, Google CSE, Bing) | — | No env vars/keys found | API key | Paid/limited free tiers | **Unavailable** |
| 6 | Google Maps / Places API | — | No key found | Google Cloud key + billing | Paid beyond free credit | **Unavailable**. Maps can be viewed manually in browser; automated scraping of Maps is against Google ToS |
| 7 | LinkedIn API / Sales Navigator | — | Not configured | LinkedIn account | Paid | **Unavailable**. Public LinkedIn pages are mostly login-walled to WebFetch; LinkedIn ToS prohibits scraping |
| 8 | Lead databases (Apollo, Hunter, etc.) | — | Not configured | Account + key | Free tiers exist | **Unavailable**; would require your approval to sign up |
| 9 | Gmail / Google Calendar / Google Drive MCP | `mcp__plugin_claude-for-nonprofits_gmail__*` etc. | Tools listed as available | Your Google account (already connected) | Included | **Will not be used to send anything.** Gmail can only create drafts; even drafts require your approval |
| 10 | HubSpot, Notion, Airtable, Monday, Salesforce, Similarweb, Ahrefs MCPs | — | Listed as "requires authentication" | OAuth via `/mcp` in an interactive `claude` terminal | Depends on your plans | **Not usable** until you authorise them. Not needed for phase 1 |
| 11 | Python | Python 3.11.9 | `python --version` | — | Free | — |
| 12 | Data libraries | pandas 3.0.5, sqlite3 3.45.1, pytest 9.1.1, requests, httpx, beautifulsoup4, lxml | `pip list` | — | Free | **openpyxl not installed** → Excel export not available without `pip install openpyxl` (CSV is used instead) |
| 13 | Git | git 2.55.0 | `git --version` | — | Free | No remote configured; nothing will be pushed |
| 14 | Subagents | `Agent` tool (general-purpose, Explore, Plan) | Listed in session | — | Uses your Claude usage allowance | Each agent only sees the brief it is given; results must be audited |
| 15 | Credentials in environment | — | Scanned env var names for API_KEY/TOKEN/etc. | — | — | **None relevant found** (only an internal app token) |

## 3. What each tool is used for in this project

- **WebSearch** → discovery: find competitor pricing pages, agency sites, Reddit/forum threads, job posts, directories, prospect websites.
- **WebFetch** → verification: open the official page and extract the specific fact (price, plan, service, contact page, team page). Facts are recorded only from fetched pages; search snippets alone are marked lower confidence.
- **Built-in browser** → fallback when WebFetch fails on JS-heavy pages (pricing calculators, directories). Not used for logged-in sites.
- **Python + pandas + SQLite** → the local CRM/research pipeline in `src/` (import, dedupe, validate, score, queue, draft generation).
- **Subagents** → parallel research streams with a fixed output file each (see plan below).

## 4. Tasks that can be completed immediately

- Market research on the four hypotheses from public sources (vendor pages, reviews snippets, Reddit, job boards, government MSME publications).
- Competitor pricing and features from official pricing pages.
- Agency/consultant acquisition study from their public websites, case-study pages, marketplace profiles.
- Prospect discovery from company websites and public directories reachable without login.
- Official contact pages / published business emails and phone numbers from company websites.
- Building and testing the Python tooling.
- Drafting (not sending) outreach.

## 5. Tasks that need additional setup or your authorisation

| Task | Why blocked | What you would need to do |
|---|---|---|
| Decision-maker identification at scale via LinkedIn | Login wall + ToS | Look up names manually in your own LinkedIn, or approve use of Claude-in-Chrome on public profile pages one at a time |
| Google Maps bulk discovery | No API key; scraping prohibited | Optional: create a Google Places API key (free monthly credit, billing account required) — needs your approval |
| Email verification / enrichment | No tool configured | Optional free tier of Hunter/Apollo — needs your approval and sign-up |
| G2 / Capterra full review text | Pages often blocked to fetchers | Manual reading in your browser; I record only what I can actually access |
| Sending any outreach (email, LinkedIn, forms) | Policy: no external contact without approval | You review `outreach/OUTREACH_QUEUE.csv` and send yourself, or explicitly approve each send |
| Excel output | openpyxl missing | `pip install openpyxl` (free) if you want .xlsx |

## 6. Known limitations affecting research quality

- WebSearch is US-centric; India-local results (e.g. Hyderabad coaching institutes) are thinner, so more manual verification is needed per prospect.
- WebFetch summarises pages with a small model. Prices and names extracted this way are spot-checked; any unverified field is labelled.
- Review-site content (G2/Capterra/Trustpilot) is frequently inaccessible; complaints are taken from pages that could actually be read (Reddit, app-store pages, accessible review pages) and labelled as customer opinion.
- Company size is rarely verifiable without LinkedIn; it is left blank unless a source states it.

## 7. Phased execution plan

| Phase | Output files | How |
|---|---|---|
| 1 Environment | this file | done |
| 2 Market + competitors | `MARKET_OVERVIEW.md`, `COMPETITOR_MATRIX.csv`, `COMPETITIVE_ANALYSIS.md` | 2 parallel research subagents (segments A/B and C/D) |
| 3 Agency acquisition | `COMPETITOR_ACQUISITION_STUDY.md/.csv` | 1 subagent |
| 4 Niche comparison + buyer hypotheses | `DEMAND_VALIDATION.md`, `outreach/INTERVIEW_GUIDE.md` | main session, after phases 2–3 |
| 5–6 Prospects + contacts | `data/prospects.csv`, `data/contacts.csv`, `BUYING_SIGNALS.md`, `CONTACT_RESEARCH_METHOD.md` | subagents per niche, then a data-quality audit |
| 7 Scoring + outreach drafts | `PROSPECT_SCORING.md`, `outreach/*` | Python scoring + generated drafts, human review queue |
| 8 Tooling | `src/*.py`, `tests/*.py`, `data/prospects.db` | main session, pytest |
| 9 Recommendation | `FINAL_RECOMMENDATION.md` | main session |
