"""SQLite storage for per-lead trackable ROI links."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Iterable, Iterator


DEFAULT_DB_PATH = os.environ.get("LINKS_DB_PATH", "./roi_links.db")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@contextmanager
def connect(db_path: str | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or DEFAULT_DB_PATH
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


ALLOWED_MODELS = ("auto", "filaire", "solaire")


def _normalize_model(value: Any) -> str:
    if isinstance(value, str) and value in ALLOWED_MODELS:
        return value
    return "auto"


def init_db(db_path: str | None = None) -> None:
    with connect(db_path) as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS links (
                slug TEXT PRIMARY KEY,
                display_name TEXT NOT NULL DEFAULT '',
                config_json TEXT NOT NULL DEFAULT '{}',
                model TEXT NOT NULL DEFAULT 'auto',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                revoked_at TEXT
            );
            CREATE TABLE IF NOT EXISTS link_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('view','change','print')),
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_link_events_slug_created
                ON link_events(slug, created_at);
            """
        )
        # Lazy migration for existing DBs created before `model` was added.
        cols = {r[1] for r in c.execute("PRAGMA table_info(links)").fetchall()}
        if "model" not in cols:
            c.execute("ALTER TABLE links ADD COLUMN model TEXT NOT NULL DEFAULT 'auto'")


# ── links CRUD ────────────────────────────────────────────────────────────

def create_link(
    slug: str,
    display_name: str,
    config: dict[str, Any],
    db_path: str | None = None,
    model: str = "auto",
) -> None:
    now = _now()
    with connect(db_path) as c:
        c.execute(
            "INSERT INTO links(slug, display_name, config_json, model, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (slug, display_name, json.dumps(config), _normalize_model(model), now, now),
        )


def update_link(
    slug: str,
    display_name: str,
    config: dict[str, Any],
    db_path: str | None = None,
    model: str = "auto",
) -> bool:
    with connect(db_path) as c:
        cur = c.execute(
            "UPDATE links SET display_name=?, config_json=?, model=?, updated_at=? WHERE slug=?",
            (display_name, json.dumps(config), _normalize_model(model), _now(), slug),
        )
        return cur.rowcount > 0


def revoke_link(slug: str, db_path: str | None = None) -> bool:
    with connect(db_path) as c:
        cur = c.execute(
            "UPDATE links SET revoked_at=COALESCE(revoked_at, ?), updated_at=? WHERE slug=?",
            (_now(), _now(), slug),
        )
        return cur.rowcount > 0


def get_link(slug: str, db_path: str | None = None) -> dict[str, Any] | None:
    with connect(db_path) as c:
        row = c.execute("SELECT * FROM links WHERE slug=?", (slug,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["config"] = json.loads(d.get("config_json") or "{}")
        d["model"] = _normalize_model(d.get("model"))
        return d


def list_links(db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as c:
        rows = c.execute(
            """
            SELECT l.*,
                   (SELECT COUNT(*) FROM link_events e WHERE e.slug=l.slug AND e.type='view') AS view_count,
                   (SELECT MAX(created_at) FROM link_events e WHERE e.slug=l.slug AND e.type='view') AS last_view
            FROM links l
            ORDER BY l.created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


# ── events ────────────────────────────────────────────────────────────────

def log_event(slug: str, type_: str, payload: dict[str, Any] | None = None, db_path: str | None = None) -> None:
    if type_ not in ("view", "change", "print"):
        raise ValueError(f"invalid event type: {type_}")
    raw = json.dumps(payload or {})
    if len(raw) > 2048:
        raw = raw[:2048]
    with connect(db_path) as c:
        c.execute(
            "INSERT INTO link_events(slug, type, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (slug, type_, raw, _now()),
        )


def list_events(slug: str, limit: int = 200, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as c:
        rows = c.execute(
            "SELECT * FROM link_events WHERE slug=? ORDER BY created_at DESC, id DESC LIMIT ?",
            (slug, limit),
        ).fetchall()
        return [dict(r) for r in rows]
