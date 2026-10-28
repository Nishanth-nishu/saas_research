"""Compile research/BUYING_SIGNALS.md from data/prospects.csv."""
from __future__ import annotations

import pandas as pd

from common import PROSPECTS_CSV, RESEARCH, read_csv
from score_prospects import _UNOPENED

HEADER = """# Buying Signals

Compiled from `data/prospects.csv` by `src/build_signals_report.py` (first run 2026-10-28). The raw
per-segment tables and discovery notes are in `research/parts/signals_[A-D].md`.

**Every signal is a hypothesis about possible need, not proof of intent to buy.** Never tell a prospect you
know their internal problem; at most reference the public fact (e.g. "I saw you're hiring a reporting specialist").

## How signals were judged
- **Opened**: the source page was actually loaded and the signal seen. Counted in scoring.
- **Snippet/unopened**: seen only in a search-result summary, or the page exists but was not opened. Recorded,
  but earns **zero** points until someone opens it (`score_prospects.has_real_signal`).
- **Date**: most job boards reached (Weekday, Indeed snippets, agency careers pages) show **no posting date**.
  Undated signals must be re-checked before use.
"""

FOOTER = """
## Signal types that proved most useful

| Signal type | Where found | Strength | Notes |
|---|---|---|---|
| Company's own careers page listing a manual role with duties (reporting specialist, billing/reconciliation, documentation) | Raleigh Digital, GEL Studios, Ishwar Pharma careers pages (re-opened 2026-10-28) | Strong | Best evidence found; all three undated |
| Dated job post with duties and tools (Freshdesk, Shopify, Sheets) | Talentmate (Aramya, 2026-09-08) | Strong | Only dated source found for segment D |
| Several concurrent postings for the same manual role | jobs.weekday.works | Moderate | Names employer + role; no date or duties |
| Agency site stating weekly/monthly reports and Looker Studio dashboards as deliverables | Agency homepages | Moderate | Shows the workflow exists, not that it hurts |
| Multi-branch footprint + many inquiry channels (forms, WhatsApp, callback) | Education consultancies' sites | Moderate | Volume proxy only |
| Search snippets of Indeed/Naukri listings | Search results | Weak until opened | Indeed/Naukri blocked to the fetcher; open manually in a browser |

## Next steps to strengthen signals
1. Open each undated Weekday/Indeed listing in a normal browser and record the posting date (about 5 min each).
2. For Tier B prospects, open the `/careers` pages flagged "not opened".
3. Re-check every signal within 7 days before referencing it in outreach; job posts close.
"""


def md_table(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False))


def _cell(text: str, n: int) -> str:
    return str(text).replace("|", "/").replace("\n", " ")[:n]


def build(df: pd.DataFrame) -> str:
    df = df.copy()
    df["qs"] = pd.to_numeric(df["qualification_score"], errors="coerce").fillna(0)
    s = df[df["buying_signals"] != ""].sort_values(["segment", "qs"], ascending=[True, False])
    s = s.assign(opened=~s["buying_signals"].str.contains(_UNOPENED))
    summary = s.groupby("segment").agg(
        signals=("company_name", "count"), opened=("opened", "sum"),
        dated=("buying_signal_date", lambda x: int((x != "").sum()))).reset_index()
    out = [HEADER, "## Summary\n", md_table(summary), "\n## Signals by prospect\n"]
    for seg, g in s.groupby("segment"):
        out += [f"### {seg}\n", "| Prospect | Tier | Signal | Source | Signal date | Relevance (workflow) | Status | Confidence |",
                "|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            out.append(f"| {r.company_name} ({r.prospect_id}) | {r.tier} | {_cell(r.buying_signals, 180)} | "
                       f"{r.buying_signal_url.split('|')[0].strip()} | {r.buying_signal_date or 'undated'} | "
                       f"{_cell(r.workflow_hypothesis, 90)} | {'opened' if r.opened else 'snippet/unopened'} | {r.confidence} |")
        out.append("")
    return "\n".join(out) + FOOTER


if __name__ == "__main__":
    text = build(read_csv(PROSPECTS_CSV))
    (RESEARCH / "BUYING_SIGNALS.md").write_text(text, encoding="utf-8")
    print(text[text.index("## Summary"):text.index("## Signals by prospect")])
