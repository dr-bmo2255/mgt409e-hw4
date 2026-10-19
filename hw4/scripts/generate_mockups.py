#!/usr/bin/env python3
"""One-time: generate blank product photos for the Custom Dan Gear mockups (gpt-image, ~$0.125 each).
Hard limit: the 7 products below, each generated only if its file doesn't exist yet. Stops on the first error.
Usage (from hw4/):  ask-dan-image-studio/backend/.venv/bin/python scripts/generate_mockups.py"""
import base64, os, sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "ask-dan-image-studio" / ".env", override=True)
OUT = ROOT / "Dan Image Resources" / "mockups"
COMMON = ("Photorealistic e-commerce product photo, straight-on front view, centered, the product fills about 75% of the frame, "
          "soft even studio lighting with a gentle shadow, plain very light warm-gray seamless background. The print area is completely "
          "BLANK: no logos, no text, no graphics, no labels, no people, no hands, no props.")
PRODUCTS = {
    "tee": "A plain white crew-neck short-sleeve cotton t-shirt, shown flat as if on an invisible mannequin, front side.",
    "crewneck": "A plain heather-gray crewneck sweatshirt with ribbed collar, cuffs and waistband, shown flat as if on an invisible mannequin, front side.",
    "hoodie": "A plain navy-blue pullover hoodie with drawstrings and a front kangaroo pocket, shown flat as if on an invisible mannequin, front side.",
    "mousepad": "A plain white rectangular fabric mouse pad with a thin black stitched edge, photographed from directly above.",
    "cup": "A plain white powder-coated 20 oz stainless steel insulated tumbler with a clear slide lid, standing upright, side view.",
    "notebook": "A plain white hardcover spiral-bound notebook with a black wire spiral on the left edge, cover facing up, photographed from directly above.",
    "folder": "A plain white two-pocket presentation folder, closed, front cover facing up, photographed from directly above.",
}

key = os.getenv("OPENAI_API_KEY")
if not key:
    sys.exit("OPENAI_API_KEY missing (expected in ask-dan-image-studio/.env)")
OUT.mkdir(parents=True, exist_ok=True)
total = 0.0
for name, desc in PRODUCTS.items():
    f = OUT / f"{name}.png"
    if f.exists():
        print("skip (exists):", f.name); continue
    r = httpx.post("https://api.openai.com/v1/images/generations", headers={"Authorization": f"Bearer {key}"},
                   json={"model": "gpt-image-2.5-sunburst", "prompt": f"{desc} {COMMON}", "size": "1024x1024",
                         "quality": "high", "n": 1, "output_format": "png"}, timeout=300)
    if r.status_code != 200:
        sys.exit(f"STOP on {name}: HTTP {r.status_code} {r.text[:300]}")
    body = r.json()
    f.write_bytes(base64.b64decode(body["data"][0]["b64_json"]))
    u = body.get("usage") or {}
    det = u.get("input_tokens_details") or {}
    cost = (det.get("text_tokens", 0) * 5 + det.get("image_tokens", 0) * 8 + u.get("output_tokens", 0) * 30) / 1e6
    total += cost
    print(f"{name}: saved, ${cost:.4f}", flush=True)
print(f"TOTAL ${total:.4f}")
