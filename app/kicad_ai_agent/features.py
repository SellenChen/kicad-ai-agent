from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .kicad_cli import erc
from .schematic import summary


def component_family(reference: str) -> str:
    prefix = ""
    for char in reference:
        if char.isalpha() or char in "#+":
            prefix += char
        else:
            break
    return prefix or "unknown"


def extract_schematic_features(schematic_path: Path, *, max_components: int = 120, include_erc: bool = False) -> dict[str, Any]:
    data = summary(schematic_path)
    components = data.get("components", [])
    family_counter = Counter(component_family(item["ref"]) for item in components)
    value_counter = Counter(item["value"] for item in components if item.get("value"))
    power_symbols = [
        item for item in components
        if item["ref"].startswith("#") or item["value"] in {"+12V", "+5V", "+3V3", "GND", "VCC", "VDD"}
    ]
    active_parts = [
        item for item in components
        if component_family(item["ref"]) in {"Q", "U", "D", "J", "P"}
    ]
    features: dict[str, Any] = {
        "schematic_path": str(schematic_path),
        "version": data.get("version"),
        "counts": {
            "placed_symbols": data.get("placed_symbols"),
            "library_symbols": data.get("library_symbols"),
            "wires": data.get("wires"),
            "labels": data.get("labels"),
            "components": len(components),
        },
        "component_families": dict(sorted(family_counter.items())),
        "common_values": value_counter.most_common(20),
        "power_symbols": power_symbols[:30],
        "active_parts": active_parts[:50],
        "components": components[:max_components],
    }
    if include_erc:
        try:
            erc_result = erc(schematic_path)
            features["erc"] = erc_result.get("summary", {})
        except Exception as exc:
            features["erc_error"] = str(exc)
    return features
