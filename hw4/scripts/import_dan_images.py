#!/usr/bin/env python3
"""Import the Handsome Dan images from `Dan Image Resources/` into the shop.

Reads the studio manifest (product → Dan category) and writes one web-optimized image per
category into data/dan/ (git-ignored, like product photos):
  data/dan/<asset_id>.webp        1200 px, for heroes / reveals
  data/dan/<asset_id>_sm.webp      480 px, for cards / chat
  data/dan/dan_map.json            {"products": {product_id: asset_id}, "assets": {asset_id: {...}}}

Source: `Dan Image Resources/catalogue_new/` (35 created) and `catalogue_existing/` (19 originals).
Usage (from hw4/):  ask-dan-image-studio/backend/.venv/bin/python scripts/import_dan_images.py
"""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "ask-dan-image-studio"
OUT = ROOT / "data" / "dan"
RESOURCES = ROOT / "Dan Image Resources"
CAPTIONS = {"Apparel": "Dan's wearing it", "Family": "Dan's gift pick", "Schools": "Dan goes to grad school",
            "Sports": "Dan's in the game", "Colleges": "Dan's college pride", "Rivalries": "Dan vs. the rivals", "Custom": "Dan special"}


def save_webp(src: Path, dest: Path, width: int) -> None:
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dest, "WEBP", quality=82, method=6)


def main() -> None:
    m = json.loads((STUDIO / "manifest" / "assets.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    assets = {}
    for a in m["assets"]:
        aid = a["asset_id"]
        new, old = RESOURCES / "catalogue_new" / f"{aid}.png", RESOURCES / "catalogue_existing" / f"{aid}.png"
        if new.exists():
            src, origin = new, "created in Ask Dan Image Studio"
        elif old.exists():
            src, origin = old, "original Dan Final Images"
        else:
            print("MISSING image for", aid)
            continue
        save_webp(src, OUT / f"{aid}.webp", 1200)
        save_webp(src, OUT / f"{aid}_sm.webp", 480)
        with Image.open(src) as im:
            w, h = im.size
        assets[aid] = {"group": a["group"], "category": a["category"], "caption": f"{CAPTIONS.get(a['group'], 'Dan')}: {a['category']}",
                       "aspect": round(w / h, 3), "origin": origin}
    # Brand art: Dan's face for the chat avatar, the Welcome Dan portrait, and seasonal one-offs.
    welcome = RESOURCES / "brand" / "welcome_dan.png"
    if welcome.exists():
        im = Image.open(welcome).convert("RGB")
        w, h = im.size
        im.crop((int(w * .30), int(h * .18), int(w * .70), int(h * .58))).resize((256, 256), Image.LANCZOS).save(OUT / "avatar_dan.webp", "WEBP", quality=85)
        save_webp(welcome, OUT / "welcome_dan.webp", 1200)
    for f in sorted((RESOURCES / "one_off").glob("*.png")):
        save_webp(f, OUT / f"{f.stem}.webp", 1200)
        save_webp(f, OUT / f"{f.stem}_sm.webp", 480)
    # Part E: rival Dans (from the original Dan Final Images) and one Dan per decade for the alumni themes.
    for folder in ("rivals", "decades"):
        for f in sorted((RESOURCES / folder).glob("*.png")):
            save_webp(f, OUT / f"{f.stem}.webp", 1200)
            save_webp(f, OUT / f"{f.stem}_sm.webp", 480)
    # Blank product photos for Custom Dan Gear (Problem 10 Part C) → data/custom/mockups/<key>.webp
    mock_out = ROOT / "data" / "custom" / "mockups"
    mock_out.mkdir(parents=True, exist_ok=True)
    for f in sorted((RESOURCES / "mockups").glob("*.png")):
        save_webp(f, mock_out / f"{f.stem}.webp", 1024)
    products = {p["product_id"]: p["dan_asset_id"] for p in m["products"] if p["dan_asset_id"] in assets}
    (OUT / "dan_map.json").write_text(json.dumps({"products": products, "assets": assets}, indent=1))
    size = sum(f.stat().st_size for f in OUT.glob("*.webp")) / 1e6
    print(f"{len(assets)} Dan images ({size:.1f} MB) mapped to {len(products)} products → {OUT}")


if __name__ == "__main__":
    main()
