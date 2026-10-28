# Prospect Scoring Model

Implemented in `src/score_prospects.py`; tested in `tests/test_scoring.py`. Every prospect row in
`data/prospects.csv` carries the five component scores and a `score_explanation` listing exactly
which evidence earned which points. **Missing evidence earns zero — it is never assumed.**

## Components (100 points)

| Component | Max | Points awarded for (each needs evidence in the row) |
|---|---|---|
| Customer-profile fit | 25 | +10 existence verified on official site · +8 profile evidence with source URL · +3 niche identified · +4 company size with a source. Capped at 8 if the business is not verified |
| Evidence of relevant workflow | 25 | `weak` (industry inference only) 5 · `moderate` (site shows workflow exists / volume) 14 · `strong` (job post or public statement showing the manual work) 22 · +3 if the evidence has a URL |
| Likely financial value | 20 | +4 per distinct value signal, max 3 (branches, volume claims, offices) · +4 already uses paid software · +4 buying signal present |
| Reachability | 15 | +6 named decision-maker with an official source · +4 published business email with source · +2 published phone with source · +2 official contact page · +1 public profile URL |
| Recency & quality | 15 | Evidence ≤90 days 8 / ≤365 days 5 / older 2 / undated 0 · +4 primary URLs for both fit and workflow · +3 buying signal ≤180 days old |

Deliberately **not** rewarded: having a website, social media presence, or merely belonging to a target industry.

## Three separate labels
- **Verified** — `verification_status = verified`: official website loaded and business exists.
- **Qualified** — verified **and** fit score ≥18 (profile evidence with URL + niche).
- **High-priority** — qualified **and** workflow evidence is `moderate` or `strong`.

## Tiers
- **Tier A** — score ≥70 **and** high-priority. Research/contact first.
- **Tier B** — score ≥45 and qualified. Relevant profile; at least one uncertainty remains.
- **Tier C** — everything else. Do not prioritise until more is known.

## Confidence
- `high` — strong workflow evidence dated within 180 days.
- `medium` — moderate or strong evidence.
- `low` — weak or no workflow evidence.

## Caveats
These scores are heuristics built from public signals. They say nothing about intent to buy. After the
first 30 conversations, compare reply/qualification rates by tier and component; if Tier A does not
outperform Tier B, re-weight (e.g. raise reachability, lower value signals).

## Current distribution
See the "Results" section appended below after each import run.


## Results (run 2026-10-28, 95 prospects after excluding 5 — see `data/excluded.csv`)

### Tier by segment
| segment | A | B | C |
|---|---|---|---|
| A_education | 2 | 20 | 0 |
| B_documents_logistics | 2 | 26 | 2 |
| C_agency_b2b_services | 3 | 22 | 0 |
| D_saas_ecommerce | 1 | 14 | 3 |

Totals: Tier A 8, Tier B 82, Tier C 5. Verified 95, qualified 95, high-priority 57.
Score range 36–91, median 63.

### Calibration changes made during the audit (2026-10-28)
1. **Access date is not evidence date.** Research passes stamped `evidence_date` with the access date; such rows now earn 3 recency points ("live page, publication date unknown") instead of 8.
2. **Unopened signals earn nothing.** Buying signals marked snippet-only / "not opened" / "page exists" get 0 value and 0 recency points and cannot make a prospect Tier A.
3. **Tier A requires direct evidence**: `strong` workflow evidence, or `moderate` plus an opened buying signal. Before these changes 44 prospects were Tier A; after, 8. The earlier count was inflated by site-only evidence.
4. Spot-check of three Tier A job posts (Raleigh Digital, Ishwar Pharma, GEL Studios) against live pages: all duties confirmed; none shows a posting date; Raleigh's founder name is not on the job page (the cited source is the homepage).

### Interpretation
Most prospects are Tier B because public evidence rarely shows the workflow *hurting*. Tier B is not "worse leads", only "less evidence". Interviews, not more desk research, are the efficient way to separate them.
