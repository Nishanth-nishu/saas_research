"""FastAPI app: counsellor web UI, public inquiry form, lead API and WhatsApp webhook."""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import security
from .config import Settings, load_settings
from .db import SOURCES, STAGES, connect, init_db, iso, parse, utcnow
from .services import ai, followups, leads, messaging, metrics, orgs

log = logging.getLogger("leadpilot")
HERE = Path(__file__).resolve().parent
COOKIE = "lp_session"


class LoginRequired(Exception):
    pass


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    init_db(connect(settings.db_path))

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        task = asyncio.create_task(_scheduler(settings)) if settings.tick_seconds > 0 else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title="LeadPilot", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.settings = settings
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.globals.update(STAGES=STAGES, SOURCES=SOURCES)

    def db():
        return connect(settings.db_path)

    # ---------- helpers ----------
    def local(ts: str, tz: str = "Asia/Kolkata", fmt: str = "%d %b %H:%M") -> str:
        dt = parse(ts)
        return dt.astimezone(ZoneInfo(tz)).strftime(fmt) if dt else ""

    def ago(ts: str) -> str:
        dt = parse(ts)
        if not dt:
            return ""
        secs = (utcnow() - dt).total_seconds()
        future = secs < 0
        secs = abs(secs)
        txt = (f"{int(secs // 60)}m" if secs < 3600 else f"{int(secs // 3600)}h" if secs < 86400
               else f"{int(secs // 86400)}d")
        return f"in {txt}" if future else f"{txt} ago"

    templates.env.filters.update(local=local, ago=ago)

    def current(request: Request):
        token = request.cookies.get(COOKIE, "")
        uid = security.read_session(token, settings.secret_key) if token else None
        if uid is None:
            raise LoginRequired()
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE id = ? AND active = 1", (uid,)).fetchone()
        if user is None:
            raise LoginRequired()
        return conn, user, orgs.get_org(conn, user["org_id"]), token

    async def form_checked(request: Request, token: str) -> dict:
        form = await request.form()
        if not security.check_csrf(token, str(form.get("csrf", "")), settings.secret_key):
            raise HTTPException(403, "Invalid or missing CSRF token; reload the page and try again")
        return {k: v for k, v in form.items()}

    def render(request: Request, name: str, ctx: dict, status: int = 200):
        if "token" in ctx:
            ctx["csrf"] = security.csrf_token(ctx["token"], settings.secret_key)
        ctx.setdefault("flash", request.query_params.get("msg", ""))
        ctx.setdefault("error", request.query_params.get("err", ""))
        return templates.TemplateResponse(request, name, ctx, status_code=status)

    def back(url: str, msg: str = "", err: str = "") -> RedirectResponse:
        sep = "&" if "?" in url else "?"
        q = f"{sep}{urlencode({'msg': msg})}" if msg else (f"{sep}{urlencode({'err': err})}" if err else "")
        return RedirectResponse(url + q, status_code=303)

    def require_admin(user):
        if user["role"] != "admin":
            raise HTTPException(403, "Admins only")

    @app.exception_handler(LoginRequired)
    async def _login_redirect(request: Request, exc: LoginRequired):
        return RedirectResponse("/login", status_code=303)

    # ---------- auth ----------
    @app.get("/", include_in_schema=False)
    def home(request: Request):
        return RedirectResponse("/dashboard" if request.cookies.get(COOKIE) else "/login", status_code=303)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/signup", response_class=HTMLResponse)
    def signup_page(request: Request):
        return render(request, "signup.html", {})

    @app.post("/signup")
    async def signup(request: Request):
        f = await request.form()
        try:
            _, uid = orgs.create_org(db(), str(f.get("org_name", "")), str(f.get("name", "")),
                                     str(f.get("email", "")), str(f.get("password", "")))
        except ValueError as e:
            return render(request, "signup.html", {"error": str(e), "form": dict(f)}, 400)
        return _login_response(uid)

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        return render(request, "login.html", {})

    @app.post("/login")
    async def login(request: Request):
        f = await request.form()
        user = orgs.authenticate(db(), str(f.get("email", "")), str(f.get("password", "")))
        if user is None:
            return render(request, "login.html", {"error": "Wrong email or password", "email": f.get("email", "")}, 401)
        return _login_response(user["id"])

    def _login_response(uid: int) -> RedirectResponse:
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie(COOKIE, security.make_session(uid, settings.secret_key), httponly=True, samesite="lax",
                        secure=settings.base_url.startswith("https"), max_age=security.SESSION_MAX_AGE)
        return resp

    @app.post("/logout")
    def logout():
        resp = RedirectResponse("/login", status_code=303)
        resp.delete_cookie(COOKIE)
        return resp

    # ---------- dashboard ----------
    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        conn, user, org, token = current(request)
        now = utcnow()
        my_tasks = followups.open_tasks(conn, org["id"], user["id"], limit=10)
        return render(request, "dashboard.html", {"user": user, "org": org, "token": token,
                                                  "m": metrics.dashboard(conn, org["id"], now), "tasks": my_tasks,
                                                  "now": iso(now)})

    # ---------- leads ----------
    @app.get("/leads", response_class=HTMLResponse)
    def leads_page(request: Request, stage: str = "open", owner: str = "", source: str = "", q: str = ""):
        conn, user, org, token = current(request)
        rows = leads.search(conn, org["id"], stage, owner, source, q)
        return render(request, "leads.html", {"user": user, "org": org, "token": token, "leads": rows,
                                              "users": orgs.users(conn, org["id"]),
                                              "f": {"stage": stage, "owner": owner, "source": source, "q": q}})

    @app.post("/leads")
    async def add_lead(request: Request):
        conn, user, org, token = current(request)
        f = await form_checked(request, token)
        try:
            lead_id, created = leads.capture(conn, org["id"], f, "manual", utcnow(), user["id"])
        except ValueError as e:
            return back("/leads", err=str(e))
        return back(f"/leads/{lead_id}", msg="Lead added" if created else "Matched an existing lead; details merged")

    @app.post("/leads/import")
    async def import_leads(request: Request):
        conn, user, org, token = current(request)
        form = await request.form()
        if not security.check_csrf(token, str(form.get("csrf", "")), settings.secret_key):
            raise HTTPException(403, "Invalid CSRF token")
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            return back("/leads", err="Choose a CSV file")
        raw = await upload.read()
        if len(raw) > 5_000_000:
            return back("/leads", err="File too large (5 MB max)")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1252", errors="replace")
        try:
            r = leads.import_csv(conn, org["id"], text, utcnow(), user["id"])
        except ValueError as e:
            return back("/leads", err=str(e))
        msg = f"Imported: {r['created']} new, {r['merged']} merged, {len(r['errors'])} skipped"
        if r["errors"]:
            msg += " (" + "; ".join(r["errors"][:3]) + ")"
        return back("/leads", msg=msg)

    @app.get("/leads/{lead_id}", response_class=HTMLResponse)
    def lead_page(request: Request, lead_id: int):
        conn, user, org, token = current(request)
        lead = leads.get(conn, org["id"], lead_id)
        if lead is None:
            raise HTTPException(404, "Lead not found")
        owner = conn.execute("SELECT name FROM users WHERE id = ?", (lead["owner_id"],)).fetchone() if lead["owner_id"] else None
        tasks = conn.execute("SELECT * FROM tasks WHERE lead_id = ? AND done_at = '' ORDER BY due_at", (lead_id,)).fetchall()
        return render(request, "lead.html", {
            "user": user, "org": org, "token": token, "lead": lead, "owner": owner,
            "users": [u for u in orgs.users(conn, org["id"]) if u["active"]],
            "timeline": leads.timeline(conn, lead_id), "messages": messaging.for_lead(conn, lead_id),
            "tasks": tasks, "in_window": messaging.in_whatsapp_window(lead, utcnow()),
            "wa_live": bool(settings.wa_access_token and org["wa_phone_number_id"]),
            "ai_live": bool(settings.anthropic_key), "now": iso(utcnow())})

    def _lead_action(path: str):
        def deco(fn):
            async def handler(request: Request, lead_id: int):
                conn, user, org, token = current(request)
                f = await form_checked(request, token)
                try:
                    msg = fn(conn, user, org, lead_id, f) or "Saved"
                except (ValueError, LookupError) as e:
                    return back(f"/leads/{lead_id}", err=str(e))
                return back(f"/leads/{lead_id}", msg=msg)
            app.post(f"/leads/{{lead_id}}/{path}")(handler)
            return fn
        return deco

    @_lead_action("stage")
    def _stage(conn, user, org, lead_id, f):
        leads.set_stage(conn, org["id"], lead_id, f.get("stage", ""), utcnow(), user["id"], f.get("lost_reason", ""))
        return "Stage updated"

    @_lead_action("assign")
    def _assign(conn, user, org, lead_id, f):
        leads.reassign(conn, org["id"], lead_id, int(f.get("owner_id") or 0), utcnow(), user["id"])
        return "Reassigned"

    @_lead_action("contact")
    def _contact(conn, user, org, lead_id, f):
        kind = f.get("kind", "note")
        if kind not in ("call", "meeting", "note", "whatsapp", "email"):
            raise ValueError("Unknown activity type")
        leads.record_contact(conn, org["id"], lead_id, kind, f.get("body", "").strip() or kind, utcnow(), user["id"])
        return "Logged"

    @_lead_action("optout")
    def _optout(conn, user, org, lead_id, f):
        leads.opt_out(conn, org["id"], lead_id, utcnow(), user["id"])
        return "Marked do-not-contact"

    @_lead_action("task")
    def _task(conn, user, org, lead_id, f):
        hours = float(f.get("hours") or 0)
        now = utcnow()
        followups.add_task(conn, org["id"], lead_id, f.get("title", ""), now + timedelta(hours=hours), now, user["id"])
        return "Task added"

    @_lead_action("draft")
    def _draft(conn, user, org, lead_id, f):
        lead = leads.get(conn, org["id"], lead_id)
        if lead is None:
            raise LookupError("Lead not found")
        text, by = ai.draft(settings, lead, org["name"], messaging.for_lead(conn, lead_id), f.get("purpose", "follow_up"))
        channel = "whatsapp" if lead["phone"] else "email"
        messaging.create_draft(conn, org["id"], lead_id, channel, text, utcnow(), user["id"], drafted_by=by)
        return "Draft ready for review" + (" (template: AI not configured)" if by == "template" else "")

    @_lead_action("message")
    def _message(conn, user, org, lead_id, f):
        messaging.create_draft(conn, org["id"], lead_id, f.get("channel", "whatsapp"), f.get("body", ""), utcnow(), user["id"])
        return "Draft saved"

    # ---------- messages ----------
    @app.post("/messages/{msg_id}/{action}")
    async def message_action(request: Request, msg_id: int, action: str):
        conn, user, org, token = current(request)
        f = await form_checked(request, token)
        nxt = f.get("next", "/outbox")
        if not nxt.startswith("/"):
            nxt = "/outbox"
        try:
            if action == "send":
                if f.get("body"):
                    messaging.update_draft(conn, org["id"], msg_id, f["body"])
                status = messaging.send(conn, settings, org["id"], msg_id, utcnow(), user["id"])
                if status == "failed":
                    err = conn.execute("SELECT error FROM messages WHERE id = ?", (msg_id,)).fetchone()["error"]
                    return back(nxt, err=f"Not sent: {err}")
                return back(nxt, msg="Sent" if status == "sent" else "Dry run: recorded but NOT delivered (WhatsApp not connected)")
            if action == "update":
                messaging.update_draft(conn, org["id"], msg_id, f.get("body", ""))
                return back(nxt, msg="Draft updated")
            if action == "discard":
                messaging.discard(conn, org["id"], msg_id)
                return back(nxt, msg="Draft discarded")
        except LookupError as e:
            return back(nxt, err=str(e))
        raise HTTPException(404)

    @app.get("/outbox", response_class=HTMLResponse)
    def outbox(request: Request, mine: str = ""):
        conn, user, org, token = current(request)
        rows = messaging.drafts(conn, org["id"], user["id"] if mine else None)
        now = utcnow()
        return render(request, "outbox.html", {"user": user, "org": org, "token": token, "drafts": rows, "mine": mine,
                                               "window": {r["id"]: messaging.in_whatsapp_window(r, now) for r in rows},
                                               "wa_live": bool(settings.wa_access_token and org["wa_phone_number_id"])})

    # ---------- tasks ----------
    @app.get("/tasks", response_class=HTMLResponse)
    def tasks_page(request: Request, everyone: str = ""):
        conn, user, org, token = current(request)
        rows = followups.open_tasks(conn, org["id"], None if everyone else user["id"])
        return render(request, "tasks.html", {"user": user, "org": org, "token": token, "tasks": rows,
                                              "everyone": everyone, "now": iso(utcnow())})

    @app.post("/tasks/{task_id}/done")
    async def task_done(request: Request, task_id: int):
        conn, user, org, token = current(request)
        f = await form_checked(request, token)
        try:
            followups.complete_task(conn, org["id"], task_id, utcnow(), user["id"])
        except LookupError as e:
            return back("/tasks", err=str(e))
        nxt = f.get("next", "/tasks")
        return back(nxt if nxt.startswith("/") else "/tasks", msg="Task done")

    # ---------- settings ----------
    @app.get("/settings", response_class=HTMLResponse)
    def settings_page(request: Request):
        conn, user, org, token = current(request)
        require_admin(user)
        return render(request, "settings.html", {
            "user": user, "org": org, "token": token, "users": orgs.users(conn, org["id"]),
            "rules": orgs.rules(conn, org["id"]), "base_url": settings.base_url or str(request.base_url).rstrip("/"),
            "wa_token_set": bool(settings.wa_access_token), "ai_live": bool(settings.anthropic_key),
            "ai_model": settings.ai_model})

    @app.post("/settings/{section}")
    async def settings_post(request: Request, section: str):
        conn, user, org, token = current(request)
        require_admin(user)
        f = await form_checked(request, token)
        try:
            if section == "org":
                tz = f.get("timezone", "Asia/Kolkata")
                ZoneInfo(tz)  # raises on an unknown zone
                orgs.update_org(conn, org["id"], name=f.get("name", org["name"]).strip() or org["name"], timezone=tz,
                                wa_phone_number_id=f.get("wa_phone_number_id", "").strip(),
                                auto_send=1 if f.get("auto_send") else 0)
                msg = "Settings saved"
            elif section == "users":
                orgs.add_user(conn, org["id"], f.get("name", ""), f.get("email", ""), f.get("password", ""),
                              f.get("role", "counsellor"))
                msg = "Team member added"
            elif section == "toggle-user":
                uid = int(f.get("user_id") or 0)
                if uid == user["id"]:
                    raise ValueError("You can't deactivate yourself")
                target = conn.execute("SELECT active FROM users WHERE id = ? AND org_id = ?", (uid, org["id"])).fetchone()
                if target is None:
                    raise LookupError("User not found")
                orgs.set_user_active(conn, org["id"], uid, not target["active"])
                msg = "Team member updated"
            elif section == "rule":
                orgs.update_rule(conn, org["id"], int(f.get("rule_id") or 0), int(f.get("delay_minutes") or 0),
                                 bool(f.get("active")), f.get("template"))
                msg = "Rule saved"
            elif section == "rotate-key":
                orgs.rotate_api_key(conn, org["id"])
                msg = "New API key generated; update any website integration that used the old one"
            elif section == "run-engine":
                s = followups.run(conn, utcnow(), org["id"])
                msg = f"Engine ran: {s['tasks']} tasks, {s['drafts']} drafts created"
            else:
                raise HTTPException(404)
        except (ValueError, LookupError, KeyError) as e:
            return back("/settings", err=str(e) or "Invalid value")
        return back("/settings", msg=msg)

    # ---------- public inquiry form ----------
    @app.get("/f/{slug}", response_class=HTMLResponse)
    def public_form(request: Request, slug: str, embed: str = ""):
        org = orgs.org_by_slug(db(), slug)
        if org is None:
            raise HTTPException(404, "Form not found")
        return render(request, "public_form.html", {"org": org, "embed": embed})

    @app.post("/f/{slug}", response_class=HTMLResponse)
    async def public_submit(request: Request, slug: str):
        conn = db()
        org = orgs.org_by_slug(conn, slug)
        if org is None:
            raise HTTPException(404, "Form not found")
        f = dict(await request.form())
        embed = f.get("embed", "")
        # Redirect after POST so refreshing the thank-you page doesn't submit the inquiry again
        thanks = RedirectResponse(f"/f/{slug}/thanks" + ("?embed=1" if embed else ""), status_code=303)
        if f.get("website"):  # honeypot field humans never see
            return thanks
        if not f.get("consent"):
            return render(request, "public_form.html", {"org": org, "embed": embed, "form": f,
                                                        "error": "Please tick the consent box so we can contact you"}, 400)
        try:
            leads.capture(conn, org["id"], f, "web_form", utcnow())
        except ValueError as e:
            return render(request, "public_form.html", {"org": org, "embed": embed, "form": f, "error": str(e)}, 400)
        return thanks

    @app.get("/f/{slug}/thanks", response_class=HTMLResponse)
    def public_thanks(request: Request, slug: str, embed: str = ""):
        org = orgs.org_by_slug(db(), slug)
        if org is None:
            raise HTTPException(404, "Form not found")
        return render(request, "thanks.html", {"org": org, "embed": embed})

    # ---------- JSON API ----------
    @app.post("/api/v1/leads")
    async def api_create_lead(request: Request):
        conn = db()
        org = orgs.org_by_api_key(conn, request.headers.get("x-api-key", ""))
        if org is None:
            return JSONResponse({"error": "invalid API key"}, status_code=401)
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return JSONResponse({"error": "body must be JSON"}, status_code=400)
        if not isinstance(data, dict):
            return JSONResponse({"error": "body must be a JSON object"}, status_code=400)
        try:
            lead_id, created = leads.capture(conn, org["id"], data, "api", utcnow())
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=422)
        return JSONResponse({"lead_id": lead_id, "created": created}, status_code=201 if created else 200)

    # ---------- WhatsApp webhook ----------
    @app.get("/webhooks/whatsapp")
    def wa_verify(request: Request):
        p = request.query_params
        if (p.get("hub.mode") == "subscribe" and settings.wa_verify_token
                and p.get("hub.verify_token") == settings.wa_verify_token):
            return PlainTextResponse(p.get("hub.challenge", ""))
        return PlainTextResponse("forbidden", status_code=403)

    @app.post("/webhooks/whatsapp")
    async def wa_inbound(request: Request):
        body = await request.body()
        if settings.wa_app_secret and not security.verify_meta_signature(
                body, request.headers.get("x-hub-signature-256", ""), settings.wa_app_secret):
            return PlainTextResponse("bad signature", status_code=401)
        if not settings.wa_app_secret:
            log.warning("WA_APP_SECRET not set: webhook signatures are NOT being verified")
        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            return PlainTextResponse("bad json", status_code=400)
        conn = db()
        for m in messaging.parse_whatsapp_webhook(payload):
            org = orgs.org_by_wa_number(conn, m["phone_number_id"])
            if org is None:
                log.warning("Inbound WhatsApp for unknown phone_number_id %s", m["phone_number_id"])
                continue
            try:
                messaging.record_inbound(conn, org["id"], m["from"], m["name"], m["text"], utcnow(), m["id"])
            except ValueError as e:
                log.warning("Inbound message skipped: %s", e)
        return Response(status_code=200)  # Meta retries on anything else

    return app


async def _scheduler(settings: Settings) -> None:
    """Run the follow-up engine every tick in a worker thread with its own connection."""
    def tick():
        conn = connect(settings.db_path)
        now = utcnow()
        stats = followups.run(conn, now)
        stats["auto_sent"] = messaging.auto_send_due(conn, settings, now)
        conn.close()
        return stats

    while True:
        try:
            stats = await asyncio.to_thread(tick)
            if stats["tasks"] or stats["drafts"]:
                log.info("Follow-up engine: %s", stats)
        except Exception:
            log.exception("Follow-up engine failed")
        await asyncio.sleep(settings.tick_seconds)
