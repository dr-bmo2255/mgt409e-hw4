"""Persistent local state (SQLite, versioned schema). Everything the user decides survives restarts."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from . import config

SCHEMA_VERSION = 1
_lock = threading.RLock()

STATUSES = ["EXISTING_REVIEWED", "MISSING", "QUEUED", "GENERATING", "PENDING_REVIEW", "REVISION_REQUESTED",
            "APPROVED", "REJECTED", "FAILED", "OUT_OF_SCOPE"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS assets (
  asset_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  approved_version INTEGER,
  notes TEXT,
  prompt_override TEXT,
  shield_override TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  updated_at REAL
);
CREATE TABLE IF NOT EXISTS versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  parent_version INTEGER,
  kind TEXT NOT NULL,              -- generate | revise | composite
  provider TEXT NOT NULL, model TEXT, settings TEXT,
  prompt TEXT, references_json TEXT, feedback TEXT,
  path TEXT NOT NULL, thumb TEXT, sha256 TEXT, width INTEGER, height INTEGER,
  cost_usd REAL NOT NULL DEFAULT 0, cost_is_estimate INTEGER NOT NULL DEFAULT 1, usage_json TEXT,
  decision TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | rejected | superseded
  qa_json TEXT,
  created_at REAL,
  UNIQUE(asset_id, version)
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT, asset_id TEXT NOT NULL, version INTEGER,
  kind TEXT NOT NULL, text TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS authorizations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,              -- pilot | batch | single
  asset_ids TEXT NOT NULL,         -- JSON list; requests outside it are refused
  max_images INTEGER NOT NULL, used_images INTEGER NOT NULL DEFAULT 0,
  budget_usd REAL NOT NULL, spent_usd REAL NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1, note TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  idem_key TEXT UNIQUE NOT NULL,   -- prevents duplicate generation on resume / double-click
  asset_id TEXT NOT NULL, kind TEXT NOT NULL, provider TEXT NOT NULL,
  parent_version INTEGER, feedback TEXT, authorization_id INTEGER,
  status TEXT NOT NULL,            -- queued | running | done | failed | cancelled
  est_cost REAL, error TEXT, version INTEGER,
  created_at REAL, started_at REAL, finished_at REAL
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS custom_assets (  -- one-off images requested in chat (not catalogue-scoped)
  asset_id TEXT PRIMARY KEY, brief TEXT NOT NULL, created_at REAL
);
CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, content TEXT NOT NULL,
  brief TEXT, revise_feedback TEXT, asset_id TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, kind TEXT, asset_id TEXT, message TEXT);
"""


def _connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or config.STATE_DB, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db():
    with _lock:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init(manifest: dict) -> None:
    with db() as c:
        c.executescript(SCHEMA)
        for r in c.execute("SELECT asset_id FROM custom_assets").fetchall():
            c.execute("INSERT OR IGNORE INTO assets (asset_id, status, updated_at) VALUES (?, 'MISSING', ?)", (r[0], time.time()))
        c.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
        for a in manifest["assets"]:
            c.execute("INSERT OR IGNORE INTO assets (asset_id, status, updated_at) VALUES (?, ?, ?)",
                      (a["asset_id"], a["status"], time.time()))
        for k, v in config.DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO settings VALUES (?, ?)", (k, json.dumps(v)))
        c.execute("INSERT OR IGNORE INTO settings VALUES ('references_confirmed', 'false')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('shields_confirmed', 'false')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('paused', 'false')")
        # Recover from a crash mid-job: never silently re-run a paid request.
        c.execute("UPDATE jobs SET status='failed', error='interrupted (app stopped while running); review before retrying' "
                  "WHERE status='running'")
        c.execute("UPDATE assets SET status='FAILED' WHERE status='GENERATING'")


# --- settings -------------------------------------------------------------------------------


def get_settings() -> dict:
    with db() as c:
        return {r["key"]: json.loads(r["value"]) for r in c.execute("SELECT key, value FROM settings")}


def set_setting(key: str, value) -> None:
    with db() as c:
        c.execute("INSERT INTO settings VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (key, json.dumps(value)))


# --- events & costs ----------------------------------------------------------------------------


def log(kind: str, message: str, asset_id: str | None = None) -> None:
    with db() as c:
        c.execute("INSERT INTO events (ts, kind, asset_id, message) VALUES (?, ?, ?, ?)", (time.time(), kind, asset_id, message))


def recent_events(limit: int = 30) -> list[dict]:
    with db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))]


def total_spent() -> float:
    with db() as c:
        return c.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM versions").fetchone()[0]


# --- assets / versions --------------------------------------------------------------------------

ALLOWED = {  # status machine: from → allowed next statuses
    "MISSING": {"QUEUED", "OUT_OF_SCOPE"},
    "EXISTING_REVIEWED": {"QUEUED", "OUT_OF_SCOPE"},  # regenerating an existing asset needs explicit user action
    "OUT_OF_SCOPE": {"MISSING"},
    "QUEUED": {"GENERATING", "MISSING", "PENDING_REVIEW", "APPROVED", "REJECTED", "REVISION_REQUESTED", "FAILED"},
    "GENERATING": {"PENDING_REVIEW", "FAILED", "QUEUED"},
    "PENDING_REVIEW": {"APPROVED", "REJECTED", "REVISION_REQUESTED", "QUEUED", "PENDING_REVIEW"},
    "REVISION_REQUESTED": {"QUEUED", "APPROVED", "REJECTED", "PENDING_REVIEW"},
    "APPROVED": {"PENDING_REVIEW", "REVISION_REQUESTED", "QUEUED"},  # a new version may be explored; approval kept
    "REJECTED": {"QUEUED", "PENDING_REVIEW", "APPROVED", "REVISION_REQUESTED", "MISSING"},
    "FAILED": {"QUEUED", "MISSING", "PENDING_REVIEW"},
}


class BadTransition(Exception):
    pass


def set_status(asset_id: str, new: str, conn: sqlite3.Connection | None = None) -> None:
    def _do(c):
        row = c.execute("SELECT status FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
        if row is None:
            raise KeyError(asset_id)
        if new != row["status"] and new not in ALLOWED.get(row["status"], set()):
            raise BadTransition(f"{asset_id}: {row['status']} → {new} not allowed")
        c.execute("UPDATE assets SET status=?, updated_at=? WHERE asset_id=?", (new, time.time(), asset_id))
    if conn is not None:
        _do(conn)
    else:
        with db() as c:
            _do(c)


def asset_state(asset_id: str) -> dict:
    with db() as c:
        a = dict(c.execute("SELECT * FROM assets WHERE asset_id=?", (asset_id,)).fetchone())
        a["versions"] = [dict(v) for v in c.execute("SELECT * FROM versions WHERE asset_id=? ORDER BY version", (asset_id,))]
        a["feedback"] = [dict(f) for f in c.execute("SELECT * FROM feedback WHERE asset_id=? ORDER BY id", (asset_id,))]
        a["jobs"] = [dict(j) for j in c.execute("SELECT * FROM jobs WHERE asset_id=? ORDER BY id DESC LIMIT 10", (asset_id,))]
    for v in a["versions"]:
        for k in ("settings", "references_json", "usage_json", "qa_json"):
            v[k] = json.loads(v[k]) if v.get(k) else None
    return a


def all_asset_states() -> dict[str, dict]:
    with db() as c:
        rows = {r["asset_id"]: dict(r) for r in c.execute("SELECT * FROM assets")}
        for r in c.execute("SELECT asset_id, COUNT(*) n, MAX(version) latest, COALESCE(SUM(cost_usd),0) cost FROM versions GROUP BY asset_id"):
            rows[r["asset_id"]].update(version_count=r["n"], latest_version=r["latest"], cost_usd=r["cost"])
        for r in c.execute("SELECT asset_id, thumb, version FROM versions v WHERE version=(SELECT MAX(version) FROM versions WHERE asset_id=v.asset_id)"):
            rows[r["asset_id"]]["latest_thumb"] = r["thumb"]
    return rows


def next_version(asset_id: str) -> int:
    with db() as c:
        return (c.execute("SELECT COALESCE(MAX(version), 0) FROM versions WHERE asset_id=?", (asset_id,)).fetchone()[0]) + 1


def add_feedback(asset_id: str, version: int | None, kind: str, text: str) -> None:
    with db() as c:
        c.execute("INSERT INTO feedback (asset_id, version, kind, text, created_at) VALUES (?, ?, ?, ?, ?)",
                  (asset_id, version, kind, text, time.time()))


# --- authorizations (the ONLY way paid requests are allowed) ---------------------------------------


def create_authorization(kind: str, asset_ids: list[str], max_images: int, budget_usd: float, note: str = "") -> int:
    with db() as c:
        cur = c.execute("INSERT INTO authorizations (kind, asset_ids, max_images, budget_usd, note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (kind, json.dumps(asset_ids), max_images, budget_usd, note, time.time()))
        return cur.lastrowid


def authorizations(active_only: bool = False) -> list[dict]:
    with db() as c:
        q = "SELECT * FROM authorizations" + (" WHERE active=1" if active_only else "") + " ORDER BY id DESC"
        out = [dict(r) for r in c.execute(q)]
    for a in out:
        a["asset_ids"] = json.loads(a["asset_ids"])
    return out


def find_authorization(asset_id: str, est_cost: float) -> dict | None:
    for a in authorizations(active_only=True):
        if asset_id in a["asset_ids"] and a["used_images"] < a["max_images"] and a["spent_usd"] + est_cost <= a["budget_usd"] + 1e-9:
            return a
    return None


def consume_authorization(auth_id: int, cost: float) -> None:
    with db() as c:
        c.execute("UPDATE authorizations SET used_images=used_images+1, spent_usd=spent_usd+? WHERE id=?", (cost, auth_id))
        c.execute("UPDATE authorizations SET active=0 WHERE id=? AND used_images>=max_images", (auth_id,))


def revoke_authorizations() -> None:
    with db() as c:
        c.execute("UPDATE authorizations SET active=0 WHERE active=1")
