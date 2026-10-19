"""Job queue, paid-request guards, review actions. One background worker, one job at a time.

Paid requests are allowed ONLY when every guard passes:
  provider=openai, key present, Dan references confirmed by the user, an active user authorization
  that names this asset and has images + budget left, the hard cumulative cap, the per-job cap,
  and the per-asset attempt limit. Guards run at enqueue time AND again right before submitting.
"""

from __future__ import annotations

import json
import shutil
import threading
import time
from pathlib import Path

from . import config, state
from .composite import composite_shield
from .prompts import build_prompt
from .providers.base import GenRequest, ProviderError
from .providers.openai_images import get_provider, key_status
from .qa import check_png, thumbnail

DAN_REFS_PER_REQUEST = 4


class GuardError(Exception):
    pass


# --- manifest -----------------------------------------------------------------------------------

_manifest: dict | None = None


def manifest() -> dict:
    """Catalogue manifest (from inventory) + one-off custom assets created in chat."""
    global _manifest
    if _manifest is None:
        _manifest = json.loads(config.MANIFEST_PATH.read_text())
    m = dict(_manifest)
    m["assets"] = list(_manifest["assets"]) + custom_assets()
    return m


def custom_assets() -> list[dict]:
    try:
        with state.db() as c:
            rows = c.execute("SELECT asset_id, brief FROM custom_assets ORDER BY created_at").fetchall()
    except Exception:  # state not initialised yet
        return []
    out = []
    for r in rows:
        b = json.loads(r["brief"])
        out.append({
            "asset_id": r["asset_id"], "group": "Custom", "category": b.get("display_name", r["asset_id"]),
            "display_name": b.get("display_name", r["asset_id"]), "product_ids": [], "product_count": 0,
            "canonical_filename": f"{r['asset_id']}.png", "existing_files": [], "status": "MISSING", "pilot": False,
            "custom": True, "shield_slug": b.get("shield_slug"),
            "shield_path": f"references/shields/{b['shield_slug']}.png" if b.get("shield_slug") else None,
            "setting": b.get("setting"), "outfit": b.get("outfit"), "pose": b.get("pose"), "humor": b.get("humor"),
            "permitted_text": b.get("permitted_text") or [], "qa_warnings": [],
        })
    return out


def create_custom_asset(brief: dict) -> dict:
    """Register a one-off asset from a chat brief. Shield must be one of the supplied shields (or none)."""
    import re as _re
    shields = {s["slug"] for s in _manifest_raw()["references"]["shields"]}
    slug = brief.get("shield_slug") or None
    if slug and slug not in shields:
        raise GuardError(f"Unknown shield '{slug}': only supplied shields can be used (no invented heraldry).")
    base = "dan_custom_" + (_re.sub(r"[^a-z0-9]+", "_", (brief.get("display_name") or "image").lower()).strip("_")[:40] or "image")
    existing = {a["asset_id"] for a in manifest()["assets"]}
    aid, n = base, 2
    while aid in existing:
        aid, n = f"{base}_{n}", n + 1
    clean = {k: brief.get(k) for k in ("display_name", "setting", "outfit", "pose", "humor", "permitted_text")}
    clean["permitted_text"] = [str(w)[:40] for w in (clean.get("permitted_text") or [])][:8]
    clean["shield_slug"] = slug
    with state.db() as c:
        c.execute("INSERT INTO custom_assets (asset_id, brief, created_at) VALUES (?, ?, ?)", (aid, json.dumps(clean), time.time()))
        c.execute("INSERT OR IGNORE INTO assets (asset_id, status, updated_at) VALUES (?, 'MISSING', ?)", (aid, time.time()))
    state.log("custom", f"one-off asset created: {clean.get('display_name')}", aid)
    return asset_def(aid)


def _manifest_raw() -> dict:
    manifest()
    return _manifest


def reload_manifest() -> dict:
    global _manifest
    _manifest = None
    return manifest()


def asset_def(asset_id: str) -> dict:
    a = next((x for x in manifest()["assets"] if x["asset_id"] == asset_id), None)
    if a is None:
        raise KeyError(f"Unknown asset {asset_id}")
    return a


def shield_for(asset: dict, st: dict) -> Path | None:
    slug = st.get("shield_override") or asset.get("shield_slug")
    if not slug or slug == "none":
        return None
    p = config.REF_SHIELD_DIR / f"{slug}.png"
    return p if p.exists() else None


def dan_references() -> list[Path]:
    settings = state.get_settings()
    chosen = settings.get("dan_reference_files") or [r["path"] for r in manifest()["references"]["dan_references"]]
    paths = [config.ROOT / p for p in chosen if "dan2" not in Path(p).name.lower()]
    return [p for p in paths if p.exists()][:DAN_REFS_PER_REQUEST]


def build_request(asset_id: str, kind: str, feedback: str | None, parent_version: int | None, settings: dict) -> GenRequest:
    a = asset_def(asset_id)
    st = state.asset_state(asset_id)
    refs = dan_references()
    shield = shield_for(a, st)
    if kind == "revise" and parent_version:
        v = next((x for x in st["versions"] if x["version"] == parent_version), None)
        if v:
            refs = [config.ROOT / v["path"]] + refs[:3]
    if shield:
        refs = refs + [shield]
    prompt = build_prompt(a, feedback=feedback, has_shield=bool(shield), is_revision=(kind == "revise"),
                          override=st.get("prompt_override"))
    return GenRequest(asset_id=asset_id, prompt=prompt, references=refs, size=settings["size"],
                      quality=settings["quality"], model=settings["model"])


# --- cost estimates -------------------------------------------------------------------------------

CALIBRATION_MARGIN = 1.25


def estimate(req: GenRequest) -> float:
    """Average ACTUAL cost of past paid images at the same model/size/quality (+25% margin);
    falls back to the provider's conservative token formula until real usage exists."""
    with state.db() as c:
        rows = c.execute("SELECT cost_usd, settings FROM versions WHERE provider='openai' AND cost_is_estimate=0").fetchall()
    same = [r["cost_usd"] for r in rows if json.loads(r["settings"] or "{}") == {"size": req.size, "quality": req.quality, "model": req.model}]
    if same:
        return round(sum(same) / len(same) * CALIBRATION_MARGIN, 4)
    return get_provider("openai").estimate(req)


# --- guards -------------------------------------------------------------------------------------


def pilot_complete() -> bool:
    """All three pilot assets have a reviewed (approved/rejected) paid version."""
    with state.db() as c:
        n = c.execute(
            f"SELECT COUNT(DISTINCT asset_id) FROM versions WHERE provider='openai' AND decision IN ('approved','rejected','superseded') "
            f"AND asset_id IN ({','.join('?' * len(config.PILOT_ASSETS))})", config.PILOT_ASSETS).fetchone()[0]
    return n == len(config.PILOT_ASSETS)


def check_paid_guards(asset_id: str, est: float, settings: dict) -> dict:
    ok, why = get_provider("openai").available()
    if not ok:
        raise GuardError(why)
    if not settings.get("references_confirmed"):
        raise GuardError("Confirm the Dan identity references in Settings before any paid generation.")
    spent = state.total_spent()
    if spent + est > settings["cost_cap_usd"] + 1e-9:
        raise GuardError(f"Hard spending cap: ${spent:.2f} spent + ${est:.2f} estimate > cap ${settings['cost_cap_usd']:.2f}")
    if est > settings["per_job_cap_usd"] + 1e-9:
        raise GuardError(f"Per-image estimate ${est:.2f} exceeds per-job cap ${settings['per_job_cap_usd']:.2f}")
    st = state.asset_state(asset_id)
    paid_attempts = sum(1 for v in st["versions"] if v["provider"] == "openai")
    if paid_attempts >= settings["max_attempts_per_asset"]:
        raise GuardError(f"{asset_id}: reached max attempts ({settings['max_attempts_per_asset']})")
    auth = state.find_authorization(asset_id, est)
    if auth is None:
        raise GuardError(f"No active authorization covers a paid request for {asset_id} (~${est:.2f}). Authorize it first.")
    return auth


def estimate_for(asset_id: str, kind: str = "generate") -> float:
    s = state.get_settings()
    req = build_request(asset_id, kind, None, 1 if kind == "revise" else None, s)
    return estimate(req)


# --- enqueue ------------------------------------------------------------------------------------


def enqueue(asset_id: str, kind: str = "generate", feedback: str | None = None, parent_version: int | None = None,
            provider: str | None = None) -> int:
    settings = state.get_settings()
    provider = provider or settings["provider"]
    asset_def(asset_id)
    with state.db() as c:
        busy = c.execute("SELECT id FROM jobs WHERE asset_id=? AND status IN ('queued','running')", (asset_id,)).fetchone()
        if busy:
            raise GuardError(f"{asset_id} already has a job in progress (#{busy['id']})")
    est, auth_id = 0.0, None
    if provider == "openai":
        req = build_request(asset_id, kind, feedback, parent_version, settings)
        est = estimate(req)
        auth_id = check_paid_guards(asset_id, est, settings)["id"]
    nv = state.next_version(asset_id)
    with state.db() as c:  # attempt counter: a retry after a FAILED job (no version produced) is a new request
        n_jobs = c.execute("SELECT COUNT(*) FROM jobs WHERE asset_id=?", (asset_id,)).fetchone()[0]
    key = f"{asset_id}:v{nv}:{kind}:{provider}:j{n_jobs + 1}"
    with state.db() as c:
        cur = c.execute(
            "INSERT OR IGNORE INTO jobs (idem_key, asset_id, kind, provider, parent_version, feedback, authorization_id, status, est_cost, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)",
            (key, asset_id, kind, provider, parent_version, feedback, auth_id, est, time.time()))
        if cur.rowcount == 0:
            raise GuardError(f"Duplicate request ignored ({key})")
        state.set_status(asset_id, "QUEUED", c)
        job_id = cur.lastrowid
    state.log("queued", f"{kind} via {provider}" + (f" (est ${est:.2f})" if est else ""), asset_id)
    _wake.set()
    return job_id


# --- worker -------------------------------------------------------------------------------------

_wake = threading.Event()
_worker: threading.Thread | None = None
_current: dict = {}


def current_job() -> dict:
    return dict(_current)


def _run_job(job: dict) -> None:
    asset_id, settings = job["asset_id"], state.get_settings()
    provider = get_provider(job["provider"])
    with state.db() as c:
        c.execute("UPDATE jobs SET status='running', started_at=? WHERE id=?", (time.time(), job["id"]))
        state.set_status(asset_id, "GENERATING", c)
    _current.update(job_id=job["id"], asset_id=asset_id, provider=job["provider"], started=time.time())
    try:
        req = build_request(asset_id, job["kind"], job["feedback"], job["parent_version"], settings)
        if provider.paid:  # re-check every guard right before spending
            auth = check_paid_guards(asset_id, estimate(req), settings)
            if auth["id"] != job["authorization_id"]:
                job["authorization_id"] = auth["id"]
        result = provider.generate(req)
        a = asset_def(asset_id)
        version = state.next_version(asset_id)
        fname = f"{asset_id}_v{version:02d}.png"
        with state.db() as c:
            known = {r[0] for r in c.execute("SELECT sha256 FROM versions WHERE asset_id=?", (asset_id,))}
        qa = check_png(result.png_bytes, fname, known, bool(a.get("shield_slug")))
        path = config.PENDING_DIR / fname
        tmp = path.with_suffix(".part")
        tmp.write_bytes(result.png_bytes)
        tmp.replace(path)  # atomic: a half-written file is never visible
        thumb = config.THUMB_DIR / f"{asset_id}_v{version:02d}.jpg"
        thumbnail(result.png_bytes, thumb)
        with state.db() as c:
            c.execute(
                "INSERT INTO versions (asset_id, version, parent_version, kind, provider, model, settings, prompt, references_json, feedback, "
                "path, thumb, sha256, width, height, cost_usd, cost_is_estimate, usage_json, qa_json, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (asset_id, version, job["parent_version"], job["kind"], provider.name, result.model,
                 json.dumps({k: settings[k] for k in ("size", "quality", "model")}), req.prompt,
                 json.dumps([str(Path(p).relative_to(config.ROOT)) for p in req.references]), job["feedback"],
                 str(path.relative_to(config.ROOT)), str(thumb.relative_to(config.ROOT)), qa.get("sha256"),
                 qa.get("width"), qa.get("height"), result.cost_usd, int(result.cost_is_estimate),
                 json.dumps(result.usage), json.dumps(qa), time.time()))
            c.execute("UPDATE jobs SET status='done', finished_at=?, version=? WHERE id=?", (time.time(), version, job["id"]))
            c.execute("UPDATE assets SET attempts=attempts+1 WHERE asset_id=?", (asset_id,))
            state.set_status(asset_id, "PENDING_REVIEW", c)
        if provider.paid and job["authorization_id"]:
            state.consume_authorization(job["authorization_id"], result.cost_usd)
        state.log("generated", f"v{version} via {provider.name}" + (f" — ${result.cost_usd:.3f}{' (est.)' if result.cost_is_estimate else ''}" if provider.paid else " (mock, $0)")
                  + ("" if qa["ok"] else f" — QA: {'; '.join(qa['errors'])}"), asset_id)
    except Exception as e:  # GuardError, ProviderError, anything: record, never retry silently
        with state.db() as c:
            c.execute("UPDATE jobs SET status='failed', error=?, finished_at=? WHERE id=?", (str(e)[:800], time.time(), job["id"]))
            state.set_status(asset_id, "FAILED", c)
        state.log("error", str(e)[:300], asset_id)
    finally:
        _current.clear()


def _loop() -> None:
    while True:
        _wake.wait(timeout=2)
        _wake.clear()
        while True:
            if state.get_settings().get("paused"):
                break
            with state.db() as c:
                row = c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
            if row is None:
                break
            _run_job(dict(row))


def start_worker() -> None:
    global _worker
    if _worker is None or not _worker.is_alive():
        _worker = threading.Thread(target=_loop, name="studio-worker", daemon=True)
        _worker.start()


def run_pending_sync() -> None:
    """Tests: process the queue synchronously."""
    while True:
        with state.db() as c:
            row = c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        if row is None or state.get_settings().get("paused"):
            return
        _run_job(dict(row))


def pause(on: bool) -> None:
    state.set_setting("paused", on)
    state.log("control", "paused" if on else "resumed")
    if not on:
        _wake.set()


def stop() -> int:
    with state.db() as c:
        rows = c.execute("SELECT asset_id FROM jobs WHERE status='queued'").fetchall()
        c.execute("UPDATE jobs SET status='cancelled', finished_at=? WHERE status='queued'", (time.time(),))
        for r in rows:
            prev = c.execute("SELECT COUNT(*) FROM versions WHERE asset_id=?", (r["asset_id"],)).fetchone()[0]
            c.execute("UPDATE assets SET status=? WHERE asset_id=?", ("PENDING_REVIEW" if prev else "MISSING", r["asset_id"]))
    state.log("control", f"stopped: {len(rows)} queued job(s) cancelled")
    return len(rows)


def recover_orphans() -> int:
    """A generated file whose DB row was never written (crash right after saving) is registered, not regenerated."""
    n = 0
    with state.db() as c:
        known = {r[0] for r in c.execute("SELECT path FROM versions")}
    for f in sorted(config.PENDING_DIR.glob("dan_*_v*.png")):
        rel = str(f.relative_to(config.ROOT))
        if rel in known:
            continue
        asset_id, v = f.stem.rsplit("_v", 1)
        try:
            asset_def(asset_id)
        except KeyError:
            continue
        data = f.read_bytes()
        thumb = config.THUMB_DIR / f"{f.stem}.jpg"
        thumbnail(data, thumb)
        with state.db() as c:
            c.execute("INSERT OR IGNORE INTO versions (asset_id, version, kind, provider, path, thumb, cost_usd, cost_is_estimate, "
                      "qa_json, created_at) VALUES (?, ?, 'recovered', 'unknown', ?, ?, 0, 1, ?, ?)",
                      (asset_id, int(v), rel, str(thumb.relative_to(config.ROOT)),
                       json.dumps({"warnings": ["Recovered after interruption; cost unknown"]}), time.time()))
            c.execute("UPDATE assets SET status='PENDING_REVIEW' WHERE asset_id=? AND status IN ('FAILED','MISSING','QUEUED')", (asset_id,))
        n += 1
    return n


# --- review actions -----------------------------------------------------------------------------


def _version(asset_id: str, version: int) -> dict:
    st = state.asset_state(asset_id)
    v = next((x for x in st["versions"] if x["version"] == version), None)
    if v is None:
        raise KeyError(f"{asset_id} v{version} not found")
    return v


def approve(asset_id: str, version: int) -> dict:
    v = _version(asset_id, version)
    src = config.ROOT / v["path"]
    vdir = config.APPROVED_DIR / "versions"
    vdir.mkdir(exist_ok=True)
    shutil.copy2(src, vdir / src.name)  # immutable per-version copy
    tmp = config.APPROVED_DIR / f".{asset_id}.png.part"
    shutil.copy2(src, tmp)
    tmp.replace(config.APPROVED_DIR / f"{asset_id}.png")  # canonical deliverable
    with state.db() as c:
        c.execute("UPDATE versions SET decision='superseded' WHERE asset_id=? AND decision='approved' AND version<>?", (asset_id, version))
        c.execute("UPDATE versions SET decision='approved' WHERE asset_id=? AND version=?", (asset_id, version))
        c.execute("UPDATE assets SET approved_version=? WHERE asset_id=?", (version, asset_id))
        state.set_status(asset_id, "APPROVED", c)
    state.add_feedback(asset_id, version, "approve", "")
    state.log("approved", f"v{version} approved", asset_id)
    return state.asset_state(asset_id)


def reject(asset_id: str, version: int, reason: str) -> dict:
    v = _version(asset_id, version)
    src = config.ROOT / v["path"]
    shutil.copy2(src, config.REJECTED_DIR / src.name)  # preserved, never deleted
    with state.db() as c:
        c.execute("UPDATE versions SET decision='rejected' WHERE asset_id=? AND version=?", (asset_id, version))
        a = c.execute("SELECT approved_version FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
        if a["approved_version"] == version:
            c.execute("UPDATE assets SET approved_version=NULL WHERE asset_id=?", (asset_id,))
        state.set_status(asset_id, "APPROVED" if a["approved_version"] and a["approved_version"] != version else "REJECTED", c)
    state.add_feedback(asset_id, version, "reject", reason)
    state.log("rejected", f"v{version}: {reason or '(no reason)'}", asset_id)
    return state.asset_state(asset_id)


def request_revision(asset_id: str, version: int, feedback: str) -> dict:
    _version(asset_id, version)
    state.add_feedback(asset_id, version, "revise", feedback)
    with state.db() as c:
        state.set_status(asset_id, "REVISION_REQUESTED", c)
    state.log("revision", f"on v{version}: {feedback[:120]}", asset_id)
    return state.asset_state(asset_id)


def composite(asset_id: str, version: int, cx: float, cy: float, width_frac: float, rotation: float = 0.0,
              shield_slug: str | None = None, occlusion: bool = True, fabric: float = 0.85) -> dict:
    a = asset_def(asset_id)
    st = state.asset_state(asset_id)
    slug = shield_slug or st.get("shield_override") or a.get("shield_slug")
    shield = config.REF_SHIELD_DIR / f"{slug}.png" if slug else None
    if not shield or not shield.exists():
        raise GuardError("No supplied shield for this asset; compositing refused (no invented heraldry).")
    v = _version(asset_id, version)
    data = composite_shield((config.ROOT / v["path"]).read_bytes(), shield, cx, cy, width_frac, rotation,
                            occlusion=occlusion, fabric=fabric)
    nv = state.next_version(asset_id)
    fname = f"{asset_id}_v{nv:02d}.png"
    path = config.PENDING_DIR / fname
    path.write_bytes(data)
    thumb = config.THUMB_DIR / f"{asset_id}_v{nv:02d}.jpg"
    thumbnail(data, thumb)
    qa = check_png(data, fname, set(), True)
    qa["warnings"].insert(0, f"Exact supplied shield '{slug}' composited (original pixels) at x={cx:.2f}, y={cy:.2f}, w={width_frac:.2f}")
    with state.db() as c:
        c.execute("INSERT INTO versions (asset_id, version, parent_version, kind, provider, model, settings, path, thumb, sha256, "
                  "width, height, cost_usd, cost_is_estimate, qa_json, feedback, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,0,?,?,?)",
                  (asset_id, nv, version, "composite", "local", "pillow",
                   json.dumps({"cx": cx, "cy": cy, "width_frac": width_frac, "rotation": rotation, "shield": slug,
                               "occlusion": occlusion, "fabric": fabric}),
                   str(path.relative_to(config.ROOT)), str(thumb.relative_to(config.ROOT)), qa.get("sha256"),
                   qa.get("width"), qa.get("height"), json.dumps(qa), f"composite shield {slug}", time.time()))
        state.set_status(asset_id, "PENDING_REVIEW", c)
    state.log("composite", f"v{nv} = v{version} + exact {slug} shield", asset_id)
    return state.asset_state(asset_id)


# --- authorizations ------------------------------------------------------------------------------


def authorize_pilot(budget_usd: float) -> int:
    if any(a["kind"] == "pilot" for a in state.authorizations()):
        raise GuardError("The three-image pilot was already authorized once.")
    return state.create_authorization("pilot", list(config.PILOT_ASSETS), 3, budget_usd, "Phase 1 pilot: exactly three images")


def authorize_batch(asset_ids: list[str], budget_usd: float) -> int:
    if not pilot_complete():
        raise GuardError("Review all three pilot images (approve or reject each) before authorizing a batch.")
    if not 1 <= len(asset_ids) <= config.BATCH_MAX:
        raise GuardError(f"A supervised batch is 1–{config.BATCH_MAX} assets.")
    return state.create_authorization("batch", asset_ids, len(asset_ids), budget_usd, "Supervised batch")


def authorize_single(asset_id: str, budget_usd: float) -> int:
    if not any(a["kind"] == "pilot" for a in state.authorizations()):
        raise GuardError("Authorize the three-image pilot first.")
    return state.create_authorization("single", [asset_id], 1, budget_usd, "Single paid generation/revision")


# --- overview -----------------------------------------------------------------------------------


def overview() -> dict:
    m = manifest()
    states = state.all_asset_states()
    settings = state.get_settings()
    counts: dict[str, int] = {}
    for s in states.values():
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    scoped = [a["asset_id"] for a in m["assets"] if a["status"] == "MISSING" and not a.get("custom")]
    approved_new = sum(1 for aid in scoped if states[aid]["status"] == "APPROVED")
    spent = state.total_spent()
    with state.db() as c:
        est_spend = c.execute("SELECT COALESCE(SUM(cost_usd),0) FROM versions WHERE cost_is_estimate=1 AND provider='openai'").fetchone()[0]
    s = settings
    per = estimate_for(config.PILOT_ASSETS[0]) if manifest() else 0
    return {
        "counts": m["counts"], "previous_audit_counts": m["previous_audit_counts"], "status_counts": counts,
        "scoped_total": len(scoped), "scoped_approved": approved_new,
        "pending_review": sum(1 for aid in scoped if states[aid]["status"] == "PENDING_REVIEW"),
        "spent_usd": round(spent, 4), "spent_includes_estimates_usd": round(est_spend, 4),
        "cost_cap_usd": s["cost_cap_usd"], "remaining_budget_usd": round(s["cost_cap_usd"] - spent, 4),
        "estimates": {"per_image": per, "pilot_3": round(per * 3, 2), "first_pass_35": round(per * len(scoped), 2),
                      "worst_case": round(per * len(scoped) * s["max_attempts_per_asset"], 2)},
        "pilot_complete": pilot_complete(),
        "custom_count": sum(1 for a in m["assets"] if a.get("custom")),
        "provider": s["provider"], "key": key_status(), "paused": bool(s.get("paused")),
        "references_confirmed": bool(s.get("references_confirmed")),
        "current_job": current_job(),
        "authorizations": state.authorizations(active_only=True),
        "events": state.recent_events(25),
        "discrepancies": m["discrepancies"],
    }


# --- mock demo cleanup -----------------------------------------------------------------------------


def is_mock_derived(asset_id: str, version: int) -> bool:
    """True if this version is a mock placeholder or was composited from one."""
    with state.db() as c:
        seen = set()
        while version and version not in seen:
            seen.add(version)
            r = c.execute("SELECT provider, parent_version FROM versions WHERE asset_id=? AND version=?", (asset_id, version)).fetchone()
            if r is None:
                return False
            if r["provider"] == "mock":
                return True
            if r["provider"] != "local":
                return False
            version = r["parent_version"]
    return False


def clear_mock_results() -> dict:
    """Archive and remove every mock-derived version so real generation starts clean. Paid images are never touched."""
    archive = config.REJECTED_DIR / "mock_demo"
    archive.mkdir(parents=True, exist_ok=True)
    removed: dict[str, int] = {}
    m = manifest()
    with state.db() as c:
        rows = [dict(r) for r in c.execute("SELECT asset_id, version, path, thumb FROM versions ORDER BY asset_id, version")]
    # Decide first: deleting a parent before checking its composite child would hide the mock origin.
    doomed = [r for r in rows if is_mock_derived(r["asset_id"], r["version"])]
    for r in doomed:
        p = config.ROOT / r["path"]
        if p.exists():
            shutil.move(str(p), archive / p.name)
        for extra in (config.APPROVED_DIR / "versions" / p.name, config.REJECTED_DIR / p.name):
            if extra.exists():
                extra.unlink()
        removed[r["asset_id"]] = removed.get(r["asset_id"], 0) + 1
        with state.db() as c:
            c.execute("DELETE FROM versions WHERE asset_id=? AND version=?", (r["asset_id"], r["version"]))
            c.execute("DELETE FROM feedback WHERE asset_id=? AND version=?", (r["asset_id"], r["version"]))
    for aid in removed:
        base = next((a["status"] for a in m["assets"] if a["asset_id"] == aid), "MISSING")
        with state.db() as c:
            left = c.execute("SELECT version, decision FROM versions WHERE asset_id=? ORDER BY version", (aid,)).fetchall()
            approved = next((v["version"] for v in left if v["decision"] == "approved"), None)
            status = "APPROVED" if approved else ("PENDING_REVIEW" if left else base)
            c.execute("UPDATE assets SET status=?, approved_version=?, attempts=? WHERE asset_id=?", (status, approved, len(left), aid))
            c.execute("DELETE FROM jobs WHERE asset_id=? AND provider='mock'", (aid,))
        canon = config.APPROVED_DIR / f"{aid}.png"
        if canon.exists() and not approved:
            canon.unlink()
    state.log("cleanup", f"cleared mock demo results for {len(removed)} asset(s) (archived in output/rejected/mock_demo)")
    return {"assets": removed}
