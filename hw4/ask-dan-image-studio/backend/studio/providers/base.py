"""Image provider interface. Adding FLUX later = one new class, no app rewrite."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GenRequest:
    asset_id: str
    prompt: str
    references: list[Path]  # Dan identity refs, optional shield, optional current image (for revisions)
    size: str = "1536x1536"
    quality: str = "high"
    model: str = "gpt-image-2.5-sunburst"


@dataclass
class GenResult:
    png_bytes: bytes
    cost_usd: float
    cost_is_estimate: bool
    usage: dict = field(default_factory=dict)
    model: str = ""


class ProviderError(Exception):
    def __init__(self, message: str, transient: bool = False):
        super().__init__(message)
        self.transient = transient


class Provider:
    name = "base"
    paid = False

    def available(self) -> tuple[bool, str]:
        return True, ""

    def estimate(self, req: GenRequest) -> float:
        return 0.0

    def generate(self, req: GenRequest) -> GenResult:
        raise NotImplementedError


# --- Cost model (OFFICIAL token prices, ESTIMATED token counts) -----------------------------------
# developers.openai.com/api/docs/models/gpt-image-2.5-sunburst (checked 2026-10-18):
#   text input $5/1M, image input $8/1M, image output $30/1M (Standard). No official per-image table,
#   so token counts below are conservative estimates; actual usage replaces them when the API reports it.
PRICES = {"gpt-image-2.5-sunburst": {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0},
          "gpt-image-2.5-flare": {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0},
          "gpt-image-2": {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0}}
OUT_TOKENS_1024 = {"low": 300, "medium": 1100, "high": 4200, "xhigh": 6500, "max": 9000, "auto": 4200}
IN_TOKENS_PER_REF = 1600  # conservative per reference image
PROMPT_TOKENS = 900


def estimate_cost(model: str, size: str, quality: str, n_refs: int) -> float:
    p = PRICES.get(model, PRICES["gpt-image-2.5-sunburst"])
    w, h = (int(x) for x in size.lower().split("x"))
    scale = (w * h) / (1024 * 1024)
    out_tokens = OUT_TOKENS_1024.get(quality, 4200) * scale
    cost = out_tokens * p["image_out"] + n_refs * IN_TOKENS_PER_REF * p["image_in"] + PROMPT_TOKENS * p["text_in"]
    return round(cost / 1_000_000, 4)


def cost_from_usage(model: str, usage: dict) -> float | None:
    """Actual cost from the API's reported token usage, if present."""
    if not usage:
        return None
    p = PRICES.get(model, PRICES["gpt-image-2.5-sunburst"])
    det = usage.get("input_tokens_details") or {}
    text_in = det.get("text_tokens")
    img_in = det.get("image_tokens")
    out = usage.get("output_tokens")
    if out is None or (text_in is None and img_in is None):
        return None
    return round(((text_in or 0) * p["text_in"] + (img_in or 0) * p["image_in"] + out * p["image_out"]) / 1_000_000, 4)
