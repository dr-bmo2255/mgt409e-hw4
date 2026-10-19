import base64
import io
import json
import zipfile

import httpx
import pytest
from PIL import Image


# --- safe ZIP extraction ---------------------------------------------------------------------------


def test_safe_zip_blocks_zip_slip_and_skips_junk(studio, tmp_path):
    from studio.safezip import UnsafeZip, safe_extract
    good = tmp_path / "good.zip"
    with zipfile.ZipFile(good, "w") as z:
        z.writestr("folder/a.png", b"x" * 10)
        z.writestr("__MACOSX/folder/._a.png", b"junk")
        z.writestr("folder/.DS_Store", b"junk")
        z.writestr("folder/~$lock.xlsx", b"junk")
    out = safe_extract(good, tmp_path / "out")
    assert [p.name for p in out] == ["a.png"]
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as z:
        z.writestr("../../escape.png", b"x")
    with pytest.raises(UnsafeZip):
        safe_extract(evil, tmp_path / "out2")


def test_safe_zip_blocks_decompression_bomb(studio, tmp_path):
    from studio.safezip import UnsafeZip, safe_extract
    bomb = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("big.png", b"\0" * 5_000_000)
    with pytest.raises(UnsafeZip):
        safe_extract(bomb, tmp_path / "out")


# --- inventory & mapping --------------------------------------------------------------------------


def test_reconciled_counts_match_real_data(studio):
    c = studio["manifest"]["counts"]
    assert (c["catalogue_products"], c["product_photos_present"]) == (102, 102)
    assert (c["dan_assets_required"], c["existing_assets"], c["missing_assets"]) == (54, 19, 35)
    assert c["shields_available"] == 31
    assert studio["manifest"]["missing_inputs"] == []


@pytest.mark.parametrize("pid,expected", [
    ("district-vit-hoodie-vintage-sailor-bulldog", ("Apparel", "Hoodies")),   # 'sailor' ≠ sailing
    ("champion-mens-triumph-raglan-crew", ("Apparel", "Crewnecks")),          # 'crew' = crewneck
    ("crew-left-chest-hoodie", ("Sports", "Rowing")),                          # Yale crew
    ("squash-left-chest-tennis", ("Sports", "Squash")),
    ("yale-bowl-t-shirt", ("Sports", "Football")),
    ("the-forest-school-hoodie", ("Schools", "Environment")),
    ("2025-yale-vs-harvard-t-shirt", ("Rivalries", "Harvard")),
    ("yale-sports-creqneck-field-hockey", ("Sports", "Field Hockey")),         # not ice hockey
    ("school-of-management-crest-t-shirt", ("Schools", "Management")),
])
def test_product_mapping(studio, pid, expected):
    p = next(x for x in studio["manifest"]["products"] if x["product_id"] == pid)
    assert (p["dan_group"], p["dan_category"]) == expected


def test_only_filename_discrepancies_vs_previous_audit(studio):
    d = studio["manifest"]["discrepancies"]
    assert {x["issue"] for x in d} == {"audit filename not found in archive"}
    assert {x["studio"] for x in d} == {"Dan Ivy Harvard Sideeye.png", "Dan Crew Rowing.png"}


def test_references_are_original_dan_only(studio):
    refs = studio["manifest"]["references"]["dan_references"]
    assert refs and all(not r["name"].lower().startswith("dan2") for r in refs)
    collage = [f for f in studio["manifest"]["dan_files"] if f["disposition"] == "collage_excluded"]
    assert [f["filename"] for f in collage] == ["Dan Socks and Hoodie.png"]


def test_trumbull_and_school_shields_present(studio):
    slugs = {s["slug"] for s in studio["manifest"]["references"]["shields"]}
    assert {"trumbull_college", "school_of_management", "law_school", "school_of_the_environment"} <= slugs
    for a in studio["manifest"]["assets"]:
        if a["asset_id"].startswith("dan_school_"):
            assert a["shield_path"], a["asset_id"]


# --- status machine ---------------------------------------------------------------------------------


def test_invalid_status_transition_rejected(fresh_state):
    st = fresh_state["state"]
    with pytest.raises(st.BadTransition):
        st.set_status("dan_hoodie", "APPROVED")  # MISSING → APPROVED without review is illegal


# --- mock end-to-end ---------------------------------------------------------------------------------


def test_mock_generate_revise_approve_reject_composite(fresh_state):
    en, st, cfg = fresh_state["engine"], fresh_state["state"], fresh_state["config"]
    en.enqueue("dan_school_management", provider="mock")
    with pytest.raises(en.GuardError):  # duplicate while queued
        en.enqueue("dan_school_management", provider="mock")
    en.run_pending_sync()
    a = st.asset_state("dan_school_management")
    assert a["status"] == "PENDING_REVIEW" and len(a["versions"]) == 1
    v1 = a["versions"][0]
    assert (cfg.ROOT / v1["path"]).exists() and v1["cost_usd"] == 0
    assert Image.open(cfg.ROOT / v1["path"]).size == (1536, 1536)

    en.request_revision("dan_school_management", 1, "make Dan look like the Babe Ruth photo; correct the SOM shield")
    en.enqueue("dan_school_management", "revise", "correct the SOM shield", 1, provider="mock")
    en.run_pending_sync()
    a = st.asset_state("dan_school_management")
    assert [v["version"] for v in a["versions"]] == [1, 2] and a["versions"][1]["parent_version"] == 1
    assert "REVIEWER FEEDBACK" in a["versions"][1]["prompt"]

    en.composite("dan_school_management", 2, 0.5, 0.55, 0.15)
    en.reject("dan_school_management", 1, "wrong shield")
    en.approve("dan_school_management", 3)
    a = st.asset_state("dan_school_management")
    assert a["status"] == "APPROVED" and a["approved_version"] == 3
    assert (cfg.APPROVED_DIR / "dan_school_management.png").exists()
    assert (cfg.REJECTED_DIR / "dan_school_management_v01.png").exists()
    assert (cfg.PENDING_DIR / "dan_school_management_v01.png").exists()  # versions are never deleted


def test_composite_refuses_without_supplied_shield(fresh_state):
    en = fresh_state["engine"]
    en.enqueue("dan_hoodie", provider="mock")
    en.run_pending_sync()
    with pytest.raises(en.GuardError):
        en.composite("dan_hoodie", 1, 0.5, 0.5, 0.2)


# --- paid provider guards (fake transport, no network) ---------------------------------------------------


def _fake_transport(calls):
    buf = io.BytesIO()
    Image.new("RGB", (1536, 1536), (0, 53, 107)).putpixel((5, 5), (255, 255, 255))
    img = Image.effect_noise((1536, 1536), 64).convert("RGB")
    img.save(buf, "PNG")
    payload = {"data": [{"b64_json": base64.b64encode(buf.getvalue()).decode()}],
               "usage": {"input_tokens_details": {"text_tokens": 800, "image_tokens": 6000}, "output_tokens": 9000}}

    def handler(request):
        calls.append(request)
        assert request.headers["x-portkey-api-key"] == "test-key-not-real"
        return httpx.Response(200, json=payload)
    return httpx.MockTransport(handler)


@pytest.fixture
def paid(fresh_state, monkeypatch):
    from studio.providers import openai_images
    calls = []
    monkeypatch.setattr(openai_images, "TEST_TRANSPORT", _fake_transport(calls))
    st = fresh_state["state"]
    st.set_setting("provider", "openai")
    return fresh_state, calls


def test_paid_blocked_without_confirmed_references_or_authorization(paid):
    s, calls = paid
    en, st = s["engine"], s["state"]
    with pytest.raises(en.GuardError, match="references"):
        en.enqueue("dan_hoodie")
    st.set_setting("references_confirmed", True)
    with pytest.raises(en.GuardError, match="authorization"):
        en.enqueue("dan_hoodie")
    assert calls == []


def test_pilot_exactly_three_then_stops(paid):
    s, calls = paid
    en, st = s["engine"], s["state"]
    st.set_setting("references_confirmed", True)
    en.authorize_pilot(5.0)
    with pytest.raises(en.GuardError):
        en.authorize_pilot(5.0)  # only once
    with pytest.raises(en.GuardError, match="authorization"):
        en.enqueue("dan_sport_golf")  # not a pilot asset
    for aid in ("dan_school_management", "dan_sport_lacrosse", "dan_hoodie"):
        en.enqueue(aid)
    en.run_pending_sync()
    assert len(calls) == 3
    with pytest.raises(en.GuardError):
        en.enqueue("dan_hoodie")  # pilot authorization used up: no 4th paid image
    with pytest.raises(en.GuardError, match="pilot"):
        en.authorize_batch(["dan_sport_golf"], 5.0)  # batch only after reviewing all 3
    for aid in ("dan_school_management", "dan_sport_lacrosse", "dan_hoodie"):
        assert st.asset_state(aid)["status"] == "PENDING_REVIEW"  # never auto-approved
        en.approve(aid, 1)
    assert en.pilot_complete()
    v = st.asset_state("dan_hoodie")["versions"][0]
    assert v["cost_is_estimate"] == 0 and v["cost_usd"] > 0  # actual usage used when reported
    with pytest.raises(en.GuardError):
        en.authorize_batch(["a", "b", "c", "d", "e", "f"], 5.0)  # max 5


def test_spend_cap_enforced_before_request(paid):
    s, calls = paid
    en, st = s["engine"], s["state"]
    st.set_setting("references_confirmed", True)
    st.set_setting("cost_cap_usd", 0.05)
    en.authorize_pilot(5.0)
    with pytest.raises(en.GuardError, match="cap"):
        en.enqueue("dan_hoodie")
    assert calls == []


def test_resume_never_duplicates_paid_calls(paid):
    s, calls = paid
    en, st, cfg = s["engine"], s["state"], s["config"]
    st.set_setting("references_confirmed", True)
    en.authorize_pilot(5.0)
    en.enqueue("dan_hoodie")
    with st.db() as c:  # simulate a crash mid-request
        c.execute("UPDATE jobs SET status='running'")
        c.execute("UPDATE assets SET status='GENERATING' WHERE asset_id='dan_hoodie'")
    st.init(en.manifest())  # restart
    en.run_pending_sync()
    assert calls == []  # interrupted job is NOT silently re-sent
    with st.db() as c:
        assert c.execute("SELECT status FROM jobs").fetchone()[0] == "failed"
    # A file saved just before the crash is recovered, not regenerated
    (cfg.PENDING_DIR / "dan_hoodie_v01.png").write_bytes((cfg.ROOT / st.asset_state("dan_hoodie")["versions"][0]["path"]).read_bytes()
                                                         if st.asset_state("dan_hoodie")["versions"] else _png())
    assert en.recover_orphans() == 1
    assert calls == []


def _png():
    buf = io.BytesIO()
    Image.effect_noise((1024, 1024), 64).convert("RGB").save(buf, "PNG")
    return buf.getvalue()


# --- export -------------------------------------------------------------------------------------------


def test_export_contains_only_approved_and_no_secrets(fresh_state):
    en, cfg = fresh_state["engine"], fresh_state["config"]
    from studio import exports
    en.enqueue("dan_sport_golf", provider="mock")
    en.enqueue("dan_sport_tennis", provider="mock")
    en.run_pending_sync()
    with fresh_state["state"].db() as c:  # stand-in for a real (paid) image: mock approvals are never exported
        c.execute("UPDATE versions SET provider='openai' WHERE asset_id='dan_sport_golf'")
    en.approve("dan_sport_golf", 1)
    out = exports.export_all()
    with zipfile.ZipFile(cfg.ROOT / out["zip"]) as z:
        names = set(z.namelist())
        assert "approved_png/dan_sport_golf.png" in names
        assert "approved_png/dan_sport_tennis.png" not in names
        for f in ("product_dan_mapping.json", "product_dan_mapping.csv", "ask_dan_data2_audit_updated.xlsx",
                  "ask_dan_checklist_updated.txt", "review_and_cost_report.md"):
            assert f in names
        blob = b"".join(z.read(n) for n in names if not n.endswith((".png", ".xlsx")))
        assert b"test-key-not-real" not in blob
        mapping = json.loads(z.read("product_dan_mapping.json"))
        assert len(mapping) == 102
    assert "dan_sport_tennis" in out["remaining"]


def test_inputs_never_modified(studio):
    from studio.inventory import find_inputs, sha256
    before = studio["manifest"]["inputs"]
    for k, p in find_inputs().items():
        assert sha256(p) == before[k]["sha256"]


def test_mock_approvals_never_exported_and_can_be_cleared(fresh_state):
    en, st, cfg = fresh_state["engine"], fresh_state["state"], fresh_state["config"]
    from studio import exports
    en.enqueue("dan_school_law", provider="mock")
    en.run_pending_sync()
    en.composite("dan_school_law", 1, 0.5, 0.5, 0.15)  # composite of a mock is still mock-derived
    en.approve("dan_school_law", 2)
    assert en.is_mock_derived("dan_school_law", 2)
    out = exports.export_all()
    assert out["approved_pngs"] == [] and out["mock_approvals_not_exported"] == ["dan_school_law"]
    en.clear_mock_results()
    a = st.asset_state("dan_school_law")
    assert a["status"] == "MISSING" and a["versions"] == [] and a["approved_version"] is None
    assert not (cfg.APPROVED_DIR / "dan_school_law.png").exists()
    assert (cfg.REJECTED_DIR / "mock_demo" / "dan_school_law_v01.png").exists()


def test_retry_after_failed_job_is_allowed(fresh_state, monkeypatch):
    en, st = fresh_state["engine"], fresh_state["state"]
    from studio.providers import mock
    monkeypatch.setattr(mock.MockProvider, "generate", lambda self, req: (_ for _ in ()).throw(RuntimeError("boom")))
    en.enqueue("dan_sport_golf", provider="mock")
    en.run_pending_sync()
    assert st.asset_state("dan_sport_golf")["status"] == "FAILED"
    monkeypatch.undo()
    en.enqueue("dan_sport_golf", provider="mock")  # not rejected as a duplicate
    en.run_pending_sync()
    assert st.asset_state("dan_sport_golf")["status"] == "PENDING_REVIEW"


def test_estimate_calibrates_from_actual_usage(paid):
    s, calls = paid
    en, st = s["engine"], s["state"]
    st.set_setting("references_confirmed", True)
    before = en.estimate_for("dan_hoodie")
    en.authorize_pilot(5.0)
    en.enqueue("dan_hoodie")
    en.run_pending_sync()
    actual = st.asset_state("dan_hoodie")["versions"][0]["cost_usd"]
    after = en.estimate_for("dan_sport_golf")
    assert after == round(actual * 1.25, 4) and after != before


# --- chat & one-off custom images ----------------------------------------------------------------------


def test_chat_brief_custom_asset_mock_generate_and_export(fresh_state, monkeypatch):
    import asyncio
    from studio import chat_agent, exports
    en, st = fresh_state["engine"], fresh_state["state"]
    with st.db() as c:
        c.execute("DELETE FROM custom_assets")
        c.execute("DELETE FROM chat_messages")

    async def fake(message, instructions, msgs):
        assert "Trumbull College" in instructions or "trumbull_college" in instructions  # shields offered to the agent
        return chat_agent.StudioReply(reply="Drafted a cheerleader Dan.", brief=chat_agent.ImageBrief(
            display_name="Dan as Yale cheerleader", setting="Yale Bowl sideline at dusk", outfit="cheer sweater",
            pose="leaping with pom-poms", humor="pom-pom stuck on his ear", permitted_text=["YALE"],
            shield_slug="made_up_shield"))
    monkeypatch.setattr(chat_agent, "RUNNER", fake)
    out = asyncio.run(chat_agent.respond("Make Dan a Yale cheerleader", None, en.manifest(), st.all_asset_states()))
    assert out["brief"]["display_name"] == "Dan as Yale cheerleader"
    assert out["brief"]["shield_slug"] is None  # invented shield stripped
    assert [h["role"] for h in chat_agent.history()] == ["user", "assistant"]

    a = en.create_custom_asset(out["brief"])
    assert a["asset_id"] == "dan_custom_dan_as_yale_cheerleader" and a["custom"]
    with pytest.raises(en.GuardError):
        en.create_custom_asset({**out["brief"], "shield_slug": "fake"})
    assert en.overview()["scoped_total"] == 35  # custom images never change the catalogue scope

    en.enqueue(a["asset_id"], provider="mock")
    en.run_pending_sync()
    assert "cheerleader" in st.asset_state(a["asset_id"])["versions"][0]["prompt"].lower()
    with st.db() as c:
        c.execute("UPDATE versions SET provider='openai' WHERE asset_id=?", (a["asset_id"],))
    en.approve(a["asset_id"], 1)
    res = exports.export_all()
    assert res["custom_pngs"] == [f"{a['asset_id']}.png"] and res["approved_pngs"] == []
    assert a["asset_id"] not in res["remaining"]


def test_custom_paid_generation_still_needs_authorization(paid):
    s, calls = paid
    en, st = s["engine"], s["state"]
    st.set_setting("references_confirmed", True)
    a = en.create_custom_asset({"display_name": "Dan at Mory's", "setting": "wood-paneled room", "outfit": "blazer",
                                "pose": "sitting", "humor": "tiny cup", "permitted_text": [], "shield_slug": None})
    with pytest.raises(en.GuardError, match="authorization"):
        en.enqueue(a["asset_id"])
    assert calls == []


def test_white_shield_fields_stay_opaque(studio):
    """Regression: only border-connected background is transparent; a white shield field (Trumbull) is kept."""
    from PIL import Image
    im = Image.open(studio["config"].REF_SHIELD_DIR / "trumbull_college.png").convert("RGBA")
    w, h = im.size
    assert im.getpixel((1, 1))[3] == 0                     # outside the shield: transparent
    opaque_white = sum(1 for x in range(w) for y in range(h) if im.getpixel((x, y))[3] == 255 and min(im.getpixel((x, y))[:3]) > 230)
    assert opaque_white > 0.25 * w * h                     # the white field is solid, not see-through


def test_composite_keeps_warm_foreground_in_front():
    """A vivid orange object overlapping the shield area must stay visible (occlusion)."""
    import io
    from PIL import Image
    from studio.composite import composite_shield
    base = Image.new("RGB", (1024, 1024), (20, 28, 60))                 # navy 'sweater'
    for x in range(560, 1024):
        for y in range(400, 700):
            base.putpixel((x, y), (235, 120, 30))                        # orange 'pumpkin' on the right
    buf = io.BytesIO(); base.save(buf, "PNG")
    from studio import config
    out = Image.open(io.BytesIO(composite_shield(buf.getvalue(), config.REF_SHIELD_DIR / "trumbull_college.png",
                                                 0.5, 0.55, 0.2))).convert("RGB")
    assert out.getpixel((600, 560))[0] > 180     # pumpkin pixel still orange (in front of shield)
    assert sum(out.getpixel((470, 560))) > 300   # shield (white field) drawn on the sweater side
