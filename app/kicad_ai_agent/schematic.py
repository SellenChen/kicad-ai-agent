from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import SNAPSHOT_ROOT, ensure_runtime_dirs
from .sexpr import Atom, head, parse, properties, walk


REF_VALUE_RE = re.compile(
    r"(?:把|将|请把|请将)?\s*([A-Z]+[0-9]+)\s*(?:的)?\s*(?:value|值|阻值|容值|参数)?\s*"
    r"(?:改成|修改为|设为|设置为|=|to)\s*([0-9.]+\s*[kKmMuUnNpPfFΩRr]*|[0-9.]+[a-zA-ZΩ]+)",
    re.IGNORECASE,
)

TABLE_PART_RE = re.compile(
    r"^\|\s*([A-Za-z]+\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
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


def ensure_schematic(project_path: Path) -> Path:
    project_path = project_path.resolve()
    if project_path.is_file() and project_path.suffix == ".kicad_sch":
        if not project_path.exists():
            create_empty_schematic(project_path)
        return project_path
    if project_path.is_file() and project_path.suffix == ".kicad_pro":
        candidate = project_path.with_suffix(".kicad_sch")
        if not candidate.exists():
            create_empty_schematic(candidate)
        return candidate
    matches = sorted(project_path.glob("*.kicad_sch")) if project_path.exists() else []
    if matches:
        return matches[0]
    candidate = project_path / f"{project_path.name}.kicad_sch"
    create_empty_schematic(candidate)
    return candidate


def create_empty_schematic(schematic_path: Path) -> None:
    schematic_path.parent.mkdir(parents=True, exist_ok=True)
    schematic_uuid = str(uuid.uuid4())
    schematic_path.write_text(
        f'''(kicad_sch
\t(version 20250114)
\t(generator "kicad-ai-agent")
\t(generator_version "0.2.1")
\t(uuid "{schematic_uuid}")
\t(paper "A4")
\t(lib_symbols)
)
''',
        encoding="utf-8",
    )


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


def plan_parts_from_text(project_path: Path, text: str) -> dict[str, Any]:
    parts = []
    for match in TABLE_PART_RE.finditer(text):
        ref = match.group(1).strip().upper()
        if ref.lower() in {"ref", "reference", "参考位", "位号"}:
            continue
        value = match.group(2).strip()
        footprint = match.group(3).strip()
        lib_id = match.group(4).strip()
        if not lib_id or lib_id in {"同上", "-"}:
            lib_id = "Device:R" if ref.startswith("R") else "Device:C" if ref.startswith("C") else "Device:R"
        parts.append({"ref": ref, "value": value, "footprint": footprint, "lib_id": lib_id})
    if not parts:
        return {"ok": False, "reason": "没有从上一轮回复中识别出可新增的元件表格。"}
    schematic = find_schematic(project_path)
    existing_refs = {item["ref"] for item in summary(schematic)["components"]}
    filtered = [part for part in parts if part["ref"] not in existing_refs]
    return {
        "ok": True,
        "requires_confirmation": True,
        "tool": "schematic.add_parts",
        "arguments": {
            "schematic": str(schematic),
            "parts": filtered,
            "skipped_existing": sorted(set(part["ref"] for part in parts) & existing_refs),
        },
        "validation": ["erc", "netlist"],
    }


def add_parts_preserving_format(schematic_path: Path, parts: list[dict[str, str]]) -> dict[str, Any]:
    if not parts:
        return {"changed": False, "reason": "没有需要新增的元件。"}
    text = schematic_path.read_text(encoding="utf-8")
    insert_at = text.rfind("\n)")
    if insert_at < 0:
        raise ValueError("Could not find schematic root closing parenthesis")
    snapshot_meta = create_snapshot(schematic_path, "add parts from agent plan")
    blocks = []
    x = 25.4
    y = 25.4
    for index, part in enumerate(parts):
        blocks.append(_symbol_block(part, x + (index % 4) * 25.4, y + (index // 4) * 20.32))
    updated = text[:insert_at] + "\n" + "\n".join(blocks) + text[insert_at:]
    schematic_path.write_text(updated, encoding="utf-8")
    return {
        "changed": True,
        "snapshot": snapshot_meta,
        "added": parts,
        "note": "已添加元件实例；当前版本不会自动完成连线，请在 KiCad 中检查位置并继续布线。",
    }


def _symbol_block(part: dict[str, str], x: float, y: float) -> str:
    ref = part["ref"]
    value = part.get("value", "")
    lib_id = part.get("lib_id", "Device:R") or "Device:R"
    footprint = part.get("footprint", "")
    rotation = int(float(part.get("rotation", 0) or 0))
    symbol_uuid = str(uuid.uuid4())
    instance_uuid = str(uuid.uuid4())
    return f'''\t(symbol
\t\t(lib_id "{_escape(lib_id)}")
\t\t(at {x:.2f} {y:.2f} {rotation})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{symbol_uuid}")
\t\t(property "Reference" "{_escape(ref)}"
\t\t\t(at {x:.2f} {y - 2.54:.2f} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "{_escape(value)}"
\t\t\t(at {x:.2f} {y + 2.54:.2f} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Footprint" "{_escape(footprint)}"
\t\t\t(at {x:.2f} {y + 5.08:.2f} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at {x:.2f} {y + 7.62:.2f} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/{instance_uuid}"
\t\t\t\t\t(reference "{_escape(ref)}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)'''


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def plan_circuit_from_prompt(project_path: Path, prompt: str, model_text: str = "") -> dict[str, Any]:
    text = f"{prompt}\n{model_text}".lower()
    if not _looks_like_circuit_generation(text):
        return {"ok": False, "reason": "未识别到电路生成意图。"}
    circuit = _recipe_for_prompt(text)
    schematic = ensure_schematic(project_path)
    return {
        "ok": True,
        "requires_confirmation": True,
        "tool": "schematic.generate_circuit",
        "arguments": {
            "schematic": str(schematic),
            "circuit": circuit,
        },
        "validation": ["erc", "netlist"],
    }


def generate_circuit_preserving_format(schematic_path: Path, circuit: dict[str, Any]) -> dict[str, Any]:
    text = schematic_path.read_text(encoding="utf-8")
    insert_at = text.rfind("\n)")
    if insert_at < 0:
        raise ValueError("Could not find schematic root closing parenthesis")

    snapshot_meta = create_snapshot(schematic_path, f"generate circuit: {circuit.get('name', 'untitled')}")
    existing_refs = {item["ref"] for item in summary(schematic_path)["components"]}
    components = _renumber_conflicting_components(circuit.get("components", []), existing_refs)
    blocks: list[str] = []
    for component in components:
        blocks.append(_symbol_block(component, float(component["x"]), float(component["y"])))
    for wire in circuit.get("wires", []):
        blocks.append(_wire_block(wire))
    for label in circuit.get("labels", []):
        blocks.append(_label_block(label))
    for junction in circuit.get("junctions", []):
        blocks.append(_junction_block(junction))
    for note in circuit.get("notes", []):
        blocks.append(_text_block(note))

    updated = text[:insert_at] + "\n" + "\n".join(blocks) + text[insert_at:]
    schematic_path.write_text(updated, encoding="utf-8")
    return {
        "changed": True,
        "snapshot": snapshot_meta,
        "circuit": circuit.get("name", ""),
        "components": [{"ref": item["ref"], "value": item.get("value", ""), "lib_id": item.get("lib_id", "")} for item in components],
        "wires": len(circuit.get("wires", [])),
        "labels": len(circuit.get("labels", [])),
        "note": "已完成元件摆放和连线。请在 KiCad 中检查位置、符号库解析和 ERC 结果。",
    }


def _looks_like_circuit_generation(text: str) -> bool:
    generation_words = ["生成", "创建", "搭建", "画", "设计", "generate", "create", "build", "draw"]
    circuit_words = ["电路", "滤波", "积分", "微分", "方波", "三角波", "低通", "高通", "wave", "filter", "integrator", "differentiator"]
    return any(word in text for word in generation_words) and any(word in text for word in circuit_words)


def _recipe_for_prompt(text: str) -> dict[str, Any]:
    if ("方波" in text and "三角波" in text) or ("square" in text and "triangle" in text):
        return _recipe_square_to_triangle()
    if "微分" in text or "differentiator" in text or "高通" in text:
        return _recipe_differentiator()
    if "积分" in text or "integrator" in text or "低通" in text:
        return _recipe_integrator()
    return _recipe_integrator()


def _recipe_square_to_triangle() -> dict[str, Any]:
    return {
        "name": "1 kHz square-wave to triangle-wave RC integrator",
        "description": "A first-order RC integrator / low-pass filter. For a 1 kHz square wave, R=10 kOhm and C=47 nF gives tau about 470 us.",
        "components": [
            {"ref": "R1", "value": "10K", "lib_id": "Device:R", "footprint": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "x": 90.0, "y": 70.0, "rotation": 90},
            {"ref": "C1", "value": "47nF", "lib_id": "Device:C", "footprint": "Capacitor_THT:C_Disc_D5.1mm_W3.2mm_P5.00mm", "x": 120.0, "y": 84.0, "rotation": 0},
            {"ref": "#PWR0101", "value": "GND", "lib_id": "power:GND", "footprint": "", "x": 120.0, "y": 99.0, "rotation": 0},
        ],
        "wires": [
            {"points": [[65.0, 70.0], [87.46, 70.0]]},
            {"points": [[92.54, 70.0], [120.0, 70.0]]},
            {"points": [[120.0, 70.0], [120.0, 81.46]]},
            {"points": [[120.0, 86.54], [120.0, 96.46]]},
            {"points": [[120.0, 70.0], [145.0, 70.0]]},
        ],
        "junctions": [{"x": 120.0, "y": 70.0}],
        "labels": [
            {"text": "VIN_1KHZ_SQUARE", "x": 65.0, "y": 70.0, "rotation": 0},
            {"text": "VOUT_TRIANGLE", "x": 145.0, "y": 70.0, "rotation": 0},
        ],
        "notes": [
            {"text": "1 kHz square to triangle filter: R=10K, C=47nF, tau=470us. Output is taken on the capacitor node.", "x": 65.0, "y": 110.0},
        ],
    }


def _recipe_integrator() -> dict[str, Any]:
    return {
        "name": "Simple RC integrator",
        "description": "Passive RC low-pass integrator. Output is measured on the capacitor node.",
        "components": [
            {"ref": "R1", "value": "10K", "lib_id": "Device:R", "footprint": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "x": 90.0, "y": 70.0, "rotation": 90},
            {"ref": "C1", "value": "100nF", "lib_id": "Device:C", "footprint": "Capacitor_THT:C_Disc_D5.1mm_W3.2mm_P5.00mm", "x": 120.0, "y": 84.0, "rotation": 0},
            {"ref": "#PWR0101", "value": "GND", "lib_id": "power:GND", "footprint": "", "x": 120.0, "y": 99.0, "rotation": 0},
        ],
        "wires": [
            {"points": [[65.0, 70.0], [87.46, 70.0]]},
            {"points": [[92.54, 70.0], [120.0, 70.0]]},
            {"points": [[120.0, 70.0], [120.0, 81.46]]},
            {"points": [[120.0, 86.54], [120.0, 96.46]]},
            {"points": [[120.0, 70.0], [145.0, 70.0]]},
        ],
        "junctions": [{"x": 120.0, "y": 70.0}],
        "labels": [
            {"text": "VIN", "x": 65.0, "y": 70.0, "rotation": 0},
            {"text": "VOUT_INT", "x": 145.0, "y": 70.0, "rotation": 0},
        ],
        "notes": [{"text": "Simple RC integrator / low-pass filter. Adjust R*C for the target waveform period.", "x": 65.0, "y": 110.0}],
    }


def _recipe_differentiator() -> dict[str, Any]:
    return {
        "name": "Simple RC differentiator",
        "description": "Passive RC high-pass differentiator. Output is measured on the resistor node.",
        "components": [
            {"ref": "C1", "value": "10nF", "lib_id": "Device:C", "footprint": "Capacitor_THT:C_Disc_D5.1mm_W3.2mm_P5.00mm", "x": 90.0, "y": 70.0, "rotation": 90},
            {"ref": "R1", "value": "10K", "lib_id": "Device:R", "footprint": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "x": 120.0, "y": 84.0, "rotation": 0},
            {"ref": "#PWR0101", "value": "GND", "lib_id": "power:GND", "footprint": "", "x": 120.0, "y": 99.0, "rotation": 0},
        ],
        "wires": [
            {"points": [[65.0, 70.0], [87.46, 70.0]]},
            {"points": [[92.54, 70.0], [120.0, 70.0]]},
            {"points": [[120.0, 70.0], [120.0, 81.46]]},
            {"points": [[120.0, 86.54], [120.0, 96.46]]},
            {"points": [[120.0, 70.0], [145.0, 70.0]]},
        ],
        "junctions": [{"x": 120.0, "y": 70.0}],
        "labels": [
            {"text": "VIN", "x": 65.0, "y": 70.0, "rotation": 0},
            {"text": "VOUT_DIFF", "x": 145.0, "y": 70.0, "rotation": 0},
        ],
        "notes": [{"text": "Simple RC differentiator / high-pass filter. Output pulses appear on the resistor node.", "x": 65.0, "y": 110.0}],
    }


def _renumber_conflicting_components(components: list[dict[str, Any]], existing_refs: set[str]) -> list[dict[str, Any]]:
    used = set(existing_refs)
    result = []
    for component in components:
        updated = dict(component)
        ref = str(updated.get("ref", "")).upper()
        if ref in used:
            prefix = "".join(ch for ch in ref if not ch.isdigit()) or ref
            number = 1
            while f"{prefix}{number}" in used:
                number += 1
            ref = f"{prefix}{number}"
            updated["ref"] = ref
        used.add(ref)
        result.append(updated)
    return result


def _wire_block(wire: dict[str, Any]) -> str:
    points = wire.get("points", [])
    if len(points) < 2:
        raise ValueError("wire requires at least two points")
    point_text = " ".join(f"(xy {float(x):.2f} {float(y):.2f})" for x, y in points)
    return f'''\t(wire
\t\t(pts
\t\t\t{point_text}
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{uuid.uuid4()}")
\t)'''


def _label_block(label: dict[str, Any]) -> str:
    text = str(label.get("text", "NET"))
    x = float(label.get("x", 0))
    y = float(label.get("y", 0))
    rotation = int(float(label.get("rotation", 0) or 0))
    return f'''\t(label "{_escape(text)}"
\t\t(at {x:.2f} {y:.2f} {rotation})
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify left bottom)
\t\t)
\t\t(uuid "{uuid.uuid4()}")
\t)'''


def _junction_block(junction: dict[str, Any]) -> str:
    x = float(junction.get("x", 0))
    y = float(junction.get("y", 0))
    return f'''\t(junction
\t\t(at {x:.2f} {y:.2f})
\t\t(diameter 0)
\t\t(color 0 0 0 0)
\t\t(uuid "{uuid.uuid4()}")
\t)'''


def _text_block(note: dict[str, Any]) -> str:
    text = str(note.get("text", ""))
    x = float(note.get("x", 0))
    y = float(note.get("y", 0))
    return f'''\t(text "{_escape(text)}"
\t\t(at {x:.2f} {y:.2f} 0)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify left bottom)
\t\t)
\t\t(uuid "{uuid.uuid4()}")
\t)'''
