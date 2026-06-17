from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import json
import urllib.request
import webbrowser
from pathlib import Path

import pcbnew

try:
    from .config import APP_ROOT, KICAD_PYTHON, REPO_ROOT
except Exception:
    REPO_ROOT = Path(__file__).resolve().parents[3]
    APP_ROOT = REPO_ROOT / "app"
    KICAD_PYTHON = Path(r"C:\Program Files\KiCad\10.0\bin\python.exe")


DEFAULT_PORT = "8765"


class KiCadAIAgentLauncher(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiCad AI Agent"
        self.category = "AI Assistant"
        self.description = "Launch the KiCad AI Agent side panel"
        self.show_toolbar_button = True

    def Run(self):
        project = self._project_path()
        port = self._choose_port(int(os.environ.get("KICAD_AI_AGENT_PORT", DEFAULT_PORT)), project)
        url = f"http://127.0.0.1:{port}"
        command = [
            self._python_executable(),
            str(APP_ROOT / "run_agent.py"),
            "--project",
            str(project),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]

        if os.environ.get("KICAD_AI_AGENT_DRY_RUN") == "1":
            print("KiCad AI Agent dry run:")
            print(" ".join(f'"{part}"' if " " in part else part for part in command))
            print(url)
            return None

        process = None
        self._write_launch_log(command, project, url)
        if not self._service_for_project(url, project):
            process = subprocess.Popen(
                command,
                cwd=str(APP_ROOT),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._wait_until_ready(url)

        if os.environ.get("KICAD_AI_AGENT_NO_BROWSER") != "1":
            self._open_side_panel(url)
        print(f"KiCad AI Agent opened at {url}")
        return process

    def _project_path(self) -> Path:
        override = os.environ.get("KICAD_AI_AGENT_PROJECT")
        if override:
            return self._normalize_project(Path(override))

        for candidate in self._project_candidates_from_kicad():
            normalized = self._normalize_project(candidate)
            if normalized.exists():
                return normalized

        recent = self._recent_kicad_project()
        if recent:
            return recent

        return REPO_ROOT

    def _project_candidates_from_kicad(self) -> list[Path]:
        candidates: list[Path] = []
        board = pcbnew.GetBoard()
        if board:
            for method_name in ("GetFileName", "GetProject"):
                method = getattr(board, method_name, None)
                if not method:
                    continue
                try:
                    value = method()
                except Exception:
                    continue
                candidates.extend(self._paths_from_value(value))

        for name in ("GetCurrentProject", "GetProject"):
            func = getattr(pcbnew, name, None)
            if not func:
                continue
            try:
                project = func()
            except Exception:
                continue
            candidates.extend(self._paths_from_value(project))

        candidates.extend([Path.cwd(), Path(os.getcwd())])
        return candidates

    def _paths_from_value(self, value) -> list[Path]:
        paths: list[Path] = []
        if value is None:
            return paths
        if isinstance(value, (str, os.PathLike)):
            text = str(value)
            if text:
                paths.append(Path(text))
            return paths
        for method_name in ("GetProjectFullName", "GetProjectPath", "GetFileName", "GetPath"):
            method = getattr(value, method_name, None)
            if not method:
                continue
            try:
                text = str(method())
            except Exception:
                continue
            if text:
                paths.append(Path(text))
        return paths

    def _normalize_project(self, path: Path) -> Path:
        path = path.expanduser()
        if path.is_file():
            if path.suffix.lower() in {".kicad_pcb", ".kicad_sch"}:
                project = path.with_suffix(".kicad_pro")
                return project if project.exists() else path
            return path
        if path.is_dir():
            projects = sorted(path.glob("*.kicad_pro"))
            if projects:
                same_name = path / f"{path.name}.kicad_pro"
                return same_name if same_name.exists() else projects[0]
            boards = sorted(path.glob("*.kicad_pcb"))
            if boards:
                return boards[0]
            schematics = sorted(path.glob("*.kicad_sch"))
            if schematics:
                return schematics[0]
        return path

    def _recent_kicad_project(self) -> Path | None:
        config_root = Path(os.environ.get("APPDATA", "")) / "kicad"
        if not config_root.exists():
            return None
        settings_files = sorted(
            list(config_root.rglob("eeschema.json")) + list(config_root.rglob("pcbnew.json")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        pattern = re.compile(r"[A-Za-z]:\\\\(?:[^\"\\\\]|\\\\.)+?\\.kicad_(?:pro|sch|pcb)")
        for settings_file in settings_files:
            try:
                raw = settings_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for match in pattern.finditer(raw):
                candidate = Path(match.group(0).replace("\\\\", "\\"))
                normalized = self._normalize_project(candidate)
                if normalized.exists():
                    return normalized
        return None

    def _python_executable(self) -> str:
        override = os.environ.get("KICAD_AI_AGENT_PYTHON")
        if override:
            return override
        if KICAD_PYTHON.exists():
            return str(KICAD_PYTHON)
        sibling_python = Path(sys.executable).with_name("python.exe")
        if sibling_python.exists():
            return str(sibling_python)
        return sys.executable

    def _write_launch_log(self, command: list[str], project: Path, url: str) -> None:
        try:
            log_dir = APP_ROOT.parent / "work" / "stage2_runtime" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            last_project = APP_ROOT.parent / "work" / "stage2_runtime" / "last_project.txt"
            last_project.parent.mkdir(parents=True, exist_ok=True)
            last_project.write_text(str(project), encoding="utf-8")
            (log_dir / "kicad_plugin_launch.log").write_text(
                "\n".join(
                    [
                        f"project={project}",
                        f"url={url}",
                        "command=" + " ".join(f'"{part}"' if " " in part else part for part in command),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    def _open_side_panel(self, url: str) -> None:
        edge_candidates = [
            Path(os.environ.get("ProgramFiles", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ]
        for edge in edge_candidates:
            if edge.exists():
                subprocess.Popen(
                    [
                        str(edge),
                        f"--app={url}",
                        "--window-size=430,920",
                        "--window-position=1480,40",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
        webbrowser.open(url)

    def _service_healthy(self, url: str) -> bool:
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=0.5) as response:
                return response.status == 200
        except Exception:
            return False

    def _service_for_project(self, url: str, project: Path) -> bool:
        if not self._service_healthy(url):
            return False
        try:
            with urllib.request.urlopen(f"{url}/api/project", timeout=0.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            running_project = Path(str(payload.get("project", ""))).resolve()
            return running_project == project.resolve()
        except Exception:
            return False

    def _choose_port(self, start_port: int, project: Path) -> int:
        for candidate in range(start_port, start_port + 20):
            url = f"http://127.0.0.1:{candidate}"
            if self._service_for_project(url, project):
                return candidate
            if not self._service_healthy(url):
                return candidate
        raise RuntimeError("No available KiCad AI Agent port found for the current project.")

    def _wait_until_ready(self, url: str) -> None:
        last_error = None
        for _ in range(40):
            if self._service_healthy(url):
                return
            time.sleep(0.25)
        if last_error:
            print(last_error)
