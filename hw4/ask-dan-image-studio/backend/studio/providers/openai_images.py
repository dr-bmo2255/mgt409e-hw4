"""OpenAI GPT Image adapter (images/edits with multiple reference images).

Works against OpenAI directly (OPENAI_API_KEY) or through the Portkey gateway (PORTKEY_API_KEY),
which is how this project's other AI calls are made. The key is read from the environment only:
never logged, stored, returned to the browser, or written to exports.
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import httpx

from .base import GenRequest, GenResult, Provider, ProviderError, cost_from_usage, estimate_cost

PORTKEY_URL = "https://api.portkey.ai/v1"
OPENAI_URL = "https://api.openai.com/v1"
MAX_RETRIES = 3
TEST_TRANSPORT: httpx.BaseTransport | None = None  # set by tests; real runs leave this None


def _credentials() -> tuple[str | None, str, dict]:
    if key := os.getenv("OPENAI_API_KEY"):
        return key, os.getenv("OPENAI_BASE_URL", OPENAI_URL), {}
    if key := os.getenv("PORTKEY_API_KEY"):
        return key, os.getenv("PORTKEY_BASE_URL", PORTKEY_URL), {"x-portkey-api-key": key}
    return None, "", {}


def key_status() -> dict:
    key, base, _ = _credentials()
    via = "OpenAI" if os.getenv("OPENAI_API_KEY") else ("Portkey gateway" if key else None)
    return {"present": bool(key), "via": via, "base_url": base or None}  # never the key itself


class OpenAIImagesProvider(Provider):
    name = "openai"
    paid = True

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport or TEST_TRANSPORT  # tests inject a fake transport; no real calls in tests

    def available(self) -> tuple[bool, str]:
        key, _, _ = _credentials()
        return (True, "") if key else (False, "No OPENAI_API_KEY or PORTKEY_API_KEY in the environment / .env")

    def estimate(self, req: GenRequest) -> float:
        return estimate_cost(req.model, req.size, req.quality, len(req.references))

    def generate(self, req: GenRequest) -> GenResult:
        key, base, extra = _credentials()
        if not key:
            raise ProviderError("API key not configured")
        headers = {"Authorization": f"Bearer {key}", **extra}
        data = {"model": req.model, "prompt": req.prompt, "size": req.size, "quality": req.quality,
                "n": "1", "output_format": "png"}
        files = []
        for p in req.references:
            files.append(("image[]", (Path(p).name, Path(p).read_bytes(), "image/png" if str(p).endswith(".png") else "image/jpeg")))
        last: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                with httpx.Client(timeout=httpx.Timeout(300, connect=20), transport=self._transport) as client:
                    r = client.post(f"{base}/images/edits", headers=headers, data=data, files=files)
                if r.status_code in (408, 409, 425, 429) or r.status_code >= 500:
                    raise ProviderError(f"HTTP {r.status_code}: {r.text[:300]}", transient=True)
                if r.status_code >= 400:
                    raise ProviderError(f"HTTP {r.status_code}: {r.text[:500]}", transient=False)
                body = r.json()
                b64 = (body.get("data") or [{}])[0].get("b64_json")
                if not b64:
                    raise ProviderError("Response contained no image data")
                usage = body.get("usage") or {}
                actual = cost_from_usage(req.model, usage)
                return GenResult(png_bytes=base64.b64decode(b64),
                                 cost_usd=actual if actual is not None else self.estimate(req),
                                 cost_is_estimate=actual is None, usage=usage, model=req.model)
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last = ProviderError(f"Network error: {e}", transient=True)
            except ProviderError as e:
                last = e
                if not e.transient:
                    raise
            time.sleep(min(2 ** attempt * 3, 30))  # bounded backoff
        raise last or ProviderError("Generation failed")


def get_provider(name: str) -> Provider:
    from .mock import MockProvider
    if name == "openai":
        return OpenAIImagesProvider()
    return MockProvider()
