from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

import pcbnew

try:
    from .config import APP_ROOT, REPO_ROOT
except Exception:
    REPO_ROOT = Path(__file__).resolve().parents[3]
    APP_ROOT = REPO_ROOT / "app"


DEFAULT_PORT = "8765"


class KiCadAIAgentLauncher(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiCad AI Agent"
        self.category = "AI Assistant"
        self.description = "Launch the KiCad AI Agent side panel"
        self.show_toolbar_button = True

    def Run(self):
        project = self._project_path()
        port = os.environ.get("KICAD_AI_AGENT_PORT", DEFAULT_PORT)
        url = f"http://127.0.0.1:{port}"
        command = [
            self._python_executable(),
            str(APP_ROOT / "run_agent.py"),
            "--project",
            str(project),
            "--host",
            "127.0.0.1",
            "--port",
            port,
        ]

        if os.environ.get("KICAD_AI_AGENT_DRY_RUN") == "1":
            print("KiCad AI Agent dry run:")
            print(" ".join(f'"{part}"' if " " in part else part for part in command))
            print(url)
            return None

        process = None
        if not self._service_healthy(url):
            process = subprocess.Popen(
                command,
                cwd=str(APP_ROOT),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._wait_until_ready(url)

        if os.environ.get("KICAD_AI_AGENT_NO_BROWSER") != "1":
            webbrowser.open(url)
        print(f"KiCad AI Agent opened at {url}")
        return process

    def _project_path(self) -> Path:
        override = os.environ.get("KICAD_AI_AGENT_PROJECT")
        if override:
            return Path(override)

        board = pcbnew.GetBoard()
        if board:
            board_path = Path(board.GetFileName())
            if board_path.exists():
                project_path = board_path.with_suffix(".kicad_pro")
                return project_path if project_path.exists() else board_path

        return REPO_ROOT

    def _python_executable(self) -> str:
        return os.environ.get("KICAD_AI_AGENT_PYTHON", sys.executable)

    def _service_healthy(self, url: str) -> bool:
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=0.5) as response:
                return response.status == 200
        except Exception:
            return False

    def _wait_until_ready(self, url: str) -> None:
        last_error = None
        for _ in range(40):
            if self._service_healthy(url):
                return
            time.sleep(0.25)
        if last_error:
            print(last_error)
