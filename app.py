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
    "priceBase",
    "revPerColDay",
    "wechipSharePct",
    "opexAssumptions",
    "opexByWechip",
    "sharingFromStart",
    "discountPct",
    "columns",
)

ALLOWED_MODELS = ("auto", "filaire", "solaire")


def _coerce_model(value: Any) -> str:
    if isinstance(value, str) and value in ALLOWED_MODELS:
        return value
    return "auto"


def _load_html(base: str) -> str:
    with open(os.path.join(base, "WECHIP_Configurateur_Client.html"), encoding="utf-8") as f:
        return f.read()


def _render_calculator(
    html: str,
    link_config: dict[str, Any],
    display_name: str = "",
    admin_mode: bool = False,
    admin_slug: str | None = None,
) -> str:
    payload = dict(link_config or {})
    if display_name:
        payload["display_name"] = display_name
    if admin_mode:
        payload["__admin"] = True
        if admin_slug:
            payload["__editing_slug"] = admin_slug
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
    # Compare as bytes — compare_digest raises TypeError on non-ASCII str,
    # and browsers may submit credentials containing arbitrary bytes.
    def _eq(a: str | None, b: str | None) -> bool:
        return hmac.compare_digest((a or "").encode("utf-8"), (b or "").encode("utf-8"))
    return _eq(auth.username, user) and _eq(auth.password, pwd)


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
    return bool(expected) and hmac.compare_digest(
        sent.encode("utf-8"), expected.encode("utf-8")
    )


def _validate_config(cfg: dict[str, Any]) -> list[str]:
    """Validate a JSON config dict from the admin UI. Returns error list."""
    errors: list[str] = []

    def _check_num(key: str, lo: float | None = None, hi: float | None = None) -> None:
        if key not in cfg:
            return
        v = cfg[key]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            errors.append(f"{key}: not a number")
            return
        if lo is not None and v < lo:
            errors.append(f"{key}: must be >= {lo}")
        if hi is not None and v > hi:
            errors.append(f"{key}: must be <= {hi}")

    _check_num("pricePerModule", lo=0)
    _check_num("priceBase", lo=0)
    _check_num("revPerColDay", lo=0)
    _check_num("wechipSharePct", lo=0, hi=100)
    _check_num("discountPct", lo=0, hi=95)
    _check_num("columns", lo=4, hi=16)
    if "opexAssumptions" in cfg and not isinstance(cfg["opexAssumptions"], dict):
        errors.append("opexAssumptions: must be an object")
    if "opexByWechip" in cfg and not isinstance(cfg["opexByWechip"], bool):
        errors.append("opexByWechip: must be a boolean")
    if "sharingFromStart" in cfg and not isinstance(cfg["sharingFromStart"], bool):
        errors.append("sharingFromStart: must be a boolean")
    # Reject unknown keys to keep storage tidy.
    allowed = set(CONFIG_KEYS)
    for k in cfg.keys():
        if k not in allowed:
            errors.append(f"unknown key: {k}")
    return errors


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

    @app.route("/api/health")
    def health() -> Response:
        return Response(
            json.dumps({"status": "ok"}, separators=(",", ":")),
            mimetype="application/json",
        )

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
        cfg = dict(link["config"])
        model = _coerce_model(link.get("model"))
        if model != "auto":
            cfg["model"] = model
        body = _render_calculator(html(), cfg, display_name=link.get("display_name", ""))
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

    @app.route("/admin")
    @app.route("/admin/")
    @basic_auth_required
    def admin_calculator() -> Response:
        slug = request.args.get("slug", "").strip().lower()
        cfg: dict[str, Any] = {}
        display_name = ""
        editing_slug: str | None = None
        if slug and SLUG_RE.match(slug):
            link = link_db.get_link(slug, dbp())
            if link:
                cfg = dict(link.get("config", {}))
                display_name = link.get("display_name", "")
                editing_slug = slug
                cfg["model"] = _coerce_model(link.get("model"))
        body = _render_calculator(
            html(), cfg, display_name=display_name,
            admin_mode=True, admin_slug=editing_slug,
        )
        return Response(body, mimetype="text/html")

    @app.route("/admin/api/links", methods=["POST"])
    @basic_auth_required
    def admin_api_create():
        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip().lower()
        display_name = (data.get("display_name") or "").strip()
        config = data.get("config") or {}
        if not isinstance(config, dict):
            return {"ok": False, "errors": ["config: must be object"]}, 400
        if not SLUG_RE.match(slug):
            return {"ok": False, "errors": ["slug: invalid"]}, 400
        errors = _validate_config(config)
        if errors:
            return {"ok": False, "errors": errors}, 400
        model = _coerce_model(data.get("model"))
        try:
            link_db.create_link(slug, display_name, config, dbp(), model=model)
        except sqlite3.IntegrityError:
            return {"ok": False, "errors": ["slug: already exists"]}, 409
        return {"ok": True, "slug": slug, "url": url_for("customer_link", slug=slug, _external=True)}

    @app.route("/admin/api/links/<slug>", methods=["PUT"])
    @basic_auth_required
    def admin_api_update(slug: str):
        if not SLUG_RE.match(slug):
            abort(404)
        if not link_db.get_link(slug, dbp()):
            abort(404)
        data = request.get_json(silent=True) or {}
        display_name = (data.get("display_name") or "").strip()
        config = data.get("config") or {}
        if not isinstance(config, dict):
            return {"ok": False, "errors": ["config: must be object"]}, 400
        errors = _validate_config(config)
        if errors:
            return {"ok": False, "errors": errors}, 400
        model = _coerce_model(data.get("model"))
        link_db.update_link(slug, display_name, config, dbp(), model=model)
        return {"ok": True, "slug": slug}

    @app.route("/admin/api/links/<slug>/revoke", methods=["POST"])
    @basic_auth_required
    def admin_api_revoke(slug: str):
        if not SLUG_RE.match(slug):
            abort(404)
        link_db.revoke_link(slug, dbp())
        return {"ok": True}

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
