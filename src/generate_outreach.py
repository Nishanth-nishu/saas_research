"""Generate outreach DRAFTS (never sends anything) for qualified prospects.

Writes outreach/OUTREACH_DRAFTS.md and outreach/OUTREACH_QUEUE.csv. Every draft cites the
evidence it relies on and lists facts that must be checked by a human before sending.
Sender details come from environment variables so nothing personal is hard-coded:
  SENDER_NAME, SENDER_AFFILIATION (e.g. "IIIT Hyderabad alumnus" - state it accurately)
"""
from __future__ import annotations

import os

import pandas as pd

from common import DATA, OUTREACH, PROSPECTS_CSV, blank, read_csv

SENDER = os.environ.get("SENDER_NAME", "[Your Name]")
AFFIL = os.environ.get("SENDER_AFFILIATION", "[accurate IIITH affiliation, e.g. 'IIIT Hyderabad alumnus']")

# Per-segment wording. Phrased as questions: we do not claim to know their internal problem.
SEGMENT_COPY = {
    "A_education": {
        "subject": "Question about how {company} handles student inquiries",
        "problem": "assigning and following up inquiries from ads, WhatsApp and web forms across counsellors",
        "topic": "student inquiry follow-up",
        "offer": "a small automation that captures every inquiry in one place, routes it to a counsellor and nudges follow-ups",
        "question": "How do new inquiries reach your counsellors today, and how do you track who has followed up?",
    },
    "B_documents_logistics": {
        "subject": "Question about document data entry at {company}",
        "problem": "typing data from invoices and POs into Tally or your ERP by hand",
        "topic": "invoice and PO data entry",
        "offer": "an extraction workflow that reads those documents and prepares entries for review before they go into your system",
        "question": "Roughly how many documents does your team key in per week, and where do errors usually creep in?",
    },
    "C_agency_b2b_services": {
        "subject": "Client reporting at {company}",
        "problem": "assembling monthly client reports by hand from ad, analytics and SEO platforms",
        "topic": "client reporting",
        "offer": "an automated reporting pipeline that pulls the numbers and drafts the commentary for your team to edit",
        "question": "How many hours does your team spend on client reports each month, and which part is most manual?",
    },
    "D_saas_ecommerce": {
        "subject": "Repetitive support questions at {company}",
        "problem": "answering repetitive tickets (order status, returns, how-to questions)",
        "topic": "repetitive support tickets",
        "offer": "a triage and draft-reply assistant that sits inside your existing help desk and keeps humans in control",
        "question": "What share of your tickets are repeat questions, and how are they handled today?",
    },
}


FORWARDER_COPY = {
    "subject": "Question about shipment documentation at {company}",
    "problem": "re-typing data from BLs, invoices and packing lists into job sheets, checklists and billing",
    "topic": "shipment documentation",
    "offer": "an extraction step that reads those documents and prepares a pre-filled job sheet or checklist for your team to check",
    "question": "Roughly how many shipments a month does your documentation team handle, and which documents take longest to key in?",
}


def _copy_for(r: pd.Series) -> dict:
    niche = str(r.get("niche", "")).lower()
    if r["segment"] == "B_documents_logistics" and any(k in niche for k in ("forward", "cha", "customs", "nvocc")):
        return FORWARDER_COPY
    return SEGMENT_COPY.get(r["segment"], SEGMENT_COPY["C_agency_b2b_services"])


def _first(value: str) -> str:
    return str(value or "").split("|")[0].strip()


def _greeting(r: pd.Series) -> str:
    name = str(r.get("decision_maker_name", "")).strip()
    return f"Hi {name.split()[0]}," if name else "Hello,"


def _evidence_line(r: pd.Series) -> str:
    ev = _first(r.get("buying_signals")) or _first(r.get("workflow_evidence")) or _first(r.get("fit_evidence"))
    return ev[:220]


def build_draft(r: pd.Series) -> dict:
    copy = _copy_for(r)
    company = r["company_name"].split(" (")[0]
    evidence = _evidence_line(r)
    signal_based = not blank(r.get("buying_signals"))
    # The public signal is not pasted verbatim: a human checks it and writes one honest sentence about it
    observed = ("[Optional, only after re-checking the source: one sentence on the public fact, e.g. "
                "\"I saw you're hiring for <role>\".]\n\n" if signal_based else "")
    email = (
        f"Subject: {copy['subject'].format(company=company)}\n\n"
        f"{_greeting(r)}\n\n"
        f"{observed}I came across {company} while looking at how teams like yours work, and I'm curious whether "
        f"{copy['problem']} takes up a meaningful share of your team's time.\n\n"
        f"I'm {SENDER}, {AFFIL}, and I build AI and workflow automations for small teams. I'm currently speaking with "
        f"businesses like yours to understand this workflow before building anything.\n\n"
        f"{copy['question']}\n\n"
        f"If it is a real bottleneck, I'd be glad to share a short demo of {copy['offer']}. "
        f"If not, a one-line reply saying so would still help me a lot.\n\n"
        f"Thanks,\n{SENDER}\n\n"
        f"(If you'd prefer not to hear from me again, just reply 'no' and I won't follow up.)"
    )
    linkedin = (f"Hi{' ' + r['decision_maker_name'].split()[0] if not blank(r.get('decision_maker_name')) else ''}, "
                f"I'm researching how teams like yours at {company} handle {copy['topic']}. "
                f"Would value your perspective — happy to share what I'm learning. — {SENDER}")[:295]
    follow_up = (
        f"{_greeting(r)}\n\nFollowing up once on my note about {copy['topic']}. "
        f"Even a quick 'not relevant' helps. If it is relevant, a 15-minute call this week or next would be great.\n\n"
        f"Thanks,\n{SENDER}"
    )
    verify = ["Confirm the evidence below is still current (open the URL)"]
    if blank(r.get("decision_maker_name")):
        verify.append("No named decision-maker: address the team, or find the owner/ops head manually")
    else:
        verify.append(f"Confirm {r['decision_maker_name']} still holds role '{r.get('decision_maker_role')}'")
    if signal_based:
        verify.append("Buying signal (e.g. job post) may be closed — re-check before referencing it")
    verify.append("Fill in SENDER_NAME / SENDER_AFFILIATION accurately; no implied institutional endorsement")
    channel = ("email: " + _first(r["public_email"])) if not blank(r.get("public_email")) else \
        ("contact form: " + r["contact_page_url"]) if not blank(r.get("contact_page_url")) else \
        ("LinkedIn (manual): " + r["linkedin_url"]) if not blank(r.get("linkedin_url")) else "unknown — research needed"
    return {
        "prospect_id": r["prospect_id"], "company_name": company, "tier": r["tier"],
        "qualification_score": r["qualification_score"], "segment": r["segment"],
        "decision_maker": r.get("decision_maker_name", ""), "role": r.get("decision_maker_role", ""),
        "suggested_channel": channel, "evidence": evidence,
        "evidence_url": _first(r.get("buying_signal_url")) or _first(r.get("workflow_evidence_url")) or _first(r.get("fit_evidence_url")),
        "hypothesis": r.get("workflow_hypothesis", "") or copy["problem"],
        "why_relevant": copy["offer"], "cta": "15-minute workflow conversation or short demo",
        "confidence": r.get("confidence", ""), "email_draft": email, "linkedin_note": linkedin,
        "follow_up_draft": follow_up, "verify_before_sending": "; ".join(verify),
        "approval_status": "pending_review", "sent_status": "not_sent",
    }


def generate(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """Drafts for data/shortlist.csv in its order if present, else the top Tier A/B prospects."""
    shortlist = DATA / "shortlist.csv"
    if shortlist.exists():
        sl = read_csv(shortlist)
        pool = df.set_index("prospect_id").loc[sl["prospect_id"]].reset_index()
        pool["why_shortlisted"] = sl["why_shortlisted"].values
    else:
        pool = df[df["tier"].isin(["A", "B"])].sort_values("qualification_score", ascending=False).head(top_n)
        pool["why_shortlisted"] = ""
    return pd.DataFrame([{**build_draft(r), "why_shortlisted": r["why_shortlisted"]} for _, r in pool.iterrows()])


def write_markdown(drafts: pd.DataFrame) -> str:
    out = ["# Outreach Drafts — REVIEW QUEUE (nothing has been sent)\n",
           "Generated by `src/generate_outreach.py`. Each draft must be reviewed, edited and approved "
           "by you; see `OUTREACH_POLICY.md`.\n"]
    for _, d in drafts.iterrows():
        out += [f"\n---\n\n## {d['company_name']} ({d['prospect_id']}) — Tier {d['tier']}, score {d['qualification_score']}\n",
                f"- **Why shortlisted:** {d['why_shortlisted']}",
                f"- **Decision-maker:** {d['decision_maker'] or 'not identified'} {('— ' + d['role']) if d['role'] else ''}",
                f"- **Suggested channel:** {d['suggested_channel']}",
                f"- **Evidence:** {d['evidence']}",
                f"- **Source:** {d['evidence_url']}",
                f"- **Hypothesis (unverified):** {d['hypothesis']}",
                f"- **Why relevant:** {d['why_relevant']}",
                f"- **CTA:** {d['cta']} · **Confidence:** {d['confidence']}",
                f"- **Verify before sending:** {d['verify_before_sending']}\n",
                "**Email draft**\n", "```text", d["email_draft"], "```",
                "**LinkedIn note**\n", "```text", d["linkedin_note"], "```",
                "**Follow-up (5–7 days later, once only)**\n", "```text", d["follow_up_draft"], "```"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    drafts = generate(read_csv(PROSPECTS_CSV).astype({"qualification_score": int}, errors="ignore"))
    OUTREACH.mkdir(exist_ok=True)
    drafts.to_csv(OUTREACH / "OUTREACH_QUEUE.csv", index=False, encoding="utf-8")
    (OUTREACH / "OUTREACH_DRAFTS.md").write_text(write_markdown(drafts), encoding="utf-8")
    print(f"{len(drafts)} drafts written (status: pending_review, not_sent)")
