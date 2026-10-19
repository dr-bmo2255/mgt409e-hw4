"""First-start preparation of the assignment's data pack (it is never committed, so graders bring the original).

Problem 3 gave 74 product photos white backgrounds (the originals were transparent PNGs flattened onto black).
On first start this re-applies exactly that fix (same script, byte-identical output): the original photos are kept in
data/products_original/, the white-background versions are written to data/products/, and a marker file stops it
from ever running twice. The database's Problem 2 fixes are applied separately by db.ensure_schema().
"""

import importlib.util
import shutil
import time

from db import DATA_DIR, PROJECT_DIR

PRODUCTS = DATA_DIR / "products"
ORIGINALS = DATA_DIR / "products_original"
MARKER = PRODUCTS / ".white_backgrounds_applied"
SCRIPT = PROJECT_DIR / "scripts" / "whiten_image_backgrounds.py"


def prepare_product_photos() -> None:
    photos = sorted(PRODUCTS.glob("*.jpg")) if PRODUCTS.exists() else []
    if MARKER.exists() or not photos or not SCRIPT.exists():
        return
    started = time.time()
    print(f"[setup] First start: giving product photos white backgrounds (one time, ~30 s). Originals → {ORIGINALS.name}/")
    ORIGINALS.mkdir(exist_ok=True)
    for f in photos:
        if not (ORIGINALS / f.name).exists():
            shutil.copy2(f, ORIGINALS / f.name)
    spec = importlib.util.spec_from_file_location("whiten_image_backgrounds", SCRIPT)
    whiten = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(whiten)
    n = whiten.whiten_folder(ORIGINALS, PRODUCTS, verbose=False)
    MARKER.write_text(f"{n} photos whitened by backend/prepare_data.py\n")
    print(f"[setup] Done: {n} of {len(photos)} photos updated in {time.time() - started:.0f} s.")
