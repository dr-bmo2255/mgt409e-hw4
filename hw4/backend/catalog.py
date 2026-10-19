"""Catalog data access shared by the product API (main.py) and the agent tools (tools.py)."""

import json
import re
import sqlite3

from db import connect

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# The catalogue has 22 inconsistent garment_type labels; group them for filtering.
CATEGORY_RULES = [
    ("Quarter-Zips", ("quarter-zip",)),
    ("Jackets & Fleece", ("jacket", "fleece")),
    ("Hoodies", ("hoodie", "hooded")),
    ("Crewnecks", ("crewneck", "crew", "mockneck")),
    ("Long Sleeve", ("long-sleeve",)),
    ("T-Shirts", ("t-shirt",)),
]
CATEGORY_NAMES = [name for name, _ in CATEGORY_RULES] + ["Other"]


# --- Handsome Dan category images (Problem 10) ------------------------------------------
# Built by scripts/import_dan_images.py from "Dan Image Resources/" into data/dan/.
from collections import Counter
from functools import lru_cache
from pathlib import Path

DAN_DIR = Path(__file__).resolve().parent.parent / "data" / "dan"


@lru_cache(maxsize=1)
def dan_map() -> dict:
    f = DAN_DIR / "dan_map.json"
    return json.loads(f.read_text()) if f.exists() else {"products": {}, "assets": {}}


COLORWAYS_FILE = Path(__file__).resolve().parent.parent / "data" / "products" / "colorways" / "colorways.json"


@lru_cache(maxsize=1)
def colorway_map() -> dict:
    """Part D: product_id -> {"base": color in the original photo, "images": {color: url}} (scripts/colorways.py build)."""
    return json.loads(COLORWAYS_FILE.read_text()) if COLORWAYS_FILE.exists() else {}


def dan_for_asset(asset_id: str | None) -> dict | None:
    a = dan_map()["assets"].get(asset_id or "")
    if not a:
        return None
    return {"asset_id": asset_id, "image_url": f"/media/dan/{asset_id}.webp", "thumb_url": f"/media/dan/{asset_id}_sm.webp",
            "caption": a["caption"], "category": a["category"], "group": a["group"], "aspect": a["aspect"]}


def dan_for_products(product_ids: list[str]) -> dict | None:
    """The Dan image that best represents a set of products: the most common category (first wins ties)."""
    ids = [dan_map()["products"].get(pid) for pid in product_ids]
    ids = [i for i in ids if i]
    if not ids:
        return None
    counts = Counter(ids)
    top = max(counts.values())
    return dan_for_asset(next(i for i in ids if counts[i] == top))


def category_for(garment_type: str) -> str:
    g = garment_type.lower()
    for name, keys in CATEGORY_RULES:
        if any(k in g for k in keys):
            return name
    return "Other"


def product_from_row(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": category_for(row["garment_type"]),
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_file_path": row["image_file_path"],
        "image_url": f"/media/{row['image_file_path']}",
        "price": row["price"],
        "dan": dan_for_asset(dan_map()["products"].get(row["product_id"])),
        # Part D: a photo per colorway (the original photo is the base color's).
        "base_color": colorway_map().get(row["product_id"], {}).get("base"),
        "color_images": colorway_map().get(row["product_id"], {}).get("images", {}),
    }


def _sort_sizes(sizes: list[dict]) -> list[dict]:
    return sorted(sizes, key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)


def inventory_for(conn: sqlite3.Connection, product_id: str) -> list[dict]:
    rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    return _sort_sizes([{"size": r["size"], "quantity": r["quantity"]} for r in rows])


def load_products(with_inventory: bool = False) -> list[dict]:
    """Every product (parsed), plus total_stock; optionally the per-size inventory."""
    with connect() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        inv: dict[str, list[dict]] = {}
        for r in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            inv.setdefault(r["product_id"], []).append({"size": r["size"], "quantity": r["quantity"]})
    products = []
    for row in rows:
        p = product_from_row(row)
        sizes = _sort_sizes(inv.get(p["product_id"], []))
        p["total_stock"] = sum(s["quantity"] for s in sizes)
        if with_inventory:
            p["inventory"] = sizes
        products.append(p)
    return products


def get_product(product_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        p = product_from_row(row)
        p["inventory"] = inventory_for(conn, product_id)
    p["total_stock"] = sum(s["quantity"] for s in p["inventory"])
    return p


def haystack(p: dict) -> str:
    return " ".join([p["name"], p["garment_type"], p["category"], p["description"], *p["colors"], *p["search_tags"]]).lower()


# Shopper words → words the catalog actually uses.
SYNONYMS = {
    "sweatshirt": ["crewneck", "hoodie", "sweatshirt"],
    "hoody": ["hoodie"],
    "hoodies": ["hoodie"],
    "tee": ["t-shirt"],
    "tees": ["t-shirt"],
    "tshirt": ["t-shirt"],
    "shirt": ["t-shirt", "shirt"],
    "grey": ["gray"],
    "quarter": ["quarter-zip", "1 4 zip"],
    "quarterzip": ["quarter-zip"],
    "1/4": ["quarter-zip", "1 4 zip"],
    "jacket": ["jacket", "fleece"],
    "blue": ["blue", "navy"],
    "crew": ["crewneck", "crew"],
    "mom": ["mom"],
    "dad": ["dad"],
}
STOPWORDS = {"a", "an", "the", "any", "some", "do", "you", "have", "in", "of", "for", "with", "and", "or", "me", "show", "i", "want", "yale", "please", "size", "sizes"}


def _variants(word: str) -> list[str]:
    w = word.lower().strip()
    out = SYNONYMS.get(w, [w])
    if w.endswith("s") and len(w) > 3 and w not in SYNONYMS:
        out = out + [w[:-1]]
    return out


def search(query: str = "", category: str | None = None, color: str | None = None,
           max_price: float | None = None, size: str | None = None, limit: int = 8) -> list[dict]:
    """Keyword search with simple scoring. Every meaningful word must match (via synonyms)."""
    return search_all(query, category, color, max_price, size)[:limit]


def search_all(query: str = "", category: str | None = None, color: str | None = None,
               max_price: float | None = None, size: str | None = None) -> list[dict]:
    """Every match, best first (search() just trims this)."""
    words = [w for w in re.findall(r"[a-z0-9/&'-]+", query.lower()) if w not in STOPWORDS]
    results = []
    for p in load_products(with_inventory=True):
        if category and p["category"].lower() != category.lower():
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        if color and not any(color.lower() in c.lower() or (color.lower() == "grey" and "gray" in c.lower()) for c in p["colors"]):
            continue
        if size:
            q = next((s["quantity"] for s in p["inventory"] if s["size"].upper() == size.upper()), 0)
            if q <= 0:
                continue
        text = haystack(p)
        score = 0
        ok = True
        for w in words:
            hits = [v for v in _variants(w) if v in text]
            if not hits:
                ok = False
                break
            score += 3 if any(v in p["name"].lower() for v in hits) else 1
        if ok:
            results.append((score, p))
    results.sort(key=lambda t: (-t[0], t[1]["name"]))
    return [p for _, p in results]


# --- Lookups used by the price / stock tools (Problem 6) -----------------------------

LOW_STOCK_THRESHOLD = 5  # 1-5 units left counts as "low stock"

SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "sm": "S", "small": "S",
    "m": "M", "med": "M", "medium": "M",
    "l": "L", "lg": "L", "large": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "2x": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "double xl": "XXL",
}


def normalize_size(size: str | None) -> str | None:
    """'medium' → 'M', '2xl' → 'XXL'. Returns the input upper-cased if unknown (e.g. 'XXXL')."""
    if not size:
        return None
    key = re.sub(r"\s+", " ", size.strip().lower())
    return SIZE_ALIASES.get(key, size.strip().upper())


def stock_status(quantity: int | None) -> str:
    if quantity is None:
        return "not_offered"
    if quantity <= 0:
        return "sold_out"
    if quantity <= LOW_STOCK_THRESHOLD:
        return "low_stock"
    return "in_stock"


def _norm_name(text: str) -> str:
    t = text.lower().replace("1/4", "1 4").replace("t-shirt", "t shirt").replace("tee", "t shirt")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def resolve_product(ref: str) -> tuple[dict | None, list[dict]]:
    """Find one product from an id or a (partial) name.
    Returns (product, []) when confident, otherwise (None, up to 5 candidates)."""
    ref = (ref or "").strip()
    if not ref:
        return None, []
    p = get_product(ref) or get_product(ref.lower().replace(" ", "-"))
    if p:
        return p, []
    wanted = _norm_name(ref)
    products = load_products()
    exact = [x for x in products if _norm_name(x["name"]) == wanted]
    if len(exact) == 1:
        return get_product(exact[0]["product_id"]), []
    contains = [x for x in products if wanted and wanted in _norm_name(x["name"])]
    if len(contains) == 1:
        return get_product(contains[0]["product_id"]), []
    candidates = contains or search(ref, limit=5)
    if len(candidates) == 1:
        return get_product(candidates[0]["product_id"]), []
    return None, candidates[:5]


def display_name(name: str) -> str:
    """Catalog names come from slugs ("1 4 Zip", "T Shirt"); tidy them for people. Mirrors frontend displayName()."""
    for pat, rep in [(r"\b1 4 Zip\b", "1/4 Zip"), (r"\bT Shirt\b", "T-Shirt"), (r"\bL S\b", "L/S"),
                     (r"\bUa Mens\b", "UA Men's"), (r"\b2 0\b", "2.0"), (r"\bVs\b", "vs.")]:
        name = re.sub(pat, rep, name, flags=re.I)
    return name
