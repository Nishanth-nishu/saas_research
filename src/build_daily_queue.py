"""Export today's prioritised work queue: research gaps to close and drafts awaiting review.

Usage: python src/build_daily_queue.py [N]   (default 15 items)
Writes data/daily_queue_<date>.csv.
"""
from __future__ import annotations

import sys

import pandas as pd

from common import DATA, PROSPECTS_CSV, read_csv, today

DONE = {"won", "lost", "do_not_contact", "meeting_booked"}
STATUS_PRIORITY = {"replied": 0, "contacted": 1, "approved": 2, "draft_ready": 3, "not_contacted": 4}


def build_queue(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    df = df[~df["outreach_status"].isin(DONE)].copy()
    df["qualification_score"] = pd.to_numeric(df["qualification_score"], errors="coerce").fillna(0)
    df = df[df["tier"].isin(["A", "B"]) | df["outreach_status"].isin(["replied", "contacted"])]
    df["_p"] = df["outreach_status"].map(STATUS_PRIORITY).fillna(5)
    df = df.sort_values(["_p", "tier", "qualification_score"], ascending=[True, True, False])
    cols = ["prospect_id", "company_name", "segment", "tier", "qualification_score",
            "outreach_status", "research_status", "next_action", "website", "contact_page_url"]
    return df.head(n)[cols]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    q = build_queue(read_csv(PROSPECTS_CSV), n)
    path = DATA / f"daily_queue_{today()}.csv"
    q.to_csv(path, index=False)
    print(q.to_string(index=False))
    print(f"\nsaved {path}")
