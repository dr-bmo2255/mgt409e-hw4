"""Automated QA. Anything visual that code can't judge is flagged NEEDS_REVIEW, never claimed as verified."""

import hashlib
import io
import re

from PIL import Image, ImageStat

from . import config

NAME_RX = re.compile(r"^dan_[a-z0-9_]+_v\d{2}\.png$")
HUMAN_CHECKS = [
    "Original Dan likeness (compare to references)", "English bulldog anatomy, believable paws/limbs",
    "Equipment / setting accuracy", "Exact text only (no gibberish)", "Correct supplied shield (or none)",
    "Single scene, no collage, no watermark",
]


def check_png(data: bytes, filename: str, known_hashes: set[str], has_shield_asset: bool) -> dict:
    warnings, passed = [], []
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
        fmt = im.format
    except Exception as e:
        return {"ok": False, "errors": [f"PNG does not decode: {e}"], "warnings": [], "passed": [], "needs_review": HUMAN_CHECKS}
    errors = []
    if fmt != "PNG":
        errors.append(f"Format is {fmt}, expected PNG")
    w, h = im.size
    if min(w, h) < 1024:
        errors.append(f"Too small: {w}×{h} (min 1024)")
    else:
        passed.append(f"Resolution {w}×{h}")
    if w != h:
        warnings.append(f"Not square: {w}×{h}")
    stat = ImageStat.Stat(im.convert("L"))
    if stat.stddev[0] < 8:
        errors.append("Image looks blank / flat")
    else:
        passed.append("Not blank")
    digest = hashlib.sha256(data).hexdigest()
    if digest in known_hashes:
        errors.append("Exact duplicate of an earlier version")
    else:
        passed.append("Unique")
    if not NAME_RX.match(filename):
        errors.append(f"Unexpected filename {filename}")
    else:
        passed.append("Filename convention")
    if has_shield_asset:
        warnings.append("Shield fidelity must be checked by a human (or use 'Composite exact shield')")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "passed": passed, "needs_review": HUMAN_CHECKS,
            "sha256": digest, "width": w, "height": h}


def secrets_leak_scan(paths) -> list[str]:
    """Make sure no exported text file contains anything that looks like a key."""
    rx = re.compile(r"(sk-[A-Za-z0-9]{16,}|PORTKEY_API_KEY\s*=\s*\S+|OPENAI_API_KEY\s*=\s*\S+)")
    hits = []
    for p in paths:
        try:
            if rx.search(open(p, errors="ignore").read()):
                hits.append(str(p))
        except (IsADirectoryError, FileNotFoundError):
            pass
    return hits


def thumbnail(data: bytes, out_path, size: int = 384) -> None:
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((size, size))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path, "JPEG", quality=85)


__all__ = ["check_png", "thumbnail", "secrets_leak_scan", "HUMAN_CHECKS", "config"]
