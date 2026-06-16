from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import REPORT_ROOT, ensure_runtime_dirs, kicad_cli_path


def _run(args: list[str], timeout: int = 60) -> dict[str, Any]:
    exe = kicad_cli_path()
    command = [str(exe)] + args
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ok": completed.returncode == 0,
    }


def _report_path(prefix: str, suffix: str) -> Path:
    ensure_runtime_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return REPORT_ROOT / f"{stamp}-{prefix}.{suffix}"


def erc(schematic_path: Path) -> dict[str, Any]:
    output = _report_path(schematic_path.stem + "-erc", "json")
    result = _run([
        "sch",
        "erc",
        "--format",
        "json",
        "--severity-all",
        "--output",
        str(output),
        str(schematic_path),
    ])
    result["report"] = str(output)
    if output.exists():
        data = json.loads(output.read_text(encoding="utf-8"))
        count = sum(len(sheet.get("violations", [])) for sheet in data.get("sheets", []))
        result["summary"] = {
            "kicad_version": data.get("kicad_version"),
            "violations": count,
            "schema": data.get("$schema"),
        }
    return result


def export_netlist(schematic_path: Path, fmt: str = "kicadsexpr") -> dict[str, Any]:
    suffix = "cir" if fmt == "spice" else "net"
    output = _report_path(schematic_path.stem + f"-{fmt}", suffix)
    result = _run([
        "sch",
        "export",
        "netlist",
        "--format",
        fmt,
        "--output",
        str(output),
        str(schematic_path),
    ])
    result["output"] = str(output)
    result["size"] = output.stat().st_size if output.exists() else 0
    return result


def drc(board_path: Path) -> dict[str, Any]:
    output = _report_path(board_path.stem + "-drc", "json")
    result = _run([
        "pcb",
        "drc",
        "--format",
        "json",
        "--severity-all",
        "--output",
        str(output),
        str(board_path),
    ])
    result["report"] = str(output)
    if output.exists():
        data = json.loads(output.read_text(encoding="utf-8"))
        result["summary"] = {
            "kicad_version": data.get("kicad_version"),
            "violations": len(data.get("violations", [])),
            "unconnected": len(data.get("unconnected_items", [])),
            "schema": data.get("$schema"),
        }
    return result


def validate_schematic(schematic_path: Path) -> dict[str, Any]:
    erc_result = erc(schematic_path)
    netlist_result = export_netlist(schematic_path)
    return {
        "erc": erc_result,
        "netlist": netlist_result,
        "ok": erc_result.get("ok") and netlist_result.get("ok"),
    }
