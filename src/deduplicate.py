"""Deduplicate prospects by normalised domain, then by normalised name + country.

When two rows describe the same business, non-empty values are kept and conflicting
evidence fields are concatenated (never silently dropped) so no source is lost.
"""
from __future__ import annotations

import pandas as pd

from common import blank, normalize_domain, normalize_name

# Fields where differing values from two sources are both kept
MERGE_APPEND = {
    "fit_evidence", "fit_evidence_url", "workflow_evidence", "workflow_evidence_url",
    "value_signals", "software_signals", "buying_signals", "buying_signal_url", "research_gaps",
}
STRENGTH_RANK = {"": -1, "none": 0, "weak": 1, "moderate": 2, "strong": 3}


def _merge_rows(rows: pd.DataFrame) -> dict:
    merged: dict = {}
    for col in rows.columns:
        values = [str(v).strip() for v in rows[col] if not blank(v)]
        unique = list(dict.fromkeys(values))
        if not unique:
            merged[col] = ""
        elif col == "workflow_evidence_strength":
            merged[col] = max(unique, key=lambda v: STRENGTH_RANK.get(v, -1))
        elif col in {"evidence_date", "buying_signal_date", "last_verified"}:
            merged[col] = max(unique)
        elif col in MERGE_APPEND and len(unique) > 1:
            merged[col] = " | ".join(unique)
        else:
            merged[col] = unique[0]
    return merged


def deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Return (deduplicated frame, log of merges)."""
    df = df.copy()
    df["domain"] = df["website"].map(normalize_domain)
    df["_name_key"] = df["company_name"].map(normalize_name) + "|" + df["country"].str.lower().str.strip()
    # Group key: domain when present, otherwise name+country
    df["_key"] = df.apply(lambda r: r["domain"] or r["_name_key"], axis=1)
    # Rows sharing a name+country with different/no domain also collapse onto the first key seen
    name_to_key: dict[str, str] = {}
    for idx, row in df.iterrows():
        nk = row["_name_key"]
        if nk.split("|")[0] and nk in name_to_key:
            df.at[idx, "_key"] = name_to_key[nk]
        else:
            name_to_key.setdefault(nk, row["_key"])

    log: list[dict] = []
    out_rows = []
    for key, group in df.groupby("_key", sort=False):
        if len(group) > 1:
            log.append({"key": key, "merged_names": "; ".join(group["company_name"]), "count": len(group)})
        out_rows.append(_merge_rows(group.drop(columns=["_key", "_name_key"])))
    return pd.DataFrame(out_rows), log


if __name__ == "__main__":
    from common import PROSPECTS_CSV, read_csv

    frame = read_csv(PROSPECTS_CSV)
    deduped, merges = deduplicate(frame)
    print(f"{len(frame)} rows -> {len(deduped)} after dedupe; {len(merges)} merge groups")
    for m in merges:
        print(" ", m)
