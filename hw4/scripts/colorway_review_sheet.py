#!/usr/bin/env python3
"""Part D review sheet: each product's original photo followed by its rendered colorways, one row per product,
split into pages of 15 rows -> output/colorway_review/sheet_<n>.jpg (free; reads local files only)."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "data" / "products" / "colorways" / "plan.json"
SRC = ROOT / "Dan Image Resources" / "colorways"
OUT = ROOT / "output" / "colorway_review"
T, LABEL, ROWS, COLS = 220, 30, 15, 6


def slug(s):
    import re
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    plan = json.loads(PLAN.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except OSError:
        font = ImageFont.load_default()
    items = list(plan.items())
    pages = [items[i:i + ROWS] for i in range(0, len(items), ROWS)]
    for n, page in enumerate(pages, 1):
        sheet = Image.new("RGB", (COLS * T + 260, len(page) * (T + LABEL)), "white")
        d = ImageDraw.Draw(sheet)
        for r, (pid, p) in enumerate(page):
            y = r * (T + LABEL)
            d.text((6, y + T // 2), f"{(n - 1) * ROWS + r + 1}. {p['name'][:30]}", fill="black", font=font)
            cells = [(ROOT / "data" / p["image"], f"original: {p['base']}")] + \
                    [(SRC / f"{pid}__{slug(t)}.png", t) for t in p["render"]]
            for c, (f, label) in enumerate(cells[:COLS]):
                x = 260 + c * T
                if f.exists():
                    im = Image.open(f).convert("RGB"); im.thumbnail((T - 8, T - 8))
                    sheet.paste(im, (x + 4, y + 4))
                else:
                    d.rectangle((x + 4, y + 4, x + T - 4, y + T - 4), outline="red")
                d.text((x + 6, y + T + 4), label, fill="#b00" if c == 0 else "black", font=font)
        dest = OUT / f"sheet_{n}.jpg"
        sheet.save(dest, quality=82)
        print(dest)


if __name__ == "__main__":
    main()
