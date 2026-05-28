"""Flask app: ROI calculator + per-lead trackable links."""
from __future__ import annotations

import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Any

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

import db as link_db


BASE = os.path.dirname(os.path.abspath(__file__))

ALLOWED_FILES = {
    "WECHIP_Configurateur_Client.html",
    "wechip-tokens.css",
    "favicon.ico",
}
ALLOWED_DIR_PREFIXES = ("assets/", "fonts/")

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,59}$")
HTML_PLACEHOLDER = "__WECHIP_LINK_CONFIG__"

CONFIG_KEYS = (
    "pricePerModule",
    "revPerColDay",
    "wechipSharePct",
    "opexAssumptions",
    "discountPct",
    "columns",
)


def _load_html(base: str) -> str:
    with open(os.path.join(base, "WECHIP_Configurateur_Client.html"), encoding="utf-8") as f:
        return f.read()


def _render_calculator(html: str, link_config: dict[str, Any], display_name: str = "") -> str:
    payload = dict(link_config or {})
    if display_name:
        payload["display_name"] = display_name
    safe = json.dumps(payload).replace("</", "<\\/")
    return html.replace(HTML_PLACEHOLDER, safe, 1)


_RATE_BUCKETS: dict[tuple[str, str], deque] = defaultdict(deque)
RATE_LIMIT_PER_MIN = 60


def _rate_limit_ok(key: tuple[str, str], window: float = 60.0, limit: int = RATE_LIMIT_PER_MIN) -> bool:
    bucket = _RATE_BUCKETS[key]
    now = time.monotonic()
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def _auth_credentials() -> tuple[str | None, str | None]:
    return os.environ.get("BASIC_AUTH_USER"), os.environ.get("BASIC_AUTH_PASS")


def _check_basic_auth() -> bool:
    user, pwd = _auth_credentials()
    auth = request.authorization
    if not auth or auth.type != "basic":
        return False
    return (
        hmac.compare_digest((auth.username or ""), user or "")
        and hmac.compare_digest((auth.password or ""), pwd or "")
    )


def _unauthorized() -> Response:
    return Response(
        "Authentication required",
        status=401,
        headers={"WWW-Authenticate": 'Basic realm="roi-admin"'},
    )


def basic_auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user, pwd = _auth_credentials()
        if not user or not pwd:
            return Response("Admin disabled: BASIC_AUTH_USER/BASIC_AUTH_PASS not set", status=503)
        if not _check_basic_auth():
            return _unauthorized()
        return view(*args, **kwargs)
    return wrapper


def _csrf_token() -> str:
    tok = session.get("_csrf")
    if not tok:
        tok = secrets.token_urlsafe(32)
        session["_csrf"] = tok
    return tok


def _csrf_ok() -> bool:
    sent = request.form.get("_csrf", "")
    expected = session.get("_csrf", "")
    return bool(expected) and hmac.compare_digest(sent, expected)


def _parse_config_from_form(form) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    cfg: dict[str, Any] = {}

    def _num(name: str, lo: float | None = None, hi: float | None = None) -> float | None:
        raw = (form.get(name) or "").strip()
        if not raw:
            return None
        try:
            v = float(raw)
        except ValueError:
            errors.append(f"{name}: not a number")
            return None
        if lo is not None and v < lo:
            errors.append(f"{name}: must be >= {lo}")
            return None
        if hi is not None and v > hi:
            errors.append(f"{name}: must be <= {hi}")
            return None
        return v

    v = _num("pricePerModule", lo=0)
    if v is not None: cfg["pricePerModule"] = v
    v = _num("revPerColDay", lo=0)
    if v is not None: cfg["revPerColDay"] = v
    v = _num("wechipSharePct", lo=0, hi=100)
    if v is not None: cfg["wechipSharePct"] = v
    v = _num("discountPct", lo=0, hi=95)
    if v is not None: cfg["discountPct"] = v
    v = _num("columns", lo=4, hi=16)
    if v is not None: cfg["columns"] = int(v)

    raw_opex = (form.get("opexAssumptionsJson") or "").strip()
    if raw_opex:
        try:
            parsed = json.loads(raw_opex)
            if not isinstance(parsed, dict):
                errors.append("opexAssumptions: must be a JSON object")
            else:
                cfg["opexAssumptions"] = parsed
        except json.JSONDecodeError as e:
            errors.append(f"opexAssumptions: invalid JSON ({e})")

    return cfg, errors


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["LINKS_DB_PATH"] = db_path or os.environ.get("LINKS_DB_PATH", os.path.join(BASE, "roi_links.db"))
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

    link_db.init_db(app.config["LINKS_DB_PATH"])

    cached_html: dict[str, str] = {}

    def html() -> str:
        if app.debug or app.testing or not cached_html:
            cached_html["v"] = _load_html(BASE)
        return cached_html["v"]

    def dbp() -> str:
        return app.config["LINKS_DB_PATH"]

    @app.route("/")
    def index() -> Response:
        return Response(_render_calculator(html(), {}), mimetype="text/html")

    @app.route("/c/<slug>")
    def customer_link(slug: str) -> Response:
        if not SLUG_RE.match(slug):
            abort(404)
        link = link_db.get_link(slug, dbp())
        if not link or link.get("revoked_at"):
            abort(404)
        try:
            link_db.log_event(slug, "view", {"ip": request.remote_addr or ""}, dbp())
        except sqlite3.Error:
            pass
        body = _render_calculator(html(), link["config"], display_name=link.get("display_name", ""))
        return Response(body, mimetype="text/html")

    @app.route("/c/<slug>/event", methods=["POST"])
    def customer_event(slug: str) -> Response:
        if not SLUG_RE.match(slug):
            abort(404)
        link = link_db.get_link(slug, dbp())
        if not link or link.get("revoked_at"):
            abort(404)
        ip = request.remote_addr or ""
        if not _rate_limit_ok((slug, ip)):
            return Response("", status=429)
        data = request.get_json(silent=True) or {}
        t = data.get("type")
        if t not in ("change", "print"):
            return Response("", status=400)
        payload = data.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {"value": str(payload)[:200]}
        try:
            link_db.log_event(slug, t, payload, dbp())
        except sqlite3.Error:
            pass
        return Response("", status=204)

    @app.route("/<path:filename>")
    def static_files(filename: str):
        if filename in ALLOWED_FILES or filename.startswith(ALLOWED_DIR_PREFIXES):
            return send_from_directory(BASE, filename)
        abort(404)

    @app.context_processor
    def _ctx():
        return {"csrf_token": _csrf_token}

    @app.route("/admin/links")
    @basic_auth_required
    def admin_list():
        return render_template("admin_list.html", links=link_db.list_links(dbp()))

    @app.route("/admin/links/new", methods=["GET", "POST"])
    @basic_auth_required
    def admin_new():
        if request.method == "POST":
            if not _csrf_ok():
                return Response("CSRF failed", status=400)
            slug = (request.form.get("slug") or "").strip().lower()
            display_name = (request.form.get("display_name") or "").strip()
            errors: list[str] = []
            if not SLUG_RE.match(slug):
                errors.append("slug: invalid (use a-z, 0-9, hyphen; 2-60 chars; start alphanum)")
            cfg, cfg_errors = _parse_config_from_form(request.form)
            errors.extend(cfg_errors)
            if not errors:
                try:
                    link_db.create_link(slug, display_name, cfg, dbp())
                    return redirect(url_for("admin_list"))
                except sqlite3.IntegrityError:
                    errors.append("slug: already exists")
            return render_template("admin_form.html", mode="new", link=None,
                                   form=request.form, errors=errors)
        return render_template("admin_form.html", mode="new", link=None, form={}, errors=[])

    @app.route("/admin/links/<slug>", methods=["GET", "POST"])
    @basic_auth_required
    def admin_edit(slug: str):
        link = link_db.get_link(slug, dbp())
        if not link:
            abort(404)
        if request.method == "POST":
            if not _csrf_ok():
                return Response("CSRF failed", status=400)
            display_name = (request.form.get("display_name") or "").strip()
            cfg, errors = _parse_config_from_form(request.form)
            if errors:
                return render_template("admin_form.html", mode="edit", link=link,
                                       form=request.form, errors=errors)
            link_db.update_link(slug, display_name, cfg, dbp())
            return redirect(url_for("admin_list"))
        form_prefill = {
            "display_name": link.get("display_name", ""),
            **{k: link["config"].get(k, "") for k in CONFIG_KEYS if k != "opexAssumptions"},
            "opexAssumptionsJson": json.dumps(link["config"].get("opexAssumptions"))
                if link["config"].get("opexAssumptions") else "",
        }
        return render_template("admin_form.html", mode="edit", link=link,
                               form=form_prefill, errors=[])

    @app.route("/admin/links/<slug>/revoke", methods=["POST"])
    @basic_auth_required
    def admin_revoke(slug: str):
        if not _csrf_ok():
            return Response("CSRF failed", status=400)
        link_db.revoke_link(slug, dbp())
        return redirect(url_for("admin_list"))

    @app.route("/admin/links/<slug>/stats")
    @basic_auth_required
    def admin_stats(slug: str):
        link = link_db.get_link(slug, dbp())
        if not link:
            abort(404)
        events = link_db.list_events(slug, 200, dbp())
        return render_template("admin_stats.html", link=link, events=events)

    @app.after_request
    def add_security_headers(resp: Response) -> Response:
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'",
        )
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5051)), debug=False)
