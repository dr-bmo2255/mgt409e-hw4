"""Defensive ZIP extraction: no zip-slip, no decompression bombs, skip macOS junk."""

import zipfile
from pathlib import Path, PurePosixPath

MAX_TOTAL_BYTES = 2 * 1024**3  # 2 GB uncompressed per archive
MAX_FILE_BYTES = 300 * 1024**2  # 300 MB per member
MAX_RATIO = 200  # compression ratio above this looks like a bomb
MAX_MEMBERS = 5000


class UnsafeZip(Exception):
    pass


def is_junk(name: str) -> bool:
    parts = PurePosixPath(name).parts
    base = parts[-1] if parts else ""
    return (
        "__MACOSX" in parts
        or base in (".DS_Store", "")
        or base.startswith("._")
        or base.startswith("~$")  # Office lock files
    )


def safe_extract(zip_path: Path, dest: Path, only: tuple[str, ...] | None = None) -> list[Path]:
    """Extract members (optionally only those whose suffix is in `only`) into dest.
    Returns the extracted file paths. Existing identical files are left as-is (idempotent)."""
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_MEMBERS:
            raise UnsafeZip(f"{zip_path.name}: too many members ({len(infos)})")
        total = 0
        for info in infos:
            if info.is_dir() or is_junk(info.filename):
                continue
            if only and not info.filename.lower().endswith(only):
                continue
            if info.file_size > MAX_FILE_BYTES:
                raise UnsafeZip(f"{info.filename}: member too large")
            if info.compress_size and info.file_size / info.compress_size > MAX_RATIO:
                raise UnsafeZip(f"{info.filename}: suspicious compression ratio")
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                raise UnsafeZip(f"{zip_path.name}: archive expands too large")
            # macOS zips may store non-UTF8 names; normalize odd narrow no-break spaces.
            name = info.filename.replace(" ", " ")
            target = (dest / name).resolve()
            if dest not in target.parents:
                raise UnsafeZip(f"{info.filename}: path escapes destination (zip-slip)")
            if target.exists() and target.stat().st_size == info.file_size:
                out.append(target)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".part")
            with zf.open(info) as src, open(tmp, "wb") as dst:
                written = 0
                while chunk := src.read(1 << 20):
                    written += len(chunk)
                    if written > MAX_FILE_BYTES:
                        raise UnsafeZip(f"{info.filename}: expands beyond declared size")
                    dst.write(chunk)
            tmp.replace(target)  # atomic
            out.append(target)
    return out
