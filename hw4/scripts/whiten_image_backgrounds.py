#!/usr/bin/env python3
"""Turn black backgrounds (transparent PNGs flattened to JPG) white.
Flood-fills near-black pixels connected to the image border, so dark
details inside the garment are untouched. Enclosed pure-black gaps that are
tall and narrow (between arm and body) are filled too; wide dark areas such
as the inside of a hood are real shadows and are kept. Usage (from hw4/):
    uv run --no-project --with pillow python scripts/whiten_image_backgrounds.py data/products_original data/products"""
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import os
THRESH = int(os.getenv("THRESH", "14"))  # max(R,G,B) below this counts as background black

def whiten(im):
    im = im.convert("RGB"); w, h = im.size
    r, g, b = im.split()
    brightest = ImageChops.lighter(ImageChops.lighter(r, g), b)
    dark = brightest.point(lambda v: 255 if v < THRESH else 0)
    border = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    for p in border:
        if dark.getpixel(p) == 255:
            ImageDraw.floodfill(dark, p, 128)
    # Enclosed transparent gaps (e.g. between arm and body) are pure black and tall/narrow.
    # Wide dark areas (like the inside of a hood) are real shadows and stay.
    pure = brightest.point(lambda v: 255 if v <= 6 else 0)
    ppx = pure.load()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if ppx[x, y] == 255 and dark.getpixel((x, y)) != 128:
                ImageDraw.floodfill(pure, (x, y), 100)
                region = pure.point(lambda v: 255 if v == 100 else 0)
                x0, y0, x1, y1 = region.getbbox()
                area = region.histogram()[255]
                if area >= 150 and (y1 - y0) >= 2.5 * (x1 - x0):
                    dark.paste(128, mask=region)
                pure.paste(50, mask=region)
    bg = dark.point(lambda v: 255 if v == 128 else 0)
    if not bg.getbbox():
        return None, 0
    bg = bg.filter(ImageFilter.MaxFilter(5))  # also clear the ~2px dark anti-alias fringe
    out = im.copy(); out.paste((255, 255, 255), mask=bg)
    share = sum(bg.histogram()[255:]) / (w * h)
    return out, share

src, dst = Path(sys.argv[1]), Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
n = 0
for f in sorted(src.glob("*.jpg")):
    out, share = whiten(Image.open(f))
    if out is not None and share > 0.02:
        out.save(dst / f.name, quality=95); n += 1
        print(f"{f.name}\tbackground {share:.0%}")
print("converted", n)
