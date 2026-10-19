"""Ask Dan Image Studio — local API + dashboard host.

Run (from ask-dan-image-studio/backend):  .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8765
or double-click ../start.command.  Binds to localhost only.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from studio import config, engine, exports, inventory, state
from studio.prompts import build_prompt

app = FastAPI(title="Ask Dan Image Studio", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    if not config.MANIFEST_PATH.exists():
        inventory.build()
    state.init(engine.reload_manifest())
    recovered = engine.recover_orphans()
    if recovered:
        state.log("recovery", f"registered {recovered} image(s) saved before an interruption")
    engine.start_worker()


def _err(e: Exception) -> HTTPException:
    code = 409 if isinstance(e, (engine.GuardError, state.BadTransition)) else 404 if isinstance(e, KeyError) else 400
    return HTTPException(code, str(e).strip("'\""))


# --- files (allow-listed directories only) ---------------------------------------------------------

ALLOWED_DIRS = [config.ROOT / d for d in ("references", "output/pending_review", "output/approved", "output/rejected",
                                          "output/thumbs", "output/exports", "output/work/catalogue", "output/work/dan_final")]


@app.get("/files/{rel_path:path}")
def files(rel_path: str):
    p = (config.ROOT / rel_path).resolve()
    if not any(d.resolve() in p.parents for d in ALLOWED_DIRS) or not p.is_file():
        raise HTTPException(404, "Not found")
    if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".zip"):
        raise HTTPException(404, "Not found")
    return FileResponse(p, headers={"Cache-Control": "no-cache"})


@app.get("/thumb/{rel_path:path}")
def thumb(rel_path: str):
    """Small cached JPEG preview of an allow-listed image (grids load fast; originals untouched)."""
    import hashlib
    from PIL import Image
    p = (config.ROOT / rel_path).resolve()
    if not any(d.resolve() in p.parents for d in ALLOWED_DIRS) or not p.is_file() or p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise HTTPException(404, "Not found")
    key = hashlib.sha1(f"{p}:{p.stat().st_mtime_ns}".encode()).hexdigest()
    out = config.THUMB_DIR / "cache" / f"{key}.jpg"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(p)
        im = im.convert("RGBA") if im.mode in ("P", "LA") else im
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (238, 243, 249))
            bg.paste(im, mask=im.getchannel("A"))
            im = bg
        im = im.convert("RGB")
        im.thumbnail((320, 320))
        im.save(out, "JPEG", quality=82)
    return FileResponse(out, headers={"Cache-Control": "max-age=3600"})


# --- read endpoints --------------------------------------------------------------------------------


@app.get("/api/overview")
def overview():
    return engine.overview()


@app.get("/api/inventory")
def inventory_view():
    m = engine.manifest()
    return {k: m[k] for k in ("inputs", "missing_inputs", "counts", "previous_audit_counts", "discrepancies", "dan_files", "references")}


@app.get("/api/products")
def products():
    m = engine.manifest()
    states = state.all_asset_states()
    return [{**p, "dan_status": states[p["dan_asset_id"]]["status"]} for p in m["products"]]


@app.get("/api/assets")
def assets():
    m = engine.manifest()
    states = state.all_asset_states()
    return [{**a, **{k: v for k, v in states[a["asset_id"]].items() if k != "asset_id"}, "manifest_status": a["status"]}
            for a in m["assets"]]


@app.get("/api/assets/{asset_id}")
def asset(asset_id: str):
    try:
        a = engine.asset_def(asset_id)
        st = state.asset_state(asset_id)
        shield = engine.shield_for(a, st)
        refs = engine.dan_references()
        return {**a, **st, "manifest_status": a["status"],
                "dan_reference_paths": [str(p.relative_to(config.ROOT)) for p in refs],
                "shield_path_effective": str(shield.relative_to(config.ROOT)) if shield else None,
                "prompt_preview": build_prompt(a, has_shield=bool(shield), override=st.get("prompt_override")),
                "estimate_usd": engine.estimate_for(asset_id)}
    except Exception as e:
        raise _err(e)


# --- generation & review -----------------------------------------------------------------------------


class GenerateIn(BaseModel):
    feedback: str | None = Field(default=None, max_length=2000)
    parent_version: int | None = None
    provider: str | None = None  # default: settings.provider


@app.post("/api/assets/{asset_id}/generate")
def generate(asset_id: str, body: GenerateIn):
    try:
        kind = "revise" if body.parent_version else "generate"
        job = engine.enqueue(asset_id, kind, body.feedback, body.parent_version, body.provider)
        return {"job_id": job}
    except Exception as e:
        raise _err(e)


class ReviewIn(BaseModel):
    version: int
    text: str = Field(default="", max_length=2000)


@app.post("/api/assets/{asset_id}/approve")
def approve(asset_id: str, body: ReviewIn):
    try:
        return engine.approve(asset_id, body.version)
    except Exception as e:
        raise _err(e)


@app.post("/api/assets/{asset_id}/reject")
def reject(asset_id: str, body: ReviewIn):
    try:
        return engine.reject(asset_id, body.version, body.text)
    except Exception as e:
        raise _err(e)


@app.post("/api/assets/{asset_id}/revise")
def revise(asset_id: str, body: ReviewIn):
    """Record feedback (free). Generating the revision is a separate, guarded call."""
    try:
        return engine.request_revision(asset_id, body.version, body.text)
    except Exception as e:
        raise _err(e)


class NoteIn(BaseModel):
    notes: str | None = None
    prompt_override: str | None = None
    shield_override: str | None = None
    status: str | None = None


@app.post("/api/assets/{asset_id}/meta")
def asset_meta(asset_id: str, body: NoteIn):
    try:
        with state.db() as c:
            for col in ("notes", "prompt_override", "shield_override"):
                val = getattr(body, col)
                if val is not None:
                    c.execute(f"UPDATE assets SET {col}=? WHERE asset_id=?", (val or None, asset_id))
            if body.status:
                state.set_status(asset_id, body.status, c)
        return state.asset_state(asset_id)
    except Exception as e:
        raise _err(e)


class CompositeIn(BaseModel):
    version: int
    cx: float = Field(ge=0, le=1)
    cy: float = Field(ge=0, le=1)
    width_frac: float = Field(ge=0.03, le=0.6)
    rotation: float = Field(default=0, ge=-45, le=45)
    shield_slug: str | None = None
    occlusion: bool = True  # keep warm foreground objects (pumpkin, scarf, fur) in front of the shield
    fabric: float = Field(default=0.85, ge=0, le=1)  # how much knit texture/shading shows through


@app.post("/api/assets/{asset_id}/composite")
def composite(asset_id: str, body: CompositeIn):
    try:
        return engine.composite(asset_id, body.version, body.cx, body.cy, body.width_frac, body.rotation, body.shield_slug,
                                body.occlusion, body.fabric)
    except Exception as e:
        raise _err(e)


# --- batch control / authorizations -------------------------------------------------------------------


class AuthIn(BaseModel):
    budget_usd: float = Field(gt=0, le=200)
    asset_ids: list[str] = []
    confirm: bool = False


@app.post("/api/authorize/pilot")
def authorize_pilot(body: AuthIn):
    if not body.confirm:
        raise HTTPException(400, "Explicit confirmation required")
    try:
        aid = engine.authorize_pilot(body.budget_usd)
        state.log("authorization", f"PILOT authorized: 3 images, budget ${body.budget_usd:.2f}")
        return {"authorization_id": aid}
    except Exception as e:
        raise _err(e)


@app.post("/api/authorize/batch")
def authorize_batch(body: AuthIn):
    if not body.confirm:
        raise HTTPException(400, "Explicit confirmation required")
    try:
        aid = engine.authorize_batch(body.asset_ids, body.budget_usd)
        state.log("authorization", f"BATCH authorized: {', '.join(body.asset_ids)} (budget ${body.budget_usd:.2f})")
        return {"authorization_id": aid}
    except Exception as e:
        raise _err(e)


@app.post("/api/authorize/single")
def authorize_single(body: AuthIn):
    if not body.confirm or len(body.asset_ids) != 1:
        raise HTTPException(400, "Explicit confirmation for exactly one asset required")
    try:
        aid = engine.authorize_single(body.asset_ids[0], body.budget_usd)
        state.log("authorization", f"SINGLE paid image authorized for {body.asset_ids[0]} (budget ${body.budget_usd:.2f})", body.asset_ids[0])
        return {"authorization_id": aid}
    except Exception as e:
        raise _err(e)


@app.post("/api/authorize/revoke")
def revoke():
    state.revoke_authorizations()
    state.log("authorization", "all active authorizations revoked")
    return {"ok": True}


class BatchIn(BaseModel):
    asset_ids: list[str]
    provider: str | None = None


@app.post("/api/batch/start")
def batch_start(body: BatchIn):
    if not 1 <= len(body.asset_ids) <= config.BATCH_MAX:
        raise HTTPException(400, f"Batches are 1–{config.BATCH_MAX} assets")
    queued, errors = [], {}
    for aid in body.asset_ids:
        try:
            queued.append(engine.enqueue(aid, "generate", provider=body.provider))
        except Exception as e:
            errors[aid] = str(e)
    return {"queued": queued, "errors": errors}


@app.post("/api/batch/pause")
def batch_pause():
    engine.pause(True)
    return {"paused": True}


@app.post("/api/batch/resume")
def batch_resume():
    engine.pause(False)
    return {"paused": False}


@app.post("/api/batch/stop")
def batch_stop():
    return {"cancelled": engine.stop()}


@app.get("/api/jobs")
def jobs():
    with state.db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 50")]


# --- settings ------------------------------------------------------------------------------------


@app.get("/api/settings")
def get_settings():
    from studio.providers.openai_images import key_status
    s = state.get_settings()
    m = engine.manifest()
    return {"settings": s, "key": key_status(), "pilot_assets": config.PILOT_ASSETS, "batch_max": config.BATCH_MAX,
            "dan_reference_candidates": [d for d in m["dan_files"] if d["disposition"] in ("mapped", "out_of_scope")],
            "dan_references_default": m["references"]["dan_references"], "shields": m["references"]["shields"],
            "output_dir": str(config.ROOT / "output")}


class SettingsIn(BaseModel):
    provider: str | None = Field(default=None, pattern="^(mock|openai)$")
    model: str | None = Field(default=None, pattern="^gpt-image-[0-9a-z.\\-]+$")
    size: str | None = Field(default=None, pattern="^(1024x1024|1536x1536|2048x2048)$")
    quality: str | None = Field(default=None, pattern="^(low|medium|high|xhigh|max)$")
    cost_cap_usd: float | None = Field(default=None, ge=0, le=500)
    per_job_cap_usd: float | None = Field(default=None, ge=0, le=10)
    max_attempts_per_asset: int | None = Field(default=None, ge=1, le=10)
    batch_size: int | None = Field(default=None, ge=1, le=5)
    references_confirmed: bool | None = None
    shields_confirmed: bool | None = None
    dan_reference_files: list[str] | None = None
    automatic_mode: bool | None = None


@app.post("/api/settings")
def set_settings(body: SettingsIn):
    data = body.model_dump(exclude_none=True)
    if "dan_reference_files" in data:
        bad = [p for p in data["dan_reference_files"] if "dan2" in Path(p).name.lower()]
        if bad:
            raise HTTPException(400, f"Dan2 images are deprecated and can't be references: {bad}")
        data["dan_reference_files"] = [p for p in data["dan_reference_files"] if (config.ROOT / p).exists()]
    for k, v in data.items():
        state.set_setting(k, v)
    state.log("settings", ", ".join(f"{k}={v}" for k, v in data.items() if k != "dan_reference_files"))
    return get_settings()


# --- inventory rebuild & export ----------------------------------------------------------------------


@app.post("/api/inventory/rebuild")
def rebuild():
    m = inventory.build()
    state.init(engine.reload_manifest())
    return {"counts": m["counts"]}


# --- chat & one-off images -------------------------------------------------------------------------


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    focus_asset: str | None = None


@app.get("/api/chat")
def chat_history():
    from studio import chat_agent
    return chat_agent.history()


@app.post("/api/chat")
async def chat(body: ChatIn):
    from studio import chat_agent
    try:
        return await chat_agent.respond(body.message.strip(), body.focus_asset, engine.manifest(), state.all_asset_states())
    except Exception as e:
        raise HTTPException(502, f"Chat agent unavailable: {str(e)[:300]}")


@app.delete("/api/chat")
def chat_clear():
    with state.db() as c:
        c.execute("DELETE FROM chat_messages")
    return {"ok": True}


class BriefIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    setting: str = Field(max_length=600)
    outfit: str = Field(max_length=600)
    pose: str = Field(max_length=600)
    humor: str = Field(max_length=600)
    permitted_text: list[str] = Field(default_factory=list, max_length=8)
    shield_slug: str | None = None


@app.post("/api/custom")
def create_custom(body: BriefIn):
    try:
        a = engine.create_custom_asset(body.model_dump())
        from studio import chat_agent
        chat_agent.save("system", f"Created one-off asset {a['asset_id']} ({a['display_name']})", asset_id=a["asset_id"])
        return a
    except Exception as e:
        raise _err(e)


class ConfirmIn(BaseModel):
    confirm: bool = False


@app.post("/api/admin/clear-mock")
def clear_mock(body: ConfirmIn):
    if not body.confirm:
        raise HTTPException(400, "Explicit confirmation required")
    return engine.clear_mock_results()


@app.post("/api/export")
def export():
    try:
        return exports.export_all()
    except Exception as e:
        raise _err(e)


# --- dashboard (built React app) --------------------------------------------------------------------

if config.FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=config.FRONTEND_DIST / "assets"), name="ui-assets")


@app.get("/{path:path}", response_class=HTMLResponse)
def spa(path: str):
    index = config.FRONTEND_DIST / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>Ask Dan Image Studio</h1><p>Dashboard not built yet: run <code>npm run build</code> in frontend/.</p>")
