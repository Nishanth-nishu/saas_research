"""Tailored outreach bot: research each prospect's site, pick the matching service, draft a personal email and a
one-page demo sketch, and send ONLY what a human has approved.

Free stack: public websites (httpx), templates, optional local model via Ollama, Gmail SMTP.

  python src/outreach_bot.py draft --limit 10      # research + tailor -> data/bot_queue.csv (pending_review)
  python src/outreach_bot.py list                  # show the queue
  python src/outreach_bot.py approve P-XXXX ...    # after YOU have read and edited the draft
  python src/outreach_bot.py send                  # dry run: shows what would go out
  python src/outreach_bot.py send --send           # really sends approved rows (daily cap, paced)
  python src/outreach_bot.py mark P-XXXX replied   # replied | not_interested | bounced
  python src/outreach_bot.py optout someone@x.com  # never email this address again
  python src/outreach_bot.py followups             # one follow-up draft per silent prospect after 6 days

Rules enforced here (see outreach/OUTREACH_POLICY.md): only published business emails already in
prospects.csv, never guessed; nothing is sent unless status = approved; at most DAILY_CAP sends per IST day,
spaced minutes apart; one follow-up at most; every email names the sender and has an opt-out line and a
List-Unsubscribe header; opt-outs are permanent.

Environment: SENDER_NAME, SENDER_EMAIL (Gmail address), GMAIL_APP_PASSWORD (Google account -> Security ->
App passwords; never commit it), SENDER_SITE, SENDER_CITY, OLLAMA_MODEL (optional, e.g. "llama3.2").
"""
from __future__ import annotations

import argparse
import csv
import html
import os
import random
import re
import smtplib
import sys
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import httpx

from common import DATA, PROSPECTS_CSV, read_csv

QUEUE = DATA / "bot_queue.csv"
SUPPRESSION = DATA / "suppression.csv"
DEMOS = DATA / "demos"
IST = timezone(timedelta(hours=5, minutes=30))
DAILY_CAP = int(os.environ.get("BOT_DAILY_CAP", "20"))
HARD_CAP = 30  # never more than this per day, whatever the env says
USER_AGENT = "Mozilla/5.0 (compatible; outreach-research/1.0; one-page visit)"
QUEUE_FIELDS = ["prospect_id", "company", "to_email", "email_source", "kind", "service", "signals", "subject",
                "body", "demo_file", "status", "created_utc", "sent_utc", "sent_ist", "notes"]

SENDER = os.environ.get("SENDER_NAME", "Nishanth R")
SITE = os.environ.get("SENDER_SITE", "[your website]")
CITY = os.environ.get("SENDER_CITY", "Hyderabad, India")

# ---------- services ----------
SERVICES = {
    "followup": {
        "name": "Enquiry follow-up autopilot",
        "pain": "enquiries from forms, WhatsApp and ads slipping through between counsellors",
        "demo": "every enquiry landing in one list, assigned to a counsellor, with demo-class reminders and "
                "day 1/3/7 follow-ups drafted for review",
        "question": "How do new enquiries reach your counsellors today, and how do you know who has followed up?",
        "steps": ["Enquiry arrives ({channels})", "Instant acknowledgement + counsellor assigned",
                  "Free demo class booked, reminders the day before and 2 hours before",
                  "Day 1/3/7 follow-ups drafted for the counsellor to send", "Owner sees untouched leads and show-ups daily"],
    },
    "extraction": {
        "name": "Document data extraction",
        "pain": "re-typing invoices, POs and shipping documents into {tools}",
        "demo": "a document going in and a pre-filled, checkable entry coming out for {tools}",
        "question": "Roughly how many documents does your team key in per week, and which ones take longest?",
        "steps": ["Document arrives (email, PDF, scan)", "Fields read: party, GSTIN, items, quantities, totals",
                  "Mismatches flagged (totals, GSTIN, quantities)", "Your team checks the pre-filled entry",
                  "Entry exported for {tools}"],
    },
    "reporting": {
        "name": "Automated client reporting",
        "pain": "assembling monthly client reports by hand from {tools}",
        "demo": "one of your report formats filled automatically, with draft commentary your team edits",
        "question": "How many hours a month go into client reports, and which part is most manual?",
        "steps": ["Numbers pulled from {tools}", "Your report template filled for each client",
                  "Commentary drafted for the account manager", "Edited and sent on schedule"],
    },
    "support": {
        "name": "Support & knowledge assistant",
        "pain": "the same questions (order status, returns, how-to) answered by hand every day",
        "demo": "an assistant answering from your own FAQs and policies, with citations, drafting replies in {tools}",
        "question": "What share of your tickets are repeat questions, and how are they handled today?",
        "steps": ["Question arrives ({channels})", "Answer found in your own docs, with the source cited",
                  "Draft reply prepared in {tools}", "Agent approves or edits before it is sent"],
    },
}
SEGMENT_SERVICE = {"A_education": "followup", "B_documents_logistics": "extraction",
                   "C_agency_b2b_services": "reporting", "D_saas_ecommerce": "support"}
SEGMENT_PHRASE = {"A_education": "coaching and study-abroad firms", "B_documents_logistics": "distributors and logistics firms",
                  "C_agency_b2b_services": "marketing agencies", "D_saas_ecommerce": "online brands"}

CHANNEL_PATTERNS = {
    "WhatsApp": r"wa\.me/|api\.whatsapp\.com|whatsapp",
    "web forms": r"<form\b",
    "live chat": r"tawk\.to|crisp\.chat|intercom|freshchat|zoho.*salesiq|livechat|tidio",
    "phone calls": r"tel:",
}
TOOL_PATTERNS = {
    "Tally": r"\btally\b", "Zoho": r"\bzoho\b", "Shopify": r"shopify", "Freshdesk": r"freshdesk",
    "Google Analytics": r"googletagmanager|google-analytics|gtag\(", "Meta ads": r"connect\.facebook\.net|fbq\(",
    "HubSpot": r"hubspot", "WordPress": r"wp-content",
}
TOPIC_PATTERNS = {
    "IELTS": r"\bielts\b", "PTE": r"\bpte\b", "study abroad": r"study abroad|overseas education",
    "demo class": r"demo class|free demo", "invoices": r"\binvoic", "customs": r"customs|clearing",
    "returns": r"return|exchange|refund", "reporting": r"report",
}


# ---------- research ----------
def allowed_by_robots(url: str, client: httpx.Client) -> bool:
    parts = urlparse(url)
    rp = robotparser.RobotFileParser()
    try:
        r = client.get(f"{parts.scheme}://{parts.netloc}/robots.txt")
        rp.parse(r.text.splitlines() if r.status_code == 200 else [])
    except httpx.HTTPError:
        return True  # unreachable robots.txt: treat as no restrictions, as crawlers do
    return rp.can_fetch(USER_AGENT, url)


def fetch_home(url: str, client: httpx.Client | None = None) -> str:
    """One polite GET of the public homepage. Returns '' when blocked or unreachable."""
    if not url:
        return ""
    own = client is None
    client = client or httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    try:
        if not allowed_by_robots(url, client):
            return ""
        r = client.get(url)
        return r.text if r.status_code == 200 and "html" in r.headers.get("content-type", "") else ""
    except httpx.HTTPError:
        return ""
    finally:
        if own:
            client.close()


def extract_signals(page: str) -> dict:
    low = page.lower()
    found = lambda pats: [k for k, p in pats.items() if re.search(p, low)]  # noqa: E731
    title = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    return {"channels": found(CHANNEL_PATTERNS), "tools": found(TOOL_PATTERNS), "topics": found(TOPIC_PATTERNS),
            "title": html.unescape(re.sub(r"\s+", " ", title.group(1))).strip()[:120] if title else ""}


# ---------- tailoring ----------
def choose_service(prospect: dict, signals: dict) -> str:
    topics = set(signals.get("topics", []))
    if topics & {"IELTS", "PTE", "study abroad", "demo class"}:
        return "followup"
    if topics & {"invoices", "customs"} and prospect.get("segment") == "B_documents_logistics":
        return "extraction"
    return SEGMENT_SERVICE.get(prospect.get("segment", ""), "support")


def _join(items: list[str], default: str) -> str:
    items = [i for i in items if i]
    if not items:
        return default
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _fill(text: str, signals: dict, service: str) -> str:
    default_tools = {"extraction": "Tally or your ERP", "reporting": "your ad and analytics platforms",
                     "support": "your help desk", "followup": "your CRM or sheet"}[service]
    # an agency's own site analytics says nothing about its clients' platforms, so reporting keeps the default
    tools = [] if service == "reporting" else \
        [t for t in signals.get("tools", []) if t not in ("WordPress", "Google Analytics", "Meta ads")]
    return text.format(channels=_join(signals.get("channels", []), "forms, WhatsApp and calls"),
                       tools=_join(tools, default_tools))


def observed_line(prospect: dict, signals: dict, service: str) -> str:
    """What we actually saw on their public site, stated as an observation, never as a claim about their problems."""
    ch = [c for c in signals.get("channels", []) if c != "phone calls"]
    if service == "followup" and len(ch) >= 2:
        return f"I noticed students can reach {prospect['company_name']} through {_join(ch, '')} on your website."
    if service == "followup" and {"IELTS", "PTE"} & set(signals.get("topics", [])):
        return f"I saw that {prospect['company_name']} runs {_join([t for t in ('IELTS', 'PTE') if t in signals['topics']], '')} coaching."
    return f"I came across {prospect['company_name']} while looking at {SEGMENT_PHRASE.get(prospect.get('segment', ''), 'firms in your space')}."


def ollama_opening(prospect: dict, signals: dict) -> str:
    """Optional free local model. Returns '' unless it produces a short, claim-free sentence."""
    model = os.environ.get("OLLAMA_MODEL")
    if not model:
        return ""
    prompt = (f"Write ONE friendly sentence (max 25 words) opening a cold email to {prospect['company_name']}, "
              f"whose website title is '{signals.get('title', '')}'. Mention only what the title says. "
              "No numbers, no compliments about results, no claims about their problems. Output only the sentence.")
    try:
        r = httpx.post("http://localhost:11434/api/generate", json={"model": model, "prompt": prompt, "stream": False},
                       timeout=60)
        line = r.json().get("response", "").strip().strip('"').split("\n")[0]
    except (httpx.HTTPError, ValueError):
        return ""
    bad = re.search(r"\d|guarantee|we have helped|clients like|proven|best in", line, re.I)
    return "" if bad or not (20 <= len(line) <= 200) else line


def greeting(prospect: dict) -> str:
    name = (prospect.get("decision_maker_name") or "").split(";")[0].strip()
    return f"Hi {name.split()[0]}," if name else "Hello,"


def footer(to_email: str) -> str:
    return (f"\n--\n{SENDER} · AI Automation Studio · {CITY}\n{SITE}\n"
            f"You are receiving this because {to_email} is listed as a business contact on your website. "
            "Reply \"stop\" and I won't write again.")


def build_email(prospect: dict, signals: dict, service: str) -> tuple[str, str]:
    s = SERVICES[service]
    opening = ollama_opening(prospect, signals) or observed_line(prospect, signals, service)
    topic = {"followup": "student enquiries", "extraction": "document data entry", "reporting": "client reporting",
             "support": "repeat customer questions"}[service]
    subject = f"Quick question about {topic} at {prospect['company_name']}"
    body = (f"{greeting(prospect)}\n\n{opening}\n\n"
            f"I'm {SENDER}, an AI engineer in {CITY.split(',')[0]} (MS CS, IIIT Hyderabad). I build small automations for "
            f"one workflow at a time. A common one in your space is {_fill(s['pain'], signals, service)}.\n\n"
            f"{s['question']}\n\n"
            f"If it's relevant, I can put together a short demo for {prospect['company_name']} showing "
            f"{_fill(s['demo'], signals, service)}, free, and you decide afterwards whether it's worth building. "
            f"Would a 15-minute call this week or next work?\n\nThanks,\n{SENDER}")
    return subject[:120], body


def build_demo_page(prospect: dict, signals: dict, service: str) -> str:
    s = SERVICES[service]
    steps = "".join(f"<li>{html.escape(_fill(st, signals, service))}</li>" for st in s["steps"])
    seen = ", ".join(signals.get("channels", []) + signals.get("tools", [])) or "nothing specific"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(s['name'])} sketch</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;color:#1d1d1f;background:#fff}}
h1{{font-size:26px}}.note{{color:#666;font-size:14px;border-left:3px solid #0f5c4d;padding-left:12px}}li{{margin:8px 0}}</style></head>
<body><h1>{html.escape(s['name'])}: a sketch for {html.escape(prospect['company_name'])}</h1>
<p class="note">Illustrative mock-up prepared by {html.escape(SENDER)} from your public website only. It is not
based on any internal information, and it would be adjusted after a short call.</p>
<h2>How it could work</h2><ol>{steps}</ol>
<h2>What it runs on</h2><p>Your existing tools. Public signals seen on your site: {html.escape(seen)}.</p>
<h2>Next step</h2><p>A 15-minute call to see how this workflow runs today, then a working demo on sample data.
Free. You decide afterwards whether to run a fixed-price pilot.</p>
<p>{html.escape(SENDER)} · {html.escape(SITE)}</p></body></html>"""


# ---------- queue ----------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def stamp(dt: datetime) -> tuple[str, str]:
    return dt.strftime("%Y-%m-%d %H:%M UTC"), dt.astimezone(IST).strftime("%Y-%m-%d %H:%M IST")


def load_queue() -> list[dict]:
    if not QUEUE.exists():
        return []
    with QUEUE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_queue(rows: list[dict]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=QUEUE_FIELDS)
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in QUEUE_FIELDS} for r in rows])


def suppressed() -> set[str]:
    if not SUPPRESSION.exists():
        return set()
    return {line.strip().lower() for line in SUPPRESSION.read_text(encoding="utf-8").splitlines() if "@" in line}


def eligible(prospects: list[dict], queue: list[dict]) -> list[dict]:
    done = {r["prospect_id"] for r in queue}
    block = suppressed()
    rows = [p for p in prospects
            if p.get("public_email") and p.get("prospect_id") not in done
            and p.get("contact_channel_type") == "verified_public_business_contact"
            and p.get("outreach_status", "not_contacted") == "not_contacted"
            and p["public_email"].split(";")[0].strip().lower() not in block]
    return sorted(rows, key=lambda p: -int(p.get("qualification_score") or 0))


def draft(limit: int, fetch=fetch_home) -> list[dict]:
    queue = load_queue()
    prospects = read_csv(PROSPECTS_CSV).to_dict("records")
    made = []
    for p in eligible(prospects, queue)[:limit]:
        signals = extract_signals(fetch(p.get("website", "")))
        service = choose_service(p, signals)
        subject, body = build_email(p, signals, service)
        DEMOS.mkdir(parents=True, exist_ok=True)
        demo = DEMOS / f"{p['prospect_id']}.html"
        demo.write_text(build_demo_page(p, signals, service), encoding="utf-8")
        to = p["public_email"].split(";")[0].strip()
        row = {"prospect_id": p["prospect_id"], "company": p["company_name"], "to_email": to,
               "email_source": p.get("public_email_source", ""), "kind": "initial", "service": service,
               "signals": "; ".join(signals["channels"] + signals["tools"] + signals["topics"]) or "site unreachable",
               "subject": subject, "body": body, "demo_file": str(demo.relative_to(DATA.parent)),
               "status": "pending_review", "created_utc": stamp(now_utc())[0]}
        queue.append(row)
        made.append(row)
        print(f"drafted {p['prospect_id']} {p['company_name']} -> {SERVICES[service]['name']}")
    save_queue(queue)
    return made


OUTCOME_TO_PROSPECT = {"replied": "replied", "not_interested": "do_not_contact", "bounced": "do_not_contact"}


def set_status(ids: list[str], status: str) -> int:
    """approve: pending drafts only. Outcomes: sent rows get the outcome, unsent drafts are cancelled."""
    queue = load_queue()
    n = 0
    for r in queue:
        if r["prospect_id"] not in ids:
            continue
        if status == "approved":
            if r["status"] == "pending_review":
                r["status"] = "approved"
                n += 1
        elif r["status"] == "sent":
            r["status"] = status
            n += 1
        elif r["status"] in ("pending_review", "approved"):
            r["status"] = "cancelled"
    save_queue(queue)
    if status in ("not_interested", "bounced"):
        add_suppression([r["to_email"] for r in queue if r["prospect_id"] in ids])
    if status in OUTCOME_TO_PROSPECT:
        df = read_csv(PROSPECTS_CSV)
        df.loc[df["prospect_id"].isin(ids), "outreach_status"] = OUTCOME_TO_PROSPECT[status]
        df.to_csv(PROSPECTS_CSV, index=False)
    return n


def add_suppression(emails: list[str]) -> None:
    have = suppressed()
    with SUPPRESSION.open("a", encoding="utf-8") as f:
        for e in emails:
            if e.lower() not in have:
                f.write(e.lower() + "\n")


def followups(days: int = 6) -> list[dict]:
    queue = load_queue()
    by_id: dict[str, list[dict]] = {}
    for r in queue:
        by_id.setdefault(r["prospect_id"], []).append(r)
    made = []
    cutoff = now_utc() - timedelta(days=days)
    for pid, rows in by_id.items():
        first = next((r for r in rows if r["kind"] == "initial"), None)
        # only still-silent prospects: a reply, opt-out or bounce changes the status away from "sent"
        if not first or first["status"] != "sent" or any(r["kind"] == "followup" for r in rows):
            continue
        if datetime.strptime(first["sent_utc"], "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc) > cutoff:
            continue
        body = (f"{first['body'].split(chr(10))[0]}\n\nJust following up on my note last week. If "
                f"{SERVICES[first['service']]['name'].lower()} isn't a priority right now, no problem, and I won't "
                f"follow up again.\n\nThanks,\n{SENDER}")
        row = dict(first, kind="followup", subject="Re: " + first["subject"], body=body, status="pending_review",
                   created_utc=stamp(now_utc())[0], sent_utc="", sent_ist="", notes="")
        queue.append(row)
        made.append(row)
    save_queue(queue)
    return made


# ---------- sending ----------
def sent_today(queue: list[dict], now: datetime) -> int:
    today = now.astimezone(IST).strftime("%Y-%m-%d")
    return sum(1 for r in queue if r["status"] == "sent" and r["sent_ist"].startswith(today))


def make_message(row: dict, sender_email: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = f"{SENDER} <{sender_email}>"
    msg["To"] = row["to_email"]
    msg["Subject"] = row["subject"]
    msg["List-Unsubscribe"] = f"<mailto:{sender_email}?subject=stop>"
    msg.set_content(row["body"] + "\n" + footer(row["to_email"]))
    return msg


def send(really: bool, smtp_factory=None, sleep=time.sleep) -> list[dict]:
    queue = load_queue()
    block = suppressed()
    cap = min(DAILY_CAP, HARD_CAP)
    room = max(0, cap - sent_today(queue, now_utc()))
    todo = [r for r in queue if r["status"] == "approved" and r["to_email"].lower() not in block][:room]
    if not todo:
        print(f"Nothing to send (approved rows: {sum(r['status'] == 'approved' for r in queue)}, room today: {room}).")
        return []
    sender_email = os.environ.get("SENDER_EMAIL", "")
    if not really:
        for r in todo:
            print(f"[dry run] would send to {r['to_email']}: {r['subject']}")
        print(f"{len(todo)} approved. Re-run with --send to send them, about 2-4 minutes apart.")
        return todo
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not sender_email or not password:
        sys.exit("Set SENDER_EMAIL and GMAIL_APP_PASSWORD environment variables first.")
    smtp = (smtp_factory or (lambda: smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)))()
    smtp.login(sender_email, password)
    sent = []
    try:
        for i, r in enumerate(todo):
            if i:
                sleep(random.uniform(120, 240))  # a person's pace, and well inside Gmail's limits
            try:
                smtp.send_message(make_message(r, sender_email))
            except smtplib.SMTPException as e:
                r["status"], r["notes"] = "failed", str(e)[:200]
                save_queue(queue)
                continue
            r["status"] = "sent"
            r["sent_utc"], r["sent_ist"] = stamp(now_utc())
            save_queue(queue)  # save after each send so a crash never causes a double send
            mark_contacted(r["prospect_id"], r["sent_utc"])
            sent.append(r)
            print(f"sent {r['prospect_id']} {r['to_email']} at {r['sent_utc']} / {r['sent_ist']}")
    finally:
        smtp.quit()
    return sent


def mark_contacted(prospect_id: str, when: str) -> None:
    """Contact really happened: record it in prospects.csv (policy: only after an actual send)."""
    df = read_csv(PROSPECTS_CSV)
    hit = df["prospect_id"] == prospect_id
    if hit.any():
        df.loc[hit, "outreach_status"] = "contacted"
        df.loc[hit, "next_action"] = f"Emailed {when}; follow-up draft after 6 days if no reply"
        df.to_csv(PROSPECTS_CSV, index=False)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft"); d.add_argument("--limit", type=int, default=10)  # noqa: E702
    sub.add_parser("list")
    a = sub.add_parser("approve"); a.add_argument("ids", nargs="+")  # noqa: E702
    s = sub.add_parser("send"); s.add_argument("--send", action="store_true")  # noqa: E702
    m = sub.add_parser("mark"); m.add_argument("id"); m.add_argument("status", choices=["replied", "not_interested", "bounced"])  # noqa: E702
    o = sub.add_parser("optout"); o.add_argument("emails", nargs="+")  # noqa: E702
    sub.add_parser("followups")
    args = ap.parse_args(argv)
    if args.cmd == "draft":
        print(f"{len(draft(args.limit))} drafts added to {QUEUE}. Read and edit them, then approve.")
    elif args.cmd == "list":
        for r in load_queue():
            print(f"{r['prospect_id']:12} {r['kind']:8} {r['status']:15} {r['service']:10} {r['to_email']:32} {r['company']}")
    elif args.cmd == "approve":
        print(f"{set_status(args.ids, 'approved')} row(s) approved.")
    elif args.cmd == "send":
        send(args.send)
    elif args.cmd == "mark":
        print(f"{set_status([args.id], args.status)} row(s) marked {args.status}.")
    elif args.cmd == "optout":
        add_suppression(args.emails)
        print("Added to suppression list.")
    elif args.cmd == "followups":
        print(f"{len(followups())} follow-up draft(s) added for review.")


if __name__ == "__main__":
    main()
