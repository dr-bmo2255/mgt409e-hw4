#!/usr/bin/env python3
"""Part E: one Handsome Dan per decade (1920s-2020s) for the alumni "era" themes.

Paid (approved: 11 images, ~$0.80, hard cap $3). Uses the shop's Dan generator (backend/custom.py: identity
rules + Welcome Dan / Ice Hockey reference photos, gpt-image-2.5-sunburst, 1024x1024 high).
Skips images that already exist; stops on the first error.  Output: "Dan Image Resources/decades/dan_<decade>.png"

  backend/.venv/bin/python scripts/generate_decade_dans.py [--only 1920s,1950s] [--redo 1950s]
"""
import argparse, json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
import custom  # noqa: E402

OUT = ROOT / "Dan Image Resources" / "decades"
LEDGER = OUT / "ledger.json"
CAP_USD = 3.00

DECADES = {
    "1920s": "Great Gatsby glamour. Dan wears a black tuxedo, white bow tie and a straw boater, standing proudly at a glittering "
             "Art Deco garden party: gold geometric fan patterns, strings of lights, a jazz band in the background. At his side "
             "stands a smiling adult flapper in a beaded fringe dress, feathered headband and long pearls, mid-Charleston pose.",
    "1930s": "Golden age of radio. Dan in a three-piece tweed suit and fedora sits at a chrome streamline-moderne radio microphone, "
             "calling the Yale football game from a wood-paneled 1930s press box, sepia warm light, pennants in the background.",
    "1940s": "Swing era. Dan in a navy letterman cardigan with a big white Y, pleated trousers and saddle shoes, dancing the "
             "jitterbug at a 1940s big-band dance hall with a brass section, polished wood floor and warm spotlights.",
    "1950s": "Atomic-age diner. Dan in a Yale letter sweater and rolled cuffs sits at a chrome-and-turquoise 1950s soda fountain "
             "with a jukebox glowing behind him and a strawberry milkshake with two straws in front of him.",
    "1960s": "Mod sixties. Dan in a slim black turtleneck, a mod paisley scarf and round sunglasses, posing beside a pastel "
             "1960s camper van covered in flower-power daisies on a sunny campus green, bold orange and pink light.",
    "1970s": "Disco seventies. Dan in a wide-collared satin shirt, bell-bottoms and platform shoes strikes a disco pose on a "
             "light-up dance floor under a mirror ball, warm orange, brown and mustard tones, roller skates nearby.",
    "1980s": "Neon eighties. Dan in a color-block neon windbreaker, sweatband and leg warmers holds a boombox on his shoulder "
             "in front of a synthwave neon grid sunset, a Walkman clipped to his belt, hot pink and electric cyan light.",
    "1990s": "Nineties dorm room. Dan in an oversized flannel shirt and backwards baseball cap lounges on a beanbag with a "
             "chunky beige desktop computer, a portable CD player with headphones, and lava lamp glow in teal and purple.",
    "2000s": "Y2K two-thousands. Dan in a navy velour tracksuit and trucker hat holds a silver flip phone, white earbuds in, "
             "glossy bubbly silver-and-aqua background with lens flares, very early-2000s pop-star photo shoot.",
    "2010s": "Hipster twenty-tens. Dan in a knit beanie, thick-rimmed glasses and a plaid flannel takes a selfie with a "
             "smartphone in a coffee shop with Edison bulbs and a latte with heart latte art, soft filtered light.",
    "2020s": "Today. Dan in a cozy navy Yale hoodie with wireless earbuds sits at a laptop on a video call in a bright dorm room "
             "with a ring light and plants, a reusable water bottle covered in stickers beside him.",
}
TEXT_RULE = 'The only readable word allowed anywhere is "YALE" (optional, on clothing). No other text.'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only"); ap.add_argument("--redo")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"spent": 0.0, "images": {}}
    redo = set((a.redo or "").split(",")) - {""}
    todo = [d for d in DECADES if (not a.only or d in a.only.split(",")) and (d in redo or not (OUT / f"dan_{d}.png").exists())]
    if led["spent"] + len(todo) * 0.15 > CAP_USD:
        sys.exit(f"STOP: {len(todo)} images could exceed the ${CAP_USD} cap (spent ${led['spent']:.2f})")
    print(f"{len(todo)} decade Dans to make; spent so far ${led['spent']:.2f}", flush=True)

    def make(decade):
        prompt = "\n\n".join([custom.IDENTITY, f"SCENE (Handsome Dan in the {decade}): {DECADES[decade]}",
                              custom.STYLE["photo"], TEXT_RULE, custom.NEGATIVES,
                              "FORMAT: one single square image, one continuous scene; unmistakably the "
                              f"{decade} in clothing, colors, props and photo style."])
        png, cost = custom._generate_openai(prompt)
        (OUT / f"dan_{decade}.png").write_bytes(png)
        return decade, cost

    with ThreadPoolExecutor(max_workers=4) as pool:
        for decade, cost in pool.map(make, todo):
            led["spent"] = round(led["spent"] + cost, 4); led["images"][decade] = cost
            LEDGER.write_text(json.dumps(led, indent=1))
            print(f"{decade}: ${cost:.4f} (total ${led['spent']:.2f})", flush=True)
    print("done")


if __name__ == "__main__":
    main()
