"""Every test runs in a throwaway studio root with links to the real inputs (read-only).
Real network access is blocked: any httpx request without the fake transport fails the test."""

import os
import shutil
import sys
from pathlib import Path

import pytest

REAL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def studio_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("studio")
    (root / "input").mkdir()
    for f in (REAL_ROOT / "input").iterdir():
        (root / "input" / f.name).symlink_to(f)
    (root / "frontend").mkdir()
    os.environ["STUDIO_ROOT"] = str(root)
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["PORTKEY_API_KEY"] = "test-key-not-real"
    for mod in [m for m in sys.modules if m == "studio" or m.startswith("studio.") or m == "app"]:
        del sys.modules[mod]
    return root


@pytest.fixture(scope="session")
def studio(studio_root):
    from studio import config, engine, inventory, state
    assert str(config.ROOT) == str(studio_root)
    m = inventory.build()
    state.init(engine.reload_manifest())
    return {"config": config, "engine": engine, "inventory": inventory, "state": state, "manifest": m}


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    import httpx
    real = httpx.Client.__init__

    def guarded(self, *a, **kw):
        if kw.get("transport") is None:
            raise AssertionError("Real network call attempted in tests")
        return real(self, *a, **kw)
    monkeypatch.setattr(httpx.Client, "__init__", guarded)


@pytest.fixture
def fresh_state(studio):
    """Reset mutable state between tests (keeps the manifest)."""
    st, cfg = studio["state"], studio["config"]
    with st.db() as c:
        for t in ("versions", "feedback", "jobs", "authorizations", "events"):
            c.execute(f"DELETE FROM {t}")
        c.execute("DELETE FROM assets")
        c.execute("DELETE FROM settings")
    for d in (cfg.PENDING_DIR, cfg.APPROVED_DIR, cfg.REJECTED_DIR, cfg.THUMB_DIR):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    st.init(studio["engine"].reload_manifest())
    return studio
