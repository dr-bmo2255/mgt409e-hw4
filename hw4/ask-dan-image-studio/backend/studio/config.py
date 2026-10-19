"""Paths and fixed settings for Ask Dan Image Studio."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(os.getenv("STUDIO_ROOT", Path(__file__).resolve().parents[2]))
INPUT_DIR = ROOT / "input"
WORK_DIR = ROOT / "output" / "work"  # safe extraction of the input ZIPs (read-only use)
REF_DAN_DIR = ROOT / "references" / "dan"
REF_SHIELD_DIR = ROOT / "references" / "shields"
MANIFEST_PATH = ROOT / "manifest" / "assets.json"
STATE_DB = ROOT / "state" / "studio.sqlite"
PENDING_DIR = ROOT / "output" / "pending_review"
APPROVED_DIR = ROOT / "output" / "approved"
REJECTED_DIR = ROOT / "output" / "rejected"
EXPORT_DIR = ROOT / "output" / "exports"
THUMB_DIR = ROOT / "output" / "thumbs"
REPORTS_DIR = ROOT / "reports"
FRONTEND_DIST = ROOT / "frontend" / "dist"

for d in (WORK_DIR, REF_DAN_DIR, REF_SHIELD_DIR, MANIFEST_PATH.parent, STATE_DB.parent, PENDING_DIR,
          APPROVED_DIR, REJECTED_DIR, EXPORT_DIR, THUMB_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Secrets: the Campus Customs project .env (two levels up), then the studio's own .env (wins if present).
# override=True so a stale key exported in the shell (e.g. an old ~/.zshrc entry) never wins over the files.
# Never logged or exported.
for _env in (ROOT.parent.parent.parent / ".env", ROOT.parent.parent / ".env", ROOT.parent / ".env", ROOT / ".env"):
    load_dotenv(_env, override=True)  # outside the repo (owner), hw4/.env (graders), then the studio's own .env

# Input files, matched flexibly (the user may supply newer / renamed archives).
INPUT_PATTERNS = {
    "spec": ["ASK_DAN*SPEC*.txt"],
    "dan_final_zip": ["Dan Final Images*.zip"],
    "dan_refs_zip": ["Dan Image References*.zip", "Dan images reference*.zip"],
    "catalogue_zip": ["data 2*.zip", "data*.zip"],
    "audit_xlsx": ["ask_dan*audit*.xlsx"],
    "checklist_txt": ["ask_dan*checklist*.txt"],
}

PILOT_ASSETS = ["dan_school_management", "dan_sport_lacrosse", "dan_hoodie"]
BATCH_DEFAULT, BATCH_MAX = 3, 5

DEFAULT_SETTINGS = {
    "provider": "mock",  # "mock" or "openai" (via Portkey or OpenAI directly)
    "model": "gpt-image-2.5-sunburst",
    "size": "1536x1536",
    "quality": "high",
    "cost_cap_usd": 15.0,  # hard cumulative cap; checked BEFORE every paid request
    "per_job_cap_usd": 0.75,
    "max_attempts_per_asset": 4,
    "batch_size": BATCH_DEFAULT,
    "automatic_mode": False,  # never on unless the user explicitly enables it
}

HOST, PORT = "127.0.0.1", 8765
