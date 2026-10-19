#!/usr/bin/env python3
"""Part F: regenerate the field hockey Dan (the Part A image gave him 5 legs).
Paid: 2 candidates at 1536x1536 high (same as the catalogue images), ~$0.25, cap $0.60.
Output: "Dan Image Resources/fixes/dan_sport_field_hockey_v<n>.png"."""
import base64, io, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
import custom  # noqa: E402

OUT = ROOT / "Dan Image Resources" / "fixes"
ANATOMY = ("ANATOMY (most important): Dan is a normal English bulldog with EXACTLY FOUR LEGS: two front legs and two hind legs, "
           "each ending in one paw, all four clearly visible and planted naturally on the turf. No extra legs, paws or limbs, "
           "no human-like arms; he does not hold anything with his paws.")
SCENE = ("SCENE (Field Hockey): Handsome Dan trots across a bright blue artificial field-hockey TURF (not ice) at a Yale game, "
         "carrying a proper field hockey stick crosswise in his mouth, with a white field hockey ball just in front of his front "
         "paws. He wears a navy Yale field hockey jersey with a white Y and navy shin guards on his front legs. Fierce, happy "
         "focus. A goal cage and blurred Yale players in navy in the background.")


def make(n):
    prompt = "\n\n".join([custom.IDENTITY, SCENE, ANATOMY, custom.STYLE["photo"],
                          'EXACT TEXT: the only readable word allowed is "YALE" (optional, on a banner or jersey).',
                          custom.NEGATIVES, "FORMAT: one single square image, one continuous scene."])
    r = httpx.post(f"{custom.OPENAI_URL}/images/edits", headers={"Authorization": f"Bearer {custom._openai_key()}"},
                   data={"model": custom.IMAGE_MODEL, "prompt": prompt, "size": "1536x1536", "quality": "high", "n": "1",
                         "output_format": "png"}, files=custom._reference_files(), timeout=300)
    r.raise_for_status()
    body = r.json()
    out = OUT / f"dan_sport_field_hockey_v{n}.png"
    out.write_bytes(base64.b64decode(body["data"][0]["b64_json"]))
    return out.name, custom._cost(body.get("usage") or {})


OUT.mkdir(parents=True, exist_ok=True)
total = 0.0
with ThreadPoolExecutor(2) as pool:
    for name, cost in pool.map(make, [1, 2]):
        total += cost
        print(f"{name}: ${cost:.4f}")
print(f"total ${total:.2f}")
