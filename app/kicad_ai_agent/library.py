from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_KICAD_SHARE = Path(r"C:\Program Files\KiCad\10.0\share\kicad")


def _match_files(root: Path, pattern: str, query: str, limit: int) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    query_lower = query.lower()
    results: list[dict[str, Any]] = []
    for path in root.rglob(pattern):
        haystack = path.stem.lower()
        if query_lower in haystack:
            results.append({"name": path.stem, "path": str(path), "type": path.suffix.lstrip(".")})
            if len(results) >= limit:
                break
    return results


def search_symbols(query: str, limit: int = 30) -> dict[str, Any]:
    root = DEFAULT_KICAD_SHARE / "symbols"
    results = _match_files(root, "*.kicad_sym", query, limit)
    return {"root": str(root), "query": query, "results": results}


def search_footprints(query: str, limit: int = 30) -> dict[str, Any]:
    root = DEFAULT_KICAD_SHARE / "footprints"
    results = _match_files(root, "*.kicad_mod", query, limit)
    return {"root": str(root), "query": query, "results": results}
