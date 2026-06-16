from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import DEFAULT_KICAD_CLI, REPORT_ROOT, SNAPSHOT_ROOT, STATIC_ROOT, kicad_cli_path


def environment_report(project_path: Path) -> dict[str, Any]:
    cli = kicad_cli_path()
    return {
        "project": str(project_path),
        "kicad_cli": {
            "configured": str(cli),
            "exists": cli.exists(),
            "default": str(DEFAULT_KICAD_CLI),
        },
        "runtime": {
            "snapshots": str(SNAPSHOT_ROOT),
            "snapshots_exists": SNAPSHOT_ROOT.exists(),
            "reports": str(REPORT_ROOT),
            "reports_exists": REPORT_ROOT.exists(),
            "static": str(STATIC_ROOT),
            "static_exists": STATIC_ROOT.exists(),
        },
    }


def explain_erc_report(report_path: Path) -> dict[str, Any]:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    groups: dict[str, dict[str, Any]] = {}
    for sheet in data.get("sheets", []):
        sheet_path = sheet.get("path", "/")
        for violation in sheet.get("violations", []):
            description = violation.get("description", "未知问题")
            group = groups.setdefault(
                description,
                {
                    "description": description,
                    "count": 0,
                    "severity": violation.get("severity", ""),
                    "examples": [],
                    "suggestion": _suggestion_for(description),
                },
            )
            group["count"] += 1
            if len(group["examples"]) < 3:
                items = violation.get("items", [])
                group["examples"].append(
                    {
                        "sheet": sheet_path,
                        "items": [item.get("description", "") for item in items[:2]],
                    }
                )
    return {
        "report": str(report_path),
        "kicad_version": data.get("kicad_version"),
        "groups": sorted(groups.values(), key=lambda item: item["count"], reverse=True),
    }


def _suggestion_for(description: str) -> str:
    lower = description.lower()
    if "power" in lower or "电源" in description:
        return "检查电源输入脚是否由电源输出脚或 PWR_FLAG 驱动。"
    if "not connected" in lower or "未连接" in description:
        return "确认该引脚是否应连接；如果故意悬空，可添加 no-connect 标记。"
    if "simulation" in lower or "spice" in lower:
        return "检查器件是否已设置 SPICE 模型、引脚映射和仿真参数。"
    if "label" in lower:
        return "检查标签是否拼写一致，单独出现的全局标签可能没有实际连接对象。"
    return "打开对应位置检查原理图对象，必要时重新运行 ERC 验证修复结果。"
