from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import SNAPSHOT_ROOT, ensure_runtime_dirs
from .sexpr import Atom, head, parse, properties, walk


REF_VALUE_RE = re.compile(
    r'(?:把|将)?\s*([A-Z]+[0-9]+)\s*(?:的)?(?:value|阻值|值|参数)?\s*(?:改成|修改为|设为|=)\s*([0-9.]+\s*[kKmMuUnNpPfF]?|[0-9.]+[a-zA-Z]+)'
)


@dataclass
class Component:
    ref: str
    value: str
    footprint: str = ""


def find_schematic(project_path: Path) -> Path:
    project_path = project_path.resolve()
    if project_path.is_file() and project_path.suffix == ".kicad_sch":
        return project_path
    if project_path.is_file() and project_path.suffix == ".kicad_pro":
        candidate = project_path.with_suffix(".kicad_sch")
        if candidate.exists():
            return candidate
        project_path = project_path.parent
    matches = sorted(project_path.glob("*.kicad_sch"))
    if not matches:
        raise FileNotFoundError(f"No .kicad_sch found under {project_path}")
    return matches[0]


def project_file_for(schematic_path: Path) -> Path | None:
    candidate = schematic_path.with_suffix(".kicad_pro")
    return candidate if candidate.exists() else None


def summary(schematic_path: Path) -> dict[str, Any]:
    text = schematic_path.read_text(encoding="utf-8")
    root = parse(text)
    result: dict[str, Any] = {
        "path": str(schematic_path),
        "version": "",
        "placed_symbols": 0,
        "library_symbols": 0,
        "wires": 0,
        "labels": 0,
        "components": [],
    }
    components: list[Component] = []
    for node in walk(root):
        node_head = head(node)
        if node_head == "version" and len(node) >= 2 and isinstance(node[1], Atom):
            result["version"] = node[1].value
        elif node_head == "symbol":
            if len(node) >= 2 and isinstance(node[1], Atom):
                result["library_symbols"] += 1
            else:
                props = properties(node)
                if "Reference" in props:
                    result["placed_symbols"] += 1
                    components.append(
                        Component(
                            ref=props.get("Reference", ""),
                            value=props.get("Value", ""),
                            footprint=props.get("Footprint", ""),
                        )
                    )
        elif node_head == "wire":
            result["wires"] += 1
        elif node_head in {"label", "global_label", "hierarchical_label"}:
            result["labels"] += 1
    result["components"] = [
        component.__dict__
        for component in sorted(components, key=lambda item: item.ref)
    ]
    return result


def parse_value_request(prompt: str) -> tuple[str, str] | None:
    match = REF_VALUE_RE.search(prompt)
    if not match:
        return None
    return match.group(1).upper(), match.group(2).replace(" ", "")


def component_by_ref(schematic_path: Path, reference: str) -> dict[str, str] | None:
    for item in summary(schematic_path)["components"]:
        if item["ref"] == reference:
            return item
    return None


def _matching_paren(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Could not find matching closing parenthesis")


def _find_symbol_block(text: str, reference: str) -> tuple[int, int]:
    ref_pattern = re.compile(r'\(\s*property\s+"Reference"\s+"' + re.escape(reference) + r'"')
    match = ref_pattern.search(text)
    if not match:
        raise ValueError(f"Reference {reference} not found")
    symbol_start = text.rfind("(symbol", 0, match.start())
    if symbol_start < 0:
        raise ValueError(f"Could not locate symbol block for {reference}")
    symbol_end = _matching_paren(text, symbol_start) + 1
    return symbol_start, symbol_end


def _find_property_value_span(symbol_text: str, property_name: str) -> tuple[int, int, str]:
    pattern = re.compile(
        r'(\(\s*property\s+"' + re.escape(property_name) + r'"\s+")((?:\\.|[^"\\])*)(")',
        re.MULTILINE,
    )
    match = pattern.search(symbol_text)
    if not match:
        raise ValueError(f"Property {property_name} not found")
    return match.start(2), match.end(2), match.group(2)


def create_snapshot(schematic_path: Path, reason: str) -> dict[str, str]:
    ensure_runtime_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = schematic_path.stem.replace(" ", "_")
    target_dir = SNAPSHOT_ROOT / f"{stamp}-{safe_name}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / schematic_path.name
    shutil.copy2(schematic_path, target_file)
    project_file = project_file_for(schematic_path)
    copied_project = None
    if project_file:
        copied_project = target_dir / project_file.name
        shutil.copy2(project_file, copied_project)
    meta = {
        "created_at": stamp,
        "reason": reason,
        "source": str(schematic_path),
        "snapshot": str(target_file),
        "project": str(copied_project) if copied_project else "",
    }
    (target_dir / "snapshot.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def restore_snapshot(snapshot_file: Path) -> dict[str, str]:
    meta_path = snapshot_file.parent / "snapshot.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Snapshot metadata not found: {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    shutil.copy2(snapshot_file, meta["source"])
    return meta


def set_property_preserving_format(
    schematic_path: Path,
    reference: str,
    property_name: str,
    new_value: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    text = schematic_path.read_text(encoding="utf-8")
    symbol_start, symbol_end = _find_symbol_block(text, reference)
    symbol_text = text[symbol_start:symbol_end]
    value_start, value_end, old_value = _find_property_value_span(symbol_text, property_name)
    absolute_start = symbol_start + value_start
    absolute_end = symbol_start + value_end
    updated = text[:absolute_start] + new_value + text[absolute_end:]
    before_line = text.count("\n", 0, absolute_start) + 1
    diff = {
        "reference": reference,
        "property": property_name,
        "old_value": old_value,
        "new_value": new_value,
        "line": before_line,
        "preview": [
            f'- (property "{property_name}" "{old_value}")',
            f'+ (property "{property_name}" "{new_value}")',
        ],
    }
    if dry_run:
        return {"changed": old_value != new_value, "dry_run": True, "diff": diff}
    snapshot_meta = create_snapshot(schematic_path, f"set {reference}.{property_name} to {new_value}")
    schematic_path.write_text(updated, encoding="utf-8")
    return {
        "changed": old_value != new_value,
        "dry_run": False,
        "snapshot": snapshot_meta,
        "diff": diff,
    }


def plan_from_prompt(project_path: Path, prompt: str) -> dict[str, Any]:
    parsed = parse_value_request(prompt)
    if not parsed:
        return {"ok": False, "reason": "未识别到元件参数修改意图。"}
    reference, new_value = parsed
    schematic = find_schematic(project_path)
    component = component_by_ref(schematic, reference)
    if component is None:
        return {"ok": False, "reason": f"没有找到 {reference}。", "schematic": str(schematic)}
    return {
        "ok": True,
        "requires_confirmation": True,
        "tool": "schematic.set_property",
        "arguments": {
            "schematic": str(schematic),
            "reference": reference,
            "property": "Value",
            "old_value": component["value"],
            "new_value": new_value,
        },
        "validation": ["erc", "netlist"],
    }
