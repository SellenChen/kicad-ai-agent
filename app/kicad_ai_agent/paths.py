from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "app"
STATIC_ROOT = APP_ROOT / "static"
DATA_ROOT = REPO_ROOT / "work" / "stage1_runtime"
SNAPSHOT_ROOT = DATA_ROOT / "snapshots"
REPORT_ROOT = DATA_ROOT / "reports"

DEFAULT_KICAD_CLI = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")


def ensure_runtime_dirs() -> None:
    SNAPSHOT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)


def kicad_cli_path() -> Path:
    configured = os.environ.get("KICAD_AGENT_KICAD_CLI")
    if configured:
        return Path(configured)
    return DEFAULT_KICAD_CLI
