"""Import research CSVs into SQLite and export data/prospects.csv and data/contacts.csv.

Usage:  python src/import_prospects.py [extra.csv ...]
Reads every data/parts/prospects_*.csv (plus any paths given), deduplicates, assigns
stable IDs, scores, and upserts into data/prospects.db. Every changed field is written
to the `change_log` table with old and new value, so evidence is never lost.
Human-edited tracking fields (research_status, outreach_status, next_action) are preserved.
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from common import (ALL_COLUMNS, CONTACTS_CSV, DATA, DB_PATH, PARTS, PROSPECTS_CSV, RAW_COLUMNS,
                    TRACKING_COLUMNS, blank, ensure_columns, make_prospect_id, normalize_name,
                    read_csv)
from deduplicate import deduplicate
from score_prospects import score

ANGLES = {
    "A_education": "Ask how inquiries from ads/WhatsApp/web forms are assigned and followed up across counsellors",
    "B_documents_logistics": "Ask how invoice/PO/shipping documents get from PDF/email into Tally/ERP today",
    "C_agency_b2b_services": "Ask how long monthly client reports take to assemble across ad/analytics platforms",
    "D_saas_ecommerce": "Ask what share of support tickets are repetitive (order status, returns, how-to)",
}
CONTACT_COLUMNS = ["contact_id", "prospect_id", "company_name", "person_name", "role", "channel",
                   "value", "contact_type", "source_url", "verified_status", "notes", "last_verified"]


def load_parts(extra: list[Path]) -> pd.DataFrame:
    paths = sorted(PARTS.glob("prospects_*.csv")) + extra
    frames = []
    for p in paths:
        df = ensure_columns(read_csv(p), RAW_COLUMNS)[RAW_COLUMNS]
        df["_source_file"] = p.name
        frames.append(df)
        print(f"loaded {len(df):3d} rows from {p.name}")
    if not frames:
        raise SystemExit("no input files found in data/parts/")
    return pd.concat(frames, ignore_index=True)


def build_contacts(df: pd.DataFrame) -> pd.DataFrame:
    """One row per contact channel, each tagged with its source and verification type."""
    rows = []

    def add(r, person, role, channel, value, ctype, source, status, notes=""):
        rows.append({"prospect_id": r["prospect_id"], "company_name": r["company_name"],
                     "person_name": person, "role": role, "channel": channel, "value": value,
                     "contact_type": ctype, "source_url": source, "verified_status": status,
                     "notes": notes, "last_verified": r.get("last_verified", "")})

    for _, r in df.iterrows():
        if not blank(r["decision_maker_name"]):
            add(r, r["decision_maker_name"], r["decision_maker_role"], "named_person", "",
                "public_professional_profile", r["decision_maker_source_url"],
                "role stated on source page" if not blank(r["decision_maker_source_url"]) else "unverified")
        if not blank(r["linkedin_url"]):
            add(r, r["decision_maker_name"], r["decision_maker_role"], "linkedin", r["linkedin_url"],
                "public_professional_profile", r["linkedin_url"], "URL seen in public source; not opened",
                "Open manually in your own LinkedIn; do not scrape")
        if not blank(r["public_email"]):
            add(r, "", "", "email", r["public_email"], "verified_public_business_contact",
                r["public_email_source"], "published on source page" if not blank(r["public_email_source"]) else "unverified",
                "Generic business inbox unless stated otherwise")
        if not blank(r["public_phone"]):
            add(r, "", "", "phone", r["public_phone"], "verified_public_business_contact",
                r["public_phone_source"], "published on source page" if not blank(r["public_phone_source"]) else "unverified")
        if not blank(r["contact_page_url"]):
            add(r, "", "", "contact_form", r["contact_page_url"], "official_contact_form",
                r["contact_page_url"], "official site")
        if all(blank(r[c]) for c in ["public_email", "public_phone", "contact_page_url", "linkedin_url"]):
            add(r, "", "", "none", "", "unknown", "", "unavailable", "Find official contact route")
    out = pd.DataFrame(rows, columns=[c for c in CONTACT_COLUMNS if c != "contact_id"])
    out.insert(0, "contact_id", [f"C-{i:04d}" for i in range(1, len(out) + 1)])
    return out


def upsert(df: pd.DataFrame, db_path: Path = DB_PATH) -> int:
    """Write prospects to SQLite, logging every changed field. Returns number of changes."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con = sqlite3.connect(db_path)
    con.execute(f"CREATE TABLE IF NOT EXISTS prospects ({', '.join(c + ' TEXT' for c in ALL_COLUMNS)}, "
                "PRIMARY KEY (prospect_id))")
    con.execute("CREATE TABLE IF NOT EXISTS change_log (changed_at TEXT, prospect_id TEXT, field TEXT, "
                "old_value TEXT, new_value TEXT)")
    existing_cols = [r[1] for r in con.execute("PRAGMA table_info(prospects)")]
    for col in ALL_COLUMNS:
        if col not in existing_cols:
            con.execute(f"ALTER TABLE prospects ADD COLUMN {col} TEXT")
    old = pd.read_sql("SELECT * FROM prospects", con).set_index("prospect_id") if existing_cols else pd.DataFrame()
    changes = 0
    for _, r in df.iterrows():
        pid = r["prospect_id"]
        prev = old.loc[pid] if pid in old.index else None
        for col in ALL_COLUMNS:
            new_v = "" if blank(r.get(col)) else str(r.get(col))
            old_v = "" if prev is None or blank(prev.get(col)) else str(prev.get(col))
            if new_v != old_v:
                con.execute("INSERT INTO change_log VALUES (?,?,?,?,?)", (now, pid, col, old_v, new_v))
                changes += 1
        con.execute(f"INSERT OR REPLACE INTO prospects ({', '.join(ALL_COLUMNS)}) VALUES "
                    f"({', '.join('?' for _ in ALL_COLUMNS)})",
                    [("" if blank(r.get(c)) else str(r.get(c))) for c in ALL_COLUMNS])
    con.commit()
    con.close()
    return changes


def preserve_tracking(df: pd.DataFrame) -> pd.DataFrame:
    """Carry over human-edited tracking fields from the current prospects.csv."""
    if not PROSPECTS_CSV.exists():
        return df
    prev = read_csv(PROSPECTS_CSV)
    if "prospect_id" not in prev.columns:
        return df
    prev = ensure_columns(prev, TRACKING_COLUMNS).set_index("prospect_id")[TRACKING_COLUMNS]
    for col in TRACKING_COLUMNS:
        df[col] = [prev.at[p, col] if p in prev.index and not blank(prev.at[p, col]) else v
                   for p, v in zip(df["prospect_id"], df[col])]
    return df


def drop_excluded(df: pd.DataFrame) -> pd.DataFrame:
    """Remove businesses listed in data/excluded.csv (competitors, unverifiable), with a printed reason."""
    path = DATA / "excluded.csv"
    if not path.exists():
        return df
    excluded = read_csv(path)
    keys = set(excluded["company_name"].map(normalize_name))
    mask = df["company_name"].map(normalize_name).isin(keys)
    for name in df.loc[mask, "company_name"]:
        print(f"excluded: {name}")
    return df[~mask]


def run(extra: list[Path] | None = None) -> pd.DataFrame:
    raw = drop_excluded(load_parts(extra or []))
    deduped, merges = deduplicate(raw.drop(columns=["_source_file"]))
    print(f"{len(raw)} raw rows -> {len(deduped)} unique ({len(merges)} merged groups)")
    deduped = ensure_columns(deduped, ALL_COLUMNS)
    deduped["prospect_id"] = [make_prospect_id(d, n) for d, n in zip(deduped["domain"], deduped["company_name"])]
    deduped["opening_angle"] = deduped["segment"].map(ANGLES).fillna("")
    deduped["research_status"] = deduped.apply(
        lambda r: "needs_workflow_evidence" if r["workflow_evidence_strength"] in ("", "none", "weak")
        else "needs_decision_maker" if blank(r["decision_maker_name"]) else "ready_for_review", axis=1)
    deduped["outreach_status"] = "not_contacted"
    deduped["next_action"] = deduped["research_status"].map({
        "needs_workflow_evidence": "Find job post / public statement showing the workflow",
        "needs_decision_maker": "Identify owner/ops head from official team page or your LinkedIn",
        "ready_for_review": "Review outreach draft and approve sending method",
    })
    deduped = preserve_tracking(deduped)
    scored = score(deduped)[ALL_COLUMNS]
    scored.to_csv(PROSPECTS_CSV, index=False, encoding="utf-8")
    build_contacts(scored).to_csv(CONTACTS_CSV, index=False, encoding="utf-8")
    n = upsert(scored)
    print(f"wrote {PROSPECTS_CSV.name} ({len(scored)}), {CONTACTS_CSV.name}, db changes logged: {n}")
    return scored


if __name__ == "__main__":
    run([Path(p) for p in sys.argv[1:]])
