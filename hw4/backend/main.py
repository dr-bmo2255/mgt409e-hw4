"""Campus Customs API.

Problem 3: read-only product catalog, stock by size, and product images.
Problem 4: accounts (signup / login / logout / me) in auth.py.
Problem 5: POST /api/chat → PydanticAI agent (agent.py, tools.py, models.py, prompts/).
Problem 10C: Custom Dan Gear: /api/custom/* and /api/bag (custom.py, design_agent.py).

Run from backend/:  uvicorn main:app --reload --port 8000
"""

import json
import re
import logging

from fastapi import Cookie, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import agent
import dan_voice
import custom
import config
import design_agent
import limits
import prepare_data
from auth import current_user, router as auth_router
from catalog import CATEGORY_NAMES, dan_for_products, category_for, get_product as load_product, load_products
from db import DATA_DIR, connect, ensure_schema
from context import build_customer, build_page
from models import ChatHistoryMessage, ChatRequest, ChatResponse, ProductCard, ShopDeps

log = logging.getLogger("campus_customs")

ensure_schema()  # also upgrades the original data-pack database (Problem 2 fixes)
prepare_data.prepare_product_photos()  # one-time white backgrounds for the data pack's photos (Problem 3)
custom.recover_stale()
custom.purge_expired()  # designs are kept 90 days

app = FastAPI(title="Campus Customs API", version="0.3.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(design_agent.router)
app.include_router(custom.router)
app.include_router(custom.bag_router)


@app.middleware("http")
async def revalidate_media(request, call_next):
    # Images can be replaced on disk (e.g. the white-background fix); make browsers
    # re-check with the ETag instead of silently reusing a stale copy.
    response = await call_next(request)
    if request.url.path.startswith("/media/"):
        response.headers["Cache-Control"] = "no-cache"
    return response

# Serve only the image folder, never data/ itself (that would expose the database).
app.mount("/media/products", StaticFiles(directory=DATA_DIR / "products"), name="product-images")
if (DATA_DIR / "dan").exists():
    app.mount("/media/dan", StaticFiles(directory=DATA_DIR / "dan"), name="dan-images")
# Custom Dan Gear: blank product mockups + customers' generated designs (random, unguessable file names).
(DATA_DIR / "custom" / "designs").mkdir(parents=True, exist_ok=True)
app.mount("/media/custom", StaticFiles(directory=DATA_DIR / "custom"), name="custom-images")


@app.get("/api/health")
def health() -> dict:
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0]
    return {"status": "ok", "products": count, "agent_model": agent.AGENT_MODEL,
            "chat_available": config.paid_features_open() and agent.HAS_KEY,
            "paid_features_until": config.PAID_FEATURES_UNTIL or None}


@app.get("/api/categories")
def categories() -> list[dict]:
    counts: dict[str, int] = {}
    for p in load_products():
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    return [{"name": n, "count": counts[n]} for n in CATEGORY_NAMES if n in counts]


@app.get("/api/products")
def list_products(
    q: str | None = Query(None, description="Search name, description, colors, tags"),
    category: str | None = None,
) -> list[dict]:
    products = []
    for p in load_products():
        if category and p["category"] != category:
            continue
        if q:
            haystack = " ".join(
                [p["name"], p["garment_type"], p["description"], *p["colors"], *p["search_tags"]]
            ).lower()
            if not all(word in haystack for word in q.lower().split()):
                continue
        products.append(p)
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    p = load_product(product_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


# --- Chat ---------------------------------------------------------------------------


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Hydrate the agent's product_ids from the database (drops unknown ids, keeps order)."""
    cards, seen = [], set()
    for pid in product_ids:
        if pid in seen:
            continue
        seen.add(pid)
        p = load_product(pid)
        if p:
            cards.append(ProductCard(**{k: p[k] for k in ProductCard.model_fields}))
    return cards


def load_history(user_id: int, limit: int = 40) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, voice, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def save_turn(user_id: int, message: str, reply: str, cards: list[ProductCard], voice: str) -> None:
    products_json = json.dumps([c.model_dump() for c in cards]) if cards else None
    with connect(readonly=False) as conn:
        conn.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, message))
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, voice) VALUES (?, 'assistant', ?, ?, ?)",
            (user_id, reply, products_json, voice),
        )
        conn.commit()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, cc_session: str | None = Cookie(default=None)) -> ChatResponse:
    user = current_user(cc_session)
    # Public demo: the chat costs money, so it has a time window and rate limits (limits.py). A polite reply, not an error.
    if reason := limits.check(request, user):
        return ChatResponse(reply=limits.message(reason, body.voice), products=[], voice=body.voice)
    previous_voice = body.previous_voice
    if user:
        # Signed in: the database is the source of truth for history (survives reloads and logins).
        rows = load_history(user["id"])
        history = [{"role": r["role"], "content": r["content"]} for r in rows]
        previous_voice = next((r["voice"] for r in reversed(rows) if r["role"] == "assistant"), None) or previous_voice
    else:
        history = [t.model_dump() for t in body.history]

    deps = ShopDeps(
        voice=body.voice,
        customer=build_customer(user),  # who is chatting (server-verified)
        page=build_page(body.page),  # what they're looking at (checked against the DB)
        switched_voice=previous_voice is not None and previous_voice != body.voice,
    )
    recent = dan_voice.used_recently([t["content"] for t in history if t["role"] == "assistant"][-6:])
    deps.recent_phrases, deps.suggested_phrase = recent, dan_voice.suggest(recent)
    if body.visitor:
        deps.visitor = re.sub(r"[^\w\s()/:,.'-]", "", body.visitor)[:120].strip() or None
    try:
        out = await agent.ask(body.message.strip(), history, deps)
    except agent.MissingKey as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        log.exception("agent run failed")
        raise HTTPException(status_code=502, detail="The assistant is having trouble right now. Please try again.")

    cards = product_cards(out.product_ids)
    # A drafted custom Dan design is stored server-side; generating it later sends only its id back.
    design = custom.save_brief(out.custom_design, user["id"] if user else None) if out.custom_design else None
    if user:
        save_turn(user["id"], body.message.strip(), out.reply, cards, body.voice)
    return ChatResponse(
        reply=out.reply,
        products=cards,
        results_title=out.results_title if cards else None,
        dan=dan_for_products([c.product_id for c in cards]) if cards else None,
        see_all_category=out.see_all_category,
        design=design,
        go_to=out.go_to,
        voice=body.voice,
    )


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(cc_session: str | None = Cookie(default=None)) -> list[ChatHistoryMessage]:
    user = current_user(cc_session)
    if not user:
        return []
    out = []
    for r in load_history(user["id"]):
        products = [ProductCard(**{k: p.get(k) for k in ProductCard.model_fields}) for p in json.loads(r["products_json"] or "[]")
                    if all(p.get(k) is not None for k in ProductCard.model_fields)]
        voice = r["voice"] if r["voice"] in ("brand", "dan") else None
        out.append(ChatHistoryMessage(role=r["role"], content=r["content"], voice=voice, products=products, created_at=r["created_at"]))
    return out


@app.delete("/api/chat/history")
def clear_chat_history(cc_session: str | None = Cookie(default=None)) -> dict:
    user = current_user(cc_session)
    if not user:
        return {"deleted": 0}
    with connect(readonly=False) as conn:
        n = conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user["id"],)).rowcount
        conn.commit()
    return {"deleted": n}


# --- The built website (web deployment) -------------------------------------------------------------
# When frontend/dist exists (npm run build), this one server also serves the React site, so the whole store runs
# from a single web service. Locally you can still use the Vite dev server on :5173 instead.
FRONTEND_DIST = DATA_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="site-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def site(full_path: str):
        if full_path.startswith(("api/", "media/")):
            raise HTTPException(status_code=404, detail="Not found")
        file = (FRONTEND_DIST / full_path).resolve()
        if full_path and file.is_file() and FRONTEND_DIST.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")  # client-side routes (/products/…, /custom) load the app
