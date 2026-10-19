"""SQLite helpers shared by the product API and auth."""

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

# Secrets (PORTKEY_API_KEY, SESSION_SECRET) come from a .env file, never from code. Graders put it in hw4/.env;
# the owner keeps it outside the repo (two folders up). Later files win; override=True so a stale key exported
# in the shell never wins. All .env files are git-ignored.
for env_file in (PROJECT_DIR.parent.parent / ".env", PROJECT_DIR.parent / ".env", PROJECT_DIR / ".env"):
    load_dotenv(env_file, override=True)

DB_PATH = Path(os.getenv("CAMPUS_CUSTOMS_DB", DATA_DIR / "campus_customs.db"))


def ensure_schema() -> None:
    """Additive, idempotent migrations on startup (never drops or rewrites data)."""
    with connect(readonly=False) as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(chat_messages)")}
        if "voice" not in cols:
            # Which voice wrote an assistant reply ("brand" or "dan"); NULL for user rows and older rows.
            conn.execute("ALTER TABLE chat_messages ADD COLUMN voice TEXT")
        # Chat history is always read per user, newest first.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")

        # Custom Dan Gear (Problem 10 Part C). The 7 blank products live in code (custom.py),
        # so these tables only hold what customers create: drafted briefs, generated designs, bag lines.
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS custom_briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),          -- NULL when a guest drafted it in chat
                brief_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS custom_designs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                brief_id INTEGER REFERENCES custom_briefs(id),
                title TEXT NOT NULL,
                style TEXT NOT NULL,
                status TEXT NOT NULL,                          -- queued | generating | ready | failed
                image_token TEXT,                              -- random file name under data/custom/designs/
                cost_usd REAL NOT NULL DEFAULT 0,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                finished_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_custom_designs_user ON custom_designs (user_id, id);
            CREATE TABLE IF NOT EXISTS bag_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                product_key TEXT NOT NULL,
                design_ref TEXT NOT NULL,                      -- "d:<design id>" or "starter:<dan asset id>"
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                placement_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_bag_items_user ON bag_items (user_id, id);
        """)
        fixed = apply_data_fixes(conn)
        conn.commit()
    if fixed:
        print(f"[db] Applied Problem 2 catalogue fixes to {fixed} product(s) (see backend/data_fixes.json).")


DATA_FIXES = Path(__file__).resolve().parent / "data_fixes.json"


def apply_data_fixes(conn: sqlite3.Connection) -> int:
    """Problem 2 content fixes, so the assignment's ORIGINAL campus_customs.db works as-is (the database is never
    committed). Three catalogue rows ship as filename stubs (no colors, a "Vision blocked" description); fill them
    with the reviewed values. Only rows that are still the original stub are touched, so it's safe to run every start."""
    fixes = json.loads(DATA_FIXES.read_text())["catalogue"] if DATA_FIXES.exists() else []
    changed = 0
    for f in fixes:
        cur = conn.execute(
            "UPDATE catalogue SET garment_type = ?, colors = ?, search_tags = ?, description = ? "
            "WHERE product_id = ? AND description LIKE '%Vision blocked%'",
            (f["garment_type"], json.dumps(f["colors"]), json.dumps(f["search_tags"]), f["description"], f["product_id"]),
        )
        changed += cur.rowcount
    return changed


@contextmanager
def connect(readonly: bool = True) -> Iterator[sqlite3.Connection]:
    # as_uri() percent-encodes spaces and "#" in the path; a raw "#" would start a URI fragment.
    mode = "ro" if readonly else "rw"
    conn = sqlite3.connect(f"{DB_PATH.resolve().as_uri()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
