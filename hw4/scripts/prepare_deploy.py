#!/usr/bin/env python3
"""Render build step: check the data pack is present, then do the first-start upgrade at build time
(database tables + Problem 2 fixes, Problem 3 white photo backgrounds) so the live site starts fast."""
import os
import sys
from pathlib import Path

# Render attaches the persistent disk only when the site runs, not during the build. The build prepares the data pack
# inside the repo (data/); the running site copies the database to the disk on its first boot (db.py).
os.environ.pop("DATA_PERSIST_DIR", None)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

db_file, photos = ROOT / "data" / "campus_customs.db", list((ROOT / "data" / "products").glob("*.jpg"))
if not db_file.exists() or not photos:
    sys.exit("Data pack missing: data/campus_customs.db and data/products/*.jpg must be in the deploy repo.")
if not (ROOT / "frontend" / "dist" / "index.html").exists():
    sys.exit("frontend/dist is missing: run `npm run build` in frontend/ before syncing the deploy repo.")

import db  # noqa: E402
import prepare_data  # noqa: E402

db.ensure_schema()
prepare_data.prepare_product_photos()
print(f"Deploy data ready: {len(photos)} product photos, database upgraded.")
