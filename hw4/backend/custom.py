"""Custom Dan Gear (Problem 10 Part C): a focused, customer-facing version of the Ask Dan Image Studio.

Customers describe a Handsome Dan image (on the Design with Dan page or in the chat), the shop creates it
with the one-off image generator, and they put it on one of 7 blank products (tee, crewneck, hoodie,
mousepad, insulated cup, notebook, folder) and add it to their bag.

Saved designs (Part C2): a customer's designs stay in their account for 90 days, then they're deleted.

Guards (the "Strict" choice): signed-in customers only, 3 creations per customer per day, one at a time,
a $3/day site-wide spending cap (in-flight images are reserved at the per-image estimate), and a
moderation check on the request before any money is spent. The image model's own safety system runs too.

Images are created with OpenAI gpt-image (images/edits + Dan reference photos). The class Portkey key
can't make images, so OPENAI_API_KEY is read from ask-dan-image-studio/.env, never logged or returned.
Set CUSTOM_IMAGE_PROVIDER=mock to develop without spending anything.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import dotenv_values
from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from pydantic import BaseModel, Field

import catalog
import dan_voice
from auth import current_user
from db import DATA_DIR, PROJECT_DIR, connect
from models import DesignBrief, DraftedBrief

log = logging.getLogger("campus_customs.custom")

# --- The 7 blank products ------------------------------------------------------------
# Single-piece prices modeled on custom-gear sites like CustomInk (see output/design.md, Part C).
# print = the printable area on the mockup photo, as fractions of the image (x, y, w, h).
# bleed = the design fills the whole area (mousepad, covers); otherwise it's placed and scaled inside it.

APPAREL_SIZES = ["S", "M", "L", "XL", "XXL"]
XXL_UPCHARGE = 2.00

CUSTOM_PRODUCTS: list[dict] = [
    {"key": "tee", "name": "Custom Dan Tee", "kind": "Apparel", "price": 24.99, "sizes": APPAREL_SIZES,
     "blurb": "Soft white cotton crew-neck tee, full-color front print.", "color": "White",
     "print": {"x": 0.33, "y": 0.27, "w": 0.34, "h": 0.40}, "bleed": False, "dark": False},
    {"key": "crewneck", "name": "Custom Dan Crewneck", "kind": "Apparel", "price": 39.99, "sizes": APPAREL_SIZES,
     "blurb": "Heather-gray fleece crewneck sweatshirt, full-color front print.", "color": "Heather gray",
     "print": {"x": 0.34, "y": 0.27, "w": 0.32, "h": 0.36}, "bleed": False, "dark": False},
    {"key": "hoodie", "name": "Custom Dan Hoodie", "kind": "Apparel", "price": 49.99, "sizes": APPAREL_SIZES,
     "blurb": "Navy pullover fleece hoodie with kangaroo pocket, full-color front print.", "color": "Navy",
     "print": {"x": 0.355, "y": 0.30, "w": 0.29, "h": 0.27}, "bleed": False, "dark": True},
    {"key": "mousepad", "name": "Custom Dan Mousepad", "kind": "Desk", "price": 14.99, "sizes": ["One size"],
     "blurb": "Full-bleed fabric mousepad with stitched edge, about 9.25 × 7.75 in.", "color": "White",
     "print": {"x": 0.07, "y": 0.165, "w": 0.86, "h": 0.665}, "bleed": True, "dark": False},
    {"key": "cup", "name": "Custom Dan Insulated Cup", "kind": "Drinkware", "price": 29.99, "sizes": ["20 oz"],
     "blurb": "20 oz double-wall stainless tumbler with clear slide lid, printed wrap.", "color": "White",
     "print": {"x": 0.33, "y": 0.33, "w": 0.34, "h": 0.40}, "bleed": False, "dark": False},
    {"key": "notebook", "name": "Custom Dan Notebook", "kind": "Desk", "price": 16.99, "sizes": ["One size"],
     "blurb": "Spiral hardcover notebook, full-color cover, 100 lined sheets.", "color": "White",
     "print": {"x": 0.27, "y": 0.10, "w": 0.55, "h": 0.80}, "bleed": False, "dark": False},
    {"key": "folder", "name": "Custom Dan Folder", "kind": "Desk", "price": 8.99, "sizes": ["One size"],
     "blurb": "Two-pocket presentation folder, full-color front cover.", "color": "White",
     "print": {"x": 0.21, "y": 0.13, "w": 0.58, "h": 0.74}, "bleed": False, "dark": False},
]
PRODUCTS_BY_KEY = {p["key"]: p for p in CUSTOM_PRODUCTS}

# Quantity breaks, like custom-gear sites: price per item drops as the order grows.
QTY_BREAKS = [(24, 0.15), (12, 0.10)]
MAX_QTY = 144


def public_product(p: dict) -> dict:
    return {**p, "mockup_url": f"/media/custom/mockups/{p['key']}.webp", "xxl_upcharge": XXL_UPCHARGE if p["kind"] == "Apparel" else 0}


def unit_price(p: dict, size: str, quantity: int) -> float:
    base = p["price"] + (XXL_UPCHARGE if size == "XXL" else 0)
    off = next((pct for n, pct in QTY_BREAKS if quantity >= n), 0)
    return round(base * (1 - off), 2)


# --- Settings ------------------------------------------------------------------------

STUDIO_ENV = PROJECT_DIR / "ask-dan-image-studio" / ".env"
REF_DIR = PROJECT_DIR / "ask-dan-image-studio" / "references" / "dan"
REFERENCES = ["Welcome_Dan.png", "Dan_Ice_Hockey.png"]  # who Dan is: coat, face, build
DESIGN_DIR = DATA_DIR / "custom" / "designs"

PROVIDER = os.getenv("CUSTOM_IMAGE_PROVIDER", "openai")  # "mock" for free local testing
IMAGE_MODEL = os.getenv("CUSTOM_IMAGE_MODEL", "gpt-image-2.5-sunburst")
IMAGE_SIZE, IMAGE_QUALITY = "1024x1024", "high"
OPENAI_URL = "https://api.openai.com/v1"
PRICES = {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0}  # USD per 1M tokens (gpt-image-2.5)
EST_COST = 0.15  # conservative per-image reservation (actual ≈ $0.08–0.12, recorded from usage)

RETENTION_DAYS = 90  # designs are saved in the customer's account this long (Part C2)
ACTIVE = f"created_at >= datetime('now', '-{RETENTION_DAYS} days')"

USER_DAILY_LIMIT = int(os.getenv("CUSTOM_USER_DAILY_LIMIT", "3"))
SITE_DAILY_BUDGET = float(os.getenv("CUSTOM_SITE_DAILY_BUDGET", "3.00"))

# Starter designs: the shop's own Dan art, free to put on gear without creating anything.
STARTERS = ["welcome_dan", "dan_sport_football", "dan_custom_dan_carves_a_trumbull_pumpkin", "dan_sport_ice_hockey",
            "dan_hoodie", "dan_rival_harvard"]

_guard = threading.Lock()  # makes "check the limits, then reserve a slot" atomic


def _openai_key() -> str | None:
    return os.getenv("OPENAI_API_KEY") or dotenv_values(STUDIO_ENV).get("OPENAI_API_KEY")


# --- Prompt (identity + negatives match the Ask Dan Image Studio) --------------------

IDENTITY = (
    "SUBJECT: Handsome Dan, Yale University's mascot: a friendly, stocky BROWN-AND-WHITE ENGLISH BULLDOG. "
    "Match the dog in the reference photos exactly: same brown-and-white coat distribution, broad face, heavy jowls, "
    "deep facial wrinkles, underbite, expressive dark eyes, short muzzle and stocky, low body. He is a real dog, "
    "never a human, a costume or a different breed. Dan is the clear hero and fills much of the frame."
)
NEGATIVES = (
    "AVOID: collages, split panels, borders, captions, watermarks, signatures, gibberish or invented text, misspellings, "
    "extra or missing limbs, distorted paws, logos, brand names, crests or heraldry, real or famous people, alcohol, "
    "anything sexual or suggestive, rude gestures or words, blood, gore, injuries, real weapons, anything frightening. "
    "Rivalry jokes (e.g. Dan out-running a Harvard player) stay cartoon slapstick: nobody is hurt."
)
STYLE = {
    "photo": "STYLE: photorealistic editorial photo, realistic fur, natural lighting, shallow depth of field. "
             "Square composition that reads well printed on merchandise.",
    "sticker": "STYLE: a bold, clean DIE-CUT STICKER illustration of Dan (semi-realistic painted look, still clearly the same "
               "dog), with a thick white outline around the whole figure, on a PURE WHITE (#FFFFFF) background. Small props may "
               "touch Dan, but there is no scenery, no ground and no shadow. Centered with white margin on every side.",
}


def build_prompt(b: DesignBrief) -> str:
    words = [w.strip() for w in b.text if w.strip()]
    text_rule = ("EXACT TEXT: the only readable words allowed are: " + ", ".join(f'"{w}"' for w in words)
                 + ". Spell them exactly." if words else "EXACT TEXT: no readable words anywhere.")
    return "\n\n".join([IDENTITY, f"SCENE ({b.title}): {b.scene}", STYLE[b.style], text_rule, NEGATIVES,
                        "FORMAT: one single square image, one continuous scene, printed on Campus Customs custom gear."])


# --- Safety (Part C2 guardrails) ----------------------------------------------------
# Never: anything sexual, foul language, anything disparaging any group of people, or overly violent images.
# Allowed: cartoon slapstick toward rival schools (Dan bowling over a Harvard lineman, a pie for Princeton).
# Every refusal is answered in Handsome Dan's voice (dan_voice.REFUSALS).

# Other brands / characters / hate symbols: checked locally, before anything costs money.
BLOCKED = re.compile(
    r"\b(nike|adidas|under armou?r|disney|mickey|marvel|pok[eé]mon|pikachu|star wars|harry potter|nfl|nba|mlb|"
    r"coca[- ]?cola|pepsi|starbucks|mcdonald'?s)\b",
    re.I,
)
HATE_SYMBOLS = re.compile(r"\b(swastikas?|nazis?|kkk|confederate flag)\b", re.I)
# Foul language anywhere in the request or the words to print (moderation APIs don't block mild profanity).
FOUL = re.compile(
    r"\b(f+[u*]+c*k+\w*|f\*+\w*|sh[i1*]t\w*|b[i1*]tch\w*|a+ss+holes?|asses?|bastards?|damn\w*|crap\w*|piss\w*|dicks?|"
    r"cocks?|cunts?|sluts?|whores?|wtf|stfu|bullshit|jackass\w*|douche\w*)\b",
    re.I,
)
# OpenAI moderation categories that always block. Plain "violence" is judged by score instead, so cartoon
# rivalry (a tackle, a chase) passes while realistic or graphic violence doesn't.
ALWAYS_BLOCK = ("sexual", "sexual/minors", "hate", "hate/threatening", "harassment", "harassment/threatening",
                "self-harm", "self-harm/intent", "self-harm/instructions", "illicit", "illicit/violent", "violence/graphic")
VIOLENCE_MAX = 0.80


class Refused(Exception):
    """A request the shop won't make. The message is already in Dan's voice."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(dan_voice.refusal(reason))


def check_text(text: str) -> None:
    """The free, local checks (also used by the design agent before it drafts anything)."""
    if BLOCKED.search(text):
        raise Refused("brand")
    if FOUL.search(text):
        raise Refused("language")
    if HATE_SYMBOLS.search(text):
        raise Refused("unsafe")


def moderation_verdict(result: dict) -> str | None:
    """Which policy a moderation result breaks ('unsafe'), or None if it's fine."""
    cats, scores = result.get("categories") or {}, result.get("category_scores") or {}
    if any(cats.get(c) for c in ALWAYS_BLOCK):
        return "unsafe"
    if (scores.get("violence") or 0) >= VIOLENCE_MAX:
        return "unsafe"
    return None


def moderate(text: str) -> None:
    """Raise Refused if the request breaks the rules. Fails CLOSED: no check, no image."""
    check_text(text)
    key = _openai_key()
    if not key:
        if PROVIDER == "mock":
            return
        raise HTTPException(503, "Design creation is unavailable right now.")
    try:
        r = httpx.post(f"{OPENAI_URL}/moderations", headers={"Authorization": f"Bearer {key}"},
                       json={"model": "omni-moderation-latest", "input": text}, timeout=20)
        r.raise_for_status()
        result = r.json()["results"][0]
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        log.exception("moderation check failed")
        raise HTTPException(503, "Our safety check is unavailable right now. Please try again in a minute.")
    if reason := moderation_verdict(result):
        raise Refused(reason)


# --- Briefs --------------------------------------------------------------------------


def save_brief(brief: DesignBrief, user_id: int | None) -> DraftedBrief:
    with connect(readonly=False) as conn:
        cur = conn.execute("INSERT INTO custom_briefs (user_id, brief_json) VALUES (?, ?)", (user_id, brief.model_dump_json()))
        conn.commit()
    return DraftedBrief(brief_id=cur.lastrowid, **brief.model_dump())


def load_brief(brief_id: int, user_id: int) -> DesignBrief | None:
    with connect() as conn:
        row = conn.execute("SELECT user_id, brief_json FROM custom_briefs WHERE id = ?", (brief_id,)).fetchone()
    if not row or row["user_id"] not in (None, user_id):  # guests' chat drafts can be claimed after signing in
        return None
    return DesignBrief.model_validate_json(row["brief_json"])


# --- Allowance (per customer and site-wide, per local day) ---------------------------

TODAY = "date(created_at, 'localtime') = date('now', 'localtime')"
COUNTS = "(status IN ('queued', 'generating', 'ready') OR cost_usd > 0)"  # free failures don't use a creation


def allowance(user_id: int | None) -> dict:
    with connect() as conn:
        spent = conn.execute(f"SELECT COALESCE(SUM(cost_usd), 0) FROM custom_designs WHERE {TODAY}").fetchone()[0]
        inflight = conn.execute(f"SELECT COUNT(*) FROM custom_designs WHERE {TODAY} AND status IN ('queued', 'generating')").fetchone()[0]
        used = busy = 0
        if user_id:
            used = conn.execute(f"SELECT COUNT(*) FROM custom_designs WHERE user_id = ? AND {TODAY} AND {COUNTS}", (user_id,)).fetchone()[0]
            busy = conn.execute("SELECT COUNT(*) FROM custom_designs WHERE user_id = ? AND status IN ('queued', 'generating')", (user_id,)).fetchone()[0]
    reserved = spent + inflight * EST_COST
    return {
        "signed_in": bool(user_id),
        "daily_limit": USER_DAILY_LIMIT,
        "used_today": used,
        "remaining_today": max(0, USER_DAILY_LIMIT - used),
        "in_progress": busy > 0,
        "site_open": reserved + EST_COST <= SITE_DAILY_BUDGET,
    }


# --- Image generation ----------------------------------------------------------------


def _reference_files() -> list[tuple]:
    files = []
    for name in REFERENCES:
        im = Image.open(REF_DIR / name).convert("RGB")
        im.thumbnail((1024, 1024))  # smaller upload, fewer input tokens
        buf = io.BytesIO()
        im.save(buf, "PNG")
        files.append(("image[]", (name, buf.getvalue(), "image/png")))
    return files


def _cost(usage: dict) -> float:
    det = usage.get("input_tokens_details") or {}
    out = usage.get("output_tokens")
    if out is None:
        return EST_COST
    return round(((det.get("text_tokens") or 0) * PRICES["text_in"] + (det.get("image_tokens") or 0) * PRICES["image_in"]
                  + out * PRICES["image_out"]) / 1_000_000, 4)


def _generate_openai(prompt: str) -> tuple[bytes, float]:
    key = _openai_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    data = {"model": IMAGE_MODEL, "prompt": prompt, "size": IMAGE_SIZE, "quality": IMAGE_QUALITY, "n": "1", "output_format": "png"}
    for attempt in range(2):  # one retry on rate limits / server errors (those aren't billed)
        try:
            r = httpx.post(f"{OPENAI_URL}/images/edits", headers={"Authorization": f"Bearer {key}"},
                           data=data, files=_reference_files(), timeout=httpx.Timeout(300, connect=20))
        except httpx.TransportError:
            if attempt:
                raise
            continue
        if r.status_code == 429 or r.status_code >= 500:
            if attempt:
                r.raise_for_status()
            continue
        if r.status_code == 400 and ("safety" in r.text or "moderation" in r.text):
            raise Refused("service")
        r.raise_for_status()
        body = r.json()
        return base64.b64decode(body["data"][0]["b64_json"]), _cost(body.get("usage") or {})
    raise RuntimeError("image generation failed")


def _generate_mock(prompt: str, style: str) -> tuple[bytes, float]:
    """Free stand-in for development: the Welcome Dan portrait, tinted, with no network call."""
    im = Image.open(REF_DIR / "Welcome_Dan.png").convert("RGB").resize((1024, 1024))
    if style == "sticker":
        canvas = Image.new("RGB", (1024, 1024), "white")
        mask = Image.new("L", (1024, 1024), 0)
        ImageDraw.Draw(mask).ellipse((140, 120, 884, 900), fill=255)
        canvas.paste(im, (0, 0), mask)
        im = canvas
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue(), 0.0


def cut_out_background(png: bytes) -> Image.Image:
    """Sticker style: make the white background transparent (only white connected to the border,
    so white inside the design, like the sticker outline or Dan's white fur, stays)."""
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    W, H = im.size
    r, g, b = (ch.point(lambda v: 255 if v >= 236 else 0) for ch in im.convert("RGB").split())
    near_white = ImageChops.multiply(ImageChops.multiply(r, g), b)  # 255 only where every channel is near white
    # Pad by 1px of white so a single flood fill from the corner reaches the whole border.
    padded = Image.new("L", (W + 2, H + 2), 255)
    padded.paste(near_white, (1, 1))
    ImageDraw.floodfill(padded, (0, 0), 128)
    background = padded.crop((1, 1, W + 1, H + 1)).point(lambda v: 255 if v == 128 else 0)
    alpha = ImageChops.invert(background).filter(ImageFilter.GaussianBlur(1.0))
    im.putalpha(alpha)
    return im


def _save_images(png: bytes, style: str) -> str:
    token = secrets.token_hex(10)  # unguessable file name
    DESIGN_DIR.mkdir(parents=True, exist_ok=True)
    im = cut_out_background(png) if style == "sticker" else Image.open(io.BytesIO(png)).convert("RGB")
    im.save(DESIGN_DIR / f"{token}.png", "PNG")  # full resolution, for printing
    im.save(DESIGN_DIR / f"{token}.webp", "WEBP", quality=88)
    im.resize((400, 400), Image.LANCZOS).save(DESIGN_DIR / f"{token}_sm.webp", "WEBP", quality=82)
    return token


def _finish(design_id: int, **fields) -> None:
    sets = ", ".join(f"{k} = ?" for k in fields)
    with connect(readonly=False) as conn:
        conn.execute(f"UPDATE custom_designs SET {sets}, finished_at = datetime('now') WHERE id = ?", (*fields.values(), design_id))
        conn.commit()


def run_generation(design_id: int, prompt: str, style: str) -> None:
    """Background task (runs after the POST returns; the page polls GET /designs/{id})."""
    with connect(readonly=False) as conn:
        conn.execute("UPDATE custom_designs SET status = 'generating' WHERE id = ?", (design_id,))
        conn.commit()
    try:
        png, cost = _generate_mock(prompt, style) if PROVIDER == "mock" else _generate_openai(prompt)
        token = _save_images(png, style)
        _finish(design_id, status="ready", image_token=token, cost_usd=cost)
        log.info("design %s ready ($%.4f)", design_id, cost)
    except Refused as e:
        _finish(design_id, status="failed", error=str(e))
    except Exception:
        log.exception("design %s failed", design_id)
        _finish(design_id, status="failed", error="Dan couldn't finish this one. It didn't count against your daily creations; please try again.")


def purge_expired() -> int:
    """Delete designs older than RETENTION_DAYS: their image files, any bag lines using them, and the rows."""
    with connect(readonly=False) as conn:
        rows = conn.execute(f"SELECT id, image_token FROM custom_designs WHERE NOT ({ACTIVE})").fetchall()
        for r in rows:
            if r["image_token"]:
                for suffix in (".png", ".webp", "_sm.webp"):
                    (DESIGN_DIR / f"{r['image_token']}{suffix}").unlink(missing_ok=True)
            conn.execute("DELETE FROM bag_items WHERE design_ref = ?", (f"d:{r['id']}",))
            conn.execute("DELETE FROM custom_designs WHERE id = ?", (r["id"],))
        conn.commit()
    if rows:
        log.info("purged %d expired designs", len(rows))
    return len(rows)


def recover_stale() -> None:
    """A server restart mid-generation leaves rows 'queued'/'generating' forever; release them."""
    with connect(readonly=False) as conn:
        conn.execute("UPDATE custom_designs SET status = 'failed', error = 'Interrupted. It did not count; please try again.', "
                     "finished_at = datetime('now') WHERE status IN ('queued', 'generating') AND cost_usd = 0")
        conn.commit()


# --- Serialization -------------------------------------------------------------------


STARTER_TITLES = {"welcome_dan": "Welcome Dan", "dan_sport_football": "Game day vs. Harvard",
                  "dan_custom_dan_carves_a_trumbull_pumpkin": "Trumbull pumpkin", "dan_sport_ice_hockey": "Ice hockey Dan",
                  "dan_hoodie": "Big-hoodie Dan", "dan_rival_harvard": "The Harvard side-eye"}


def starter_design(asset_id: str) -> dict | None:
    d = catalog.dan_for_asset(asset_id)
    title = STARTER_TITLES.get(asset_id) or (d and d["category"])
    if not title or not (catalog.DAN_DIR / f"{asset_id}.webp").exists():
        return None
    small = catalog.DAN_DIR / f"{asset_id}_sm.webp"
    return {"ref": f"starter:{asset_id}", "title": title, "style": "photo", "status": "ready", "kind": "starter",
            "image_url": f"/media/dan/{asset_id}.webp",
            "thumb_url": f"/media/dan/{asset_id}_sm.webp" if small.exists() else f"/media/dan/{asset_id}.webp"}


def _expiry(created_at: str) -> tuple[str, int]:
    """(expires_at ISO date, whole days left) for a design created at this UTC timestamp."""
    created = datetime.fromisoformat(created_at).replace(tzinfo=timezone.utc)
    expires = created + timedelta(days=RETENTION_DAYS)
    return expires.date().isoformat(), max(0, (expires - datetime.now(timezone.utc)).days)


def design_out(row) -> dict:
    t = row["image_token"]
    expires_at, days_left = _expiry(row["created_at"])
    return {"ref": f"d:{row['id']}", "id": row["id"], "title": row["title"], "style": row["style"], "status": row["status"],
            "kind": "mine", "error": row["error"], "created_at": row["created_at"],
            "expires_at": expires_at, "days_left": days_left,
            "image_url": f"/media/custom/designs/{t}.webp" if t else None,
            "thumb_url": f"/media/custom/designs/{t}_sm.webp" if t else None}


def resolve_design(ref: str, user_id: int) -> dict | None:
    """A design the customer may use: one of theirs that is ready, or a starter."""
    if ref.startswith("starter:"):
        asset = ref.split(":", 1)[1]
        return starter_design(asset) if asset in STARTERS else None
    m = re.fullmatch(r"d:(\d+)", ref)
    if not m:
        return None
    with connect() as conn:
        row = conn.execute(f"SELECT * FROM custom_designs WHERE id = ? AND user_id = ? AND {ACTIVE}",
                           (int(m.group(1)), user_id)).fetchone()
    return design_out(row) if row and row["status"] == "ready" else None


# --- Routes: /api/custom -------------------------------------------------------------

router = APIRouter(prefix="/api/custom", tags=["custom"])


def _require_user(cc_session: str | None) -> dict:
    user = current_user(cc_session)
    if not user:
        raise HTTPException(401, "Please log in to create and save custom designs.")
    return user


@router.get("/products")
def products() -> dict:
    return {"products": [public_product(p) for p in CUSTOM_PRODUCTS],
            "qty_breaks": [{"min_qty": n, "percent_off": round(pct * 100)} for n, pct in sorted(QTY_BREAKS)]}


@router.get("/status")
def status(cc_session: str | None = Cookie(default=None)) -> dict:
    user = current_user(cc_session)
    return {**allowance(user["id"] if user else None), "mock": PROVIDER == "mock"}


@router.get("/designs")
def list_designs(cc_session: str | None = Cookie(default=None)) -> dict:
    user = current_user(cc_session)
    mine = []
    if user:
        purge_expired()
        with connect() as conn:
            rows = conn.execute(f"SELECT * FROM custom_designs WHERE user_id = ? AND {ACTIVE} AND status != 'failed' "
                                "ORDER BY id DESC LIMIT 60", (user["id"],)).fetchall()
            # Show the most recent failure too (so a refusal is visible), but not old ones.
            failed = conn.execute("SELECT * FROM custom_designs WHERE user_id = ? AND status = 'failed' "
                                  "AND created_at >= datetime('now', '-1 day') ORDER BY id DESC LIMIT 1", (user["id"],)).fetchall()
        mine = sorted([design_out(r) for r in [*rows, *failed]], key=lambda d: -d["id"])
    return {"mine": mine, "starters": [d for a in STARTERS if (d := starter_design(a))],
            "retention_days": RETENTION_DAYS}


@router.get("/designs/{design_id}")
def get_design(design_id: int, cc_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cc_session)
    with connect() as conn:
        row = conn.execute("SELECT * FROM custom_designs WHERE id = ? AND user_id = ?", (design_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(404, "Design not found.")
    return design_out(row)


class CreateDesignIn(BaseModel):
    brief_id: int


@router.post("/designs", status_code=202)
def create_design(body: CreateDesignIn, tasks: BackgroundTasks, cc_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cc_session)
    brief = load_brief(body.brief_id, user["id"])
    if brief is None:
        raise HTTPException(404, "That design idea wasn't found. Describe it again and Dan will redraft it.")
    prompt = build_prompt(brief)
    try:
        moderate(f"{brief.title}\n{brief.scene}\n{' '.join(brief.text)}")
    except Refused as e:
        raise HTTPException(422, str(e))

    with _guard:  # check and reserve together, so two quick clicks can't both slip under a limit
        a = allowance(user["id"])
        if a["in_progress"]:
            raise HTTPException(429, "Dan is still working on your last design. Give him a moment!")
        if a["remaining_today"] <= 0:
            raise HTTPException(429, f"You've created {USER_DAILY_LIMIT} designs today, the daily limit. Come back tomorrow, "
                                     "or put one of your designs or a classic Dan on some gear.")
        if not a["site_open"]:
            raise HTTPException(429, "Dan's studio is closed for today. Please try again tomorrow, or use a classic Dan design.")
        with connect(readonly=False) as conn:
            cur = conn.execute("INSERT INTO custom_designs (user_id, brief_id, title, style, status) VALUES (?, ?, ?, ?, 'queued')",
                               (user["id"], body.brief_id, brief.title, brief.style))
            conn.commit()
            design_id = cur.lastrowid
    tasks.add_task(run_generation, design_id, prompt, brief.style)
    return get_design(design_id, cc_session)


# --- Routes: /api/bag ----------------------------------------------------------------

bag_router = APIRouter(prefix="/api/bag", tags=["bag"])


class Placement(BaseModel):
    scale: float = Field(default=0.85, ge=0.4, le=1.0)  # share of the print area's width
    y: float = Field(default=0.0, ge=-1.0, le=1.0)  # -1 top … 0 middle … 1 bottom of the free space


class BagItemIn(BaseModel):
    product_key: str
    design_ref: str = Field(max_length=40)
    size: str
    quantity: int = Field(ge=1, le=MAX_QTY)
    placement: Placement = Field(default_factory=Placement)


class BagQtyIn(BaseModel):
    quantity: int = Field(ge=1, le=MAX_QTY)


def bag_for(user_id: int) -> dict:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM bag_items WHERE user_id = ? ORDER BY id", (user_id,)).fetchall()
    items = []
    for r in rows:
        p = PRODUCTS_BY_KEY.get(r["product_key"])
        design = resolve_design(r["design_ref"], user_id)
        if not p or not design:
            continue
        unit = unit_price(p, r["size"], r["quantity"])  # always recomputed on the server
        items.append({"id": r["id"], "product": public_product(p), "design": design, "size": r["size"],
                      "quantity": r["quantity"], "placement": json.loads(r["placement_json"]),
                      "unit_price": unit, "line_total": round(unit * r["quantity"], 2)})
    return {"items": items, "count": sum(i["quantity"] for i in items),
            "subtotal": round(sum(i["line_total"] for i in items), 2)}


@bag_router.get("")
def get_bag(cc_session: str | None = Cookie(default=None)) -> dict:
    user = current_user(cc_session)
    return bag_for(user["id"]) if user else {"items": [], "count": 0, "subtotal": 0}


@bag_router.post("", status_code=201)
def add_to_bag(body: BagItemIn, cc_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cc_session)
    p = PRODUCTS_BY_KEY.get(body.product_key)
    if not p:
        raise HTTPException(404, "Unknown product.")
    if body.size not in p["sizes"]:
        raise HTTPException(422, f"{p['name']} comes in: {', '.join(p['sizes'])}.")
    if not resolve_design(body.design_ref, user["id"]):
        raise HTTPException(404, "That design isn't available.")
    with connect(readonly=False) as conn:
        conn.execute("INSERT INTO bag_items (user_id, product_key, design_ref, size, quantity, placement_json) VALUES (?, ?, ?, ?, ?, ?)",
                     (user["id"], p["key"], body.design_ref, body.size, body.quantity, body.placement.model_dump_json()))
        conn.commit()
    return bag_for(user["id"])


@bag_router.patch("/{item_id}")
def update_bag_item(item_id: int, body: BagQtyIn, cc_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cc_session)
    with connect(readonly=False) as conn:
        conn.execute("UPDATE bag_items SET quantity = ? WHERE id = ? AND user_id = ?", (body.quantity, item_id, user["id"]))
        conn.commit()
    return bag_for(user["id"])


@bag_router.delete("/{item_id}")
def remove_bag_item(item_id: int, cc_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cc_session)
    with connect(readonly=False) as conn:
        conn.execute("DELETE FROM bag_items WHERE id = ? AND user_id = ?", (item_id, user["id"]))
        conn.commit()
    return bag_for(user["id"])
