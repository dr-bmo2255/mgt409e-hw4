#!/usr/bin/env python3
"""Part D: product colorways.

The catalog's `colors` field lists every color in a product (garment + print). We treat each listed color as
a garment colorway: the existing photo shows one of them (the "base"), and the others are rendered with an
image edit of that photo (same garment and print, new fabric color, print recolored if it would disappear).

  python scripts/colorways.py plan                 # detect each photo's base color -> data/products/colorways/plan.json
  python scripts/colorways.py render --only a,b    # paid: render listed products (or --limit N), cap enforced
  python scripts/colorways.py build                # webp + colorways.json for the site (free)

Sources (PNG from the API) go to "Dan Image Resources/colorways/" (git-ignored); site images to data/products/colorways/.
"""
import argparse, base64, io, json, os, re, sqlite3, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "campus_customs.db"
OUT = ROOT / "data" / "products" / "colorways"
SRC = ROOT / "Dan Image Resources" / "colorways"
PLAN = OUT / "plan.json"
LEDGER = SRC / "ledger.json"
CAP_USD = 12.00          # hard cap for all colorway renders (approved: ~$8-9, cap $12)
PER_IMAGE_MAX = 0.20     # stop if any single image costs more than this

# Approximate fabric colors for matching and for describing the target to the image model.
PALETTE = {
    "black": (30, 30, 32), "blue": (40, 80, 170), "charcoal gray": (70, 72, 76), "cream": (240, 232, 210),
    "dark heather charcoal": (62, 64, 68), "dark heather gray": (95, 97, 100), "dusty coral": (214, 130, 115),
    "gold": (200, 160, 60), "gray": (150, 150, 152), "green": (40, 110, 70), "heather charcoal gray": (80, 82, 86),
    "heather gray": (170, 170, 172), "ivory": (245, 240, 225), "light blue": (150, 190, 225), "light gray": (205, 205, 207),
    "navy": (25, 35, 65), "navy blue": (25, 38, 72), "red": (180, 35, 45), "royal blue": (35, 75, 170),
    "white": (250, 250, 250), "yellow": (240, 205, 60),
}
SKIP = {"multicolor"}
# Base colors checked by eye on the contact sheet where the automatic fabric sample was fooled.
BASE_OVERRIDES = {"2025-yale-vs-harvard-t-shirt": "heather gray", "school-of-nursing-crest-t-shirt": "navy blue"}


def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def products():
    c = sqlite3.connect(DB)
    return [(pid, name, json.loads(cols), path) for pid, name, cols, path in
            c.execute("SELECT product_id, name, colors, image_file_path FROM catalogue ORDER BY product_id")]


def fabric_sample(path):
    """Median color of plain fabric: patches low on the body, left and right of center (below most prints)."""
    from PIL import Image, ImageStat
    im = Image.open(path).convert("RGB")
    W, H = im.size
    mask = im.convert("L").point(lambda v: 255 if v < 244 else 0)
    x0, y0, x1, y1 = mask.getbbox() or (0, 0, W, H)
    w, h = x1 - x0, y1 - y0
    pts = []
    for fx, fy in ((0.33, 0.80), (0.67, 0.80), (0.30, 0.70), (0.70, 0.70)):
        cx, cy = int(x0 + fx * w), int(y0 + fy * h)
        patch = im.crop((cx - 8, cy - 8, cx + 8, cy + 8))
        pts.append(tuple(ImageStat.Stat(patch).median))
    pts.sort(key=sum)
    return pts[len(pts) // 2]


def nearest(rgb, names):
    def d(a, b): return sum((x - y) ** 2 for x, y in zip(a, b))
    return min(names, key=lambda n: d(rgb, PALETTE.get(n, (128, 128, 128))))


def cmd_plan(_):
    OUT.mkdir(parents=True, exist_ok=True)
    plan = {}
    for pid, name, cols, path in products():
        cols = [c for c in cols if c not in SKIP]
        if len(cols) < 2:
            continue
        rgb = fabric_sample(ROOT / "data" / path)
        base = BASE_OVERRIDES.get(pid) or nearest(rgb, cols)
        plan[pid] = {"name": name, "image": path, "colors": cols, "base": base, "sample": rgb,
                     "render": [c for c in cols if c != base]}
    PLAN.write_text(json.dumps(plan, indent=1))
    print(f"{len(plan)} products, {sum(len(p['render']) for p in plan.values())} colorways to render -> {PLAN}")


def prompt_for(p, target):
    others = [c for c in p["colors"] if c != target]
    contrast = next((c for c in others if sum(PALETTE.get(c, (0, 0, 0))) and
                     abs(sum(PALETTE.get(c, (0, 0, 0))) - sum(PALETTE.get(target, (0, 0, 0)))) > 240), others[0])
    return (
        f"Edit this product photo of a Yale apparel item. Change ONLY the garment's fabric color from {p['base']} to {target}. "
        f"Keep everything else exactly the same: the same garment style, cut, seams, ribbing, folds, shadows, camera angle, "
        f"framing and the plain pure-white background. Keep the printed design identical in shape, layout, size and placement, "
        f"and keep every letter spelled exactly as it is. If a part of the print would become hard to see on {target} fabric, "
        f"recolor just that part of the print to {contrast} so it stays clearly readable. No new text, logos, tags or props. "
        f"Photorealistic e-commerce product photo."
    )


def ledger():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"spent": 0.0, "images": {}}


def render_one(key, pid, p, target):
    """One paid image edit. Returns (png bytes, cost) or raises RuntimeError with the API message."""
    import httpx
    from PIL import Image
    im = Image.open(ROOT / "data" / p["image"]).convert("RGB")
    buf = io.BytesIO(); im.save(buf, "PNG")
    r = httpx.post("https://api.openai.com/v1/images/edits", headers={"Authorization": f"Bearer {key}"},
                   data={"model": "gpt-image-2.5-sunburst", "prompt": prompt_for(p, target), "size": "1024x1024",
                         "quality": "high", "n": "1", "output_format": "png"},
                   files=[("image[]", (f"{pid}.png", buf.getvalue(), "image/png"))], timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"{pid} / {target}: HTTP {r.status_code} {r.text[:300]}")
    body = r.json(); u = body.get("usage") or {}; det = u.get("input_tokens_details") or {}
    cost = round(((det.get("text_tokens") or 0) * 5 + (det.get("image_tokens") or 0) * 8 + (u.get("output_tokens") or 0) * 30) / 1e6, 4)
    return base64.b64decode(body["data"][0]["b64_json"]), cost


def cmd_render(args):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from dotenv import dotenv_values
    key = dotenv_values(ROOT / "ask-dan-image-studio" / ".env").get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY missing (ask-dan-image-studio/.env)")
    plan, led = json.loads(PLAN.read_text()), ledger()
    SRC.mkdir(parents=True, exist_ok=True)
    todo = [(pid, t) for pid, p in plan.items() for t in p["render"]
            if (not args.only or pid in args.only.split(",")) and not (SRC / f"{pid}__{slug(t)}.png").exists()]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} to render with {args.workers} workers; spent so far ${led['spent']:.2f} of ${CAP_USD:.2f} cap", flush=True)
    lock, state = threading.Lock(), {"inflight": 0, "stop": None}
    RESERVE = 0.10  # each in-flight image counts against the cap until its real cost is known

    def work(item):
        pid, target = item
        with lock:
            if state["stop"]:
                return
            if led["spent"] + (state["inflight"] + 1) * RESERVE > CAP_USD:
                state["stop"] = f"cap reached (${led['spent']:.2f})"
                return
            state["inflight"] += 1
        try:
            png, cost = render_one(key, pid, plan[pid], target)
        except Exception as e:  # noqa: BLE001 - any failure stops the batch
            with lock:
                state["inflight"] -= 1
                state["stop"] = state["stop"] or str(e)
            return
        out = SRC / f"{pid}__{slug(target)}.png"
        out.write_bytes(png)
        with lock:
            state["inflight"] -= 1
            led["spent"] = round(led["spent"] + cost, 4); led["images"][out.name] = cost
            LEDGER.write_text(json.dumps(led, indent=1))
            print(f"[{len(led['images'])}] {pid} -> {target}: ${cost:.4f} (total ${led['spent']:.2f})", flush=True)
            if cost > PER_IMAGE_MAX:
                state["stop"] = f"image cost ${cost} above per-image max"

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(work, todo))
    LEDGER.write_text(json.dumps(led, indent=1))
    if state["stop"]:
        sys.exit(f"STOPPED: {state['stop']} (total spent ${led['spent']:.2f})")
    print(f"done; total spent ${led['spent']:.2f}")


def cmd_build(_):
    from PIL import Image
    plan = json.loads(PLAN.read_text())
    out = {}
    for pid, p in plan.items():
        imgs = {p["base"]: f"/media/products/{Path(p['image']).name}"}
        for t in p["render"]:
            src = SRC / f"{pid}__{slug(t)}.png"
            if not src.exists():
                continue
            dest = OUT / f"{pid}__{slug(t)}.webp"
            im = Image.open(src).convert("RGB"); im.thumbnail((900, 900)); im.save(dest, "WEBP", quality=86)
            imgs[t] = f"/media/products/colorways/{dest.name}"
        out[pid] = {"base": p["base"], "images": imgs}
    (OUT / "colorways.json").write_text(json.dumps(out, indent=1))
    print(f"{sum(len(v['images']) - 1 for v in out.values())} colorway images for {len(out)} products -> {OUT / 'colorways.json'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "render", "build"])
    ap.add_argument("--only"); ap.add_argument("--limit", type=int); ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    {"plan": cmd_plan, "render": cmd_render, "build": cmd_build}[a.cmd](a)
