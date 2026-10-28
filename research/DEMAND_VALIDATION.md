# Demand Validation — top three niches

Research date: 2026-10-28. Inputs: `MARKET_OVERVIEW.md`, `parts/market_AB.md`, `parts/market_CD.md`,
`COMPETITOR_ACQUISITION_STUDY.md`, `BUYING_SIGNALS.md`, `data/prospects.csv`.

The three niches compared were chosen for buyer access from Hyderabad/India, fit with the founder's skills, and
weaker AI-SaaS competition at the SMB end. Agency client reporting (C-W1) was the strongest of the rest, but cheap
AI-equipped tools ($20/client/mo) leave it little room.

- **N1 — Study-abroad consultancies and test-prep institutes (India):** inquiry → counselling → application follow-up.
- **N2 — SMB freight forwarders and customs brokers (India):** shipping-document extraction (BL, invoice, packing list) into job sheets and checklists.
- **N3 — Digital marketing agencies (India and international):** client reporting with written commentary.

## 1. What public research supports vs what needs interviews

| Question | N1 Study-abroad | N2 Forwarders/CHAs | N3 Agencies |
|---|---|---|---|
| Does the workflow exist? | **Supported.** Counsellor job duties (FACT) and multi-channel intake on 22 verified sites | **Supported.** Documentation job posts (Transcon, Palram FACT); document set per shipment | **Supported.** Reporting job duties at 3 agencies (FACT); reports listed as deliverables |
| How often? | Partly supported: daily, every lead (job posts). Volume per firm unknown | Partly supported: per shipment. Falcon claims 500+/month (VENDOR_CLAIM) | Supported: monthly per client |
| Staff time spent | **Interview needed.** Only vendor claims (80–150 leads/day/counsellor) | **Interview needed.** Vendor claim of 10–15 min per BOL | **Interview needed.** Vendor claims conflict (2–5 h vs <30 min per report) |
| Cost of errors and delays | **Interview needed.** Lost-student value unknown | **Interview needed.** Demurrage and holds (VENDOR_CLAIM only) | Interview needed |
| Current tools | Supported: WhatsApp, forms, Sheets; some LeadSquared/Meritto; Leadz runs an AI chat | Partly supported: Logi-Sys, CargoWise, Excel; mostly unknown per firm | Supported: Looker Studio and AgencyAnalytics visible |
| Previous attempts | Interview needed | Interview needed | Interview needed |
| Budget owner | **Hypothesis:** founder/director | **Hypothesis:** owner/director; accounts or operations head | **Hypothesis:** founder/head of delivery |
| Urgency | **Hypothesis:** seasonal around intakes (Jan/Sep) | Unknown | Unknown |
| Security/integration needs | Partly supported: DPDP (student data, possibly minors) from about May 2027; WhatsApp template rules | Partly supported: DPDP processor duties; no write access to ICEGATE (HYPOTHESIS) | Partly supported: Google Ads API access levels; client data access |
| Can the buyer run a paid pilot? | **Interview needed.** Price anchors ₹2.5–16.8k/mo for tools; agencies charge ₹35k+ per build | **Interview needed.** Staff cost ₹40–60k/mo suggests room | Partly supported: they pay $20/client/mo for tools; custom budget unknown |
| Same solution for many buyers? | Supported (HYPOTHESIS strength): same funnel shape across firms | Partly: fields repeat, but carrier layouts and target systems vary | Supported: same platforms everywhere |

## 2. Scorecard (1–5, public evidence only; re-score after interviews)

| Criterion | N1 | Evidence | N2 | Evidence | N3 | Evidence |
|---|---|---|---|---|---|---|
| Pain frequency | 5 | Every lead, daily | 4 | Every shipment | 4 | Monthly per client |
| Financial impact | 3 | Revenue-linked; unquantified | 4 | Higher-paid staff; error cost claimed | 3 | Hours per report claimed |
| Budget and urgency | 3 | Pay for WhatsApp and CRM tools; Meritto "too costly" for small firms | 3 | Pay for TMS; SMB willingness unknown | 3 | Tools priced per client |
| Repeatability | 4 | Same funnel | 3 | Layout variety | 4 | Same platforms |
| Access to buyers | 4 | Hyderabad cluster (Ameerpet), Kerala; owners visible; local visits possible | 2 | Port cities; trust barrier | 4 | Founders visible online; global |
| Implementation feasibility | 4 | WhatsApp BSP + n8n + Sheets | 3 | Extraction easy; writing into their software hard | 3 | Ads API verification; Looker Studio route easier |
| Competitive differentiation | 2 | Crowded tools, but weak implementation at the SMB end | 3 | Enterprise tools overpriced for SMBs; Logi-Sys AI is a threat | 2 | Tools ship AI summaries |
| **Total /35** | **25** | | **22** | | **23** | |

## 3. Recommendation
- **Primary to test: N1, study-abroad consultancies and test-prep institutes.** It has the best combination of buyer access for a Hyderabad-based founder, a daily workflow, third-party evidence that follow-up fails (Edified 2025; ICEF agent survey), and budget already spent on adjacent tools. The offer must be **implementation on the buyer's existing stack**, not another CRM.
- **Fallback: N2, SMB forwarders and customs brokers, shipping-document extraction.** It has a higher value per document and enterprise tools priced out of reach for SMBs. Buyer access is harder and local software is adding AI.
- **N3** stays as an opportunistic international channel (Upwork/Contra productised offer), not the primary focus.

**Confidence: low to medium.** Desk research separates these niches only by about 3 points. The recommendation
is a decision about **where to run interviews first**, not a product commitment.

## 4. Validation plan (2–3 weeks, about 25 h/week)
1. **Interviews:** at least 12 in N1 and at least 6 in N2, using `outreach/INTERVIEW_GUIDE.md`. Source them in this order: warm intros (IIITH network, people who used Hyderabad consultancies), in-person visits to Ameerpet test-prep and consultancy offices, then shortlist emails.
2. **Record for each interview:** leads/month, counsellors, response-time practice, tools and their cost, lost-lead estimate, who signs off on spend, pilot interest (0–3 scale in the guide).
3. **Go criteria for N1, after 12 interviews:**
   - at least 6 firms describe the follow-up gap with numbers;
   - at least 4 name the owner as budget holder and say ₹25k+ is plausible;
   - at least 2 ask for a pilot proposal.
4. **Kill or switch criteria:** fewer than 3 firms quantify the problem; firms are satisfied with Wati or Interakt and see no gap; or price acceptance is below ₹15k one-time. If triggered, run the same test on N2.
5. **Never pitch in the first 20 minutes of an interview.** A pilot is proposed only when the respondent asks.
