from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import __version__
from .diagnostics import environment_report, explain_erc_report
from .kicad_cli import export_netlist, validate_schematic
from .library import search_footprints, search_symbols
from .paths import REPORT_ROOT, SNAPSHOT_ROOT, STATIC_ROOT, ensure_runtime_dirs
from .provider import make_provider
from .schematic import (
    find_schematic,
    plan_from_prompt,
    restore_snapshot,
    set_property_preserving_format,
    summary,
)


class AgentState:
    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()
        self.provider = make_provider()

    @property
    def schematic_path(self) -> Path:
        return find_schematic(self.project_path)


class AgentHandler(BaseHTTPRequestHandler):
    state: AgentState

    def log_message(self, _format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._json(404, {"ok": False, "error": "not_found"})
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            route = parsed.path
            if route == "/":
                self._file(STATIC_ROOT / "index.html")
            elif route.startswith("/static/"):
                self._file(STATIC_ROOT / route.removeprefix("/static/"))
            elif route == "/api/health":
                self._json(200, {"ok": True, "version": __version__, "service": "kicad-ai-agent"})
            elif route == "/api/project":
                schematic = self.state.schematic_path
                self._json(200, {"ok": True, "project": str(self.state.project_path), "schematic": str(schematic)})
            elif route == "/api/project/summary":
                self._json(200, {"ok": True, "summary": summary(self.state.schematic_path)})
            elif route == "/api/snapshots":
                ensure_runtime_dirs()
                items = []
                for meta_path in sorted(SNAPSHOT_ROOT.glob("*/snapshot.json"), reverse=True):
                    try:
                        items.append(json.loads(meta_path.read_text(encoding="utf-8")))
                    except Exception:
                        continue
                self._json(200, {"ok": True, "snapshots": items})
            elif route == "/api/reports":
                ensure_runtime_dirs()
                reports = [
                    {"path": str(path), "name": path.name, "size": path.stat().st_size}
                    for path in sorted(REPORT_ROOT.glob("*"), reverse=True)
                    if path.is_file()
                ]
                self._json(200, {"ok": True, "reports": reports})
            elif route == "/api/diagnostics":
                self._json(200, {"ok": True, "diagnostics": environment_report(self.state.project_path)})
            elif route == "/api/file":
                query = parse_qs(parsed.query)
                file_path = Path(query.get("path", [""])[0])
                if not file_path.exists():
                    self._json(404, {"ok": False, "error": "file_not_found"})
                else:
                    self._json(200, {"ok": True, "path": str(file_path), "text": file_path.read_text(encoding="utf-8", errors="replace")})
            else:
                self._json(404, {"ok": False, "error": "not_found"})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:
        try:
            route = urlparse(self.path).path
            body = self._read_json()
            if route == "/api/chat":
                message = str(body.get("message", ""))
                provider_reply = self.state.provider.chat([{"role": "user", "content": message}])
                plan = plan_from_prompt(self.state.project_path, message)
                self._json(200, {"ok": True, "reply": provider_reply, "plan": plan})
            elif route == "/api/tools/set-value/preview":
                reference = str(body["reference"]).upper()
                value = str(body["value"])
                result = set_property_preserving_format(self.state.schematic_path, reference, "Value", value, dry_run=True)
                self._json(200, {"ok": True, "result": result})
            elif route == "/api/tools/set-value/apply":
                reference = str(body["reference"]).upper()
                value = str(body["value"])
                result = set_property_preserving_format(self.state.schematic_path, reference, "Value", value)
                validation = validate_schematic(self.state.schematic_path)
                self._json(200, {"ok": True, "result": result, "validation": validation})
            elif route == "/api/validate":
                self._json(200, {"ok": True, "validation": validate_schematic(self.state.schematic_path)})
            elif route == "/api/export/spice":
                self._json(200, {"ok": True, "result": export_netlist(self.state.schematic_path, "spice")})
            elif route == "/api/erc/explain":
                report_value = str(body.get("report", "")).strip()
                report = Path(report_value) if report_value else None
                if report is None or not report.exists() or not report.is_file():
                    validation = validate_schematic(self.state.schematic_path)
                    report = Path(validation["erc"]["report"])
                self._json(200, {"ok": True, "explanation": explain_erc_report(report)})
            elif route == "/api/library/symbols":
                self._json(200, {"ok": True, "symbols": search_symbols(str(body.get("query", "")))})
            elif route == "/api/library/footprints":
                self._json(200, {"ok": True, "footprints": search_footprints(str(body.get("query", "")))})
            elif route == "/api/snapshots/restore":
                snapshot = Path(str(body["snapshot"]))
                self._json(200, {"ok": True, "restored": restore_snapshot(snapshot)})
            else:
                self._json(404, {"ok": False, "error": "not_found"})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})


def serve(project: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    ensure_runtime_dirs()
    AgentHandler.state = AgentState(project)
    server = ThreadingHTTPServer((host, port), AgentHandler)
    print(json.dumps({"ok": True, "url": f"http://{host}:{port}", "project": str(project)}, ensure_ascii=False))
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(args.project, args.host, args.port)


if __name__ == "__main__":
    main()
