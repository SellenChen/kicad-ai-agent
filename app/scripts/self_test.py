from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_SRC = ROOT / "work" / "stage0_cli" / "amplifier-ac"
SAMPLE_DST = ROOT / "app" / "samples" / "amplifier-ac-stage1"


def request_json(url: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def main() -> None:
    if SAMPLE_DST.exists():
        shutil.rmtree(SAMPLE_DST)
    shutil.copytree(SAMPLE_SRC, SAMPLE_DST)
    project = SAMPLE_DST / "amplifier-ac.kicad_pro"
    port = 8877
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "kicad_ai_agent.server",
            "--project",
            str(project),
            "--port",
            str(port),
        ],
        cwd=str(ROOT / "app"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        base = f"http://127.0.0.1:{port}"
        last_error: Exception | None = None
        for _ in range(40):
            try:
                health = request_json(f"{base}/api/health")
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.25)
        else:
            raise SystemExit(f"Server did not start: {last_error}")

        summary = request_json(f"{base}/api/project/summary")
        chat = request_json(f"{base}/api/chat", {"message": "把 R4 改成 2K"})
        preview = request_json(f"{base}/api/tools/set-value/preview", {"reference": "R4", "value": "2K"})
        apply = request_json(f"{base}/api/tools/set-value/apply", {"reference": "R4", "value": "2K"})
        erc_explain = request_json(f"{base}/api/erc/explain", {})
        symbols = request_json(f"{base}/api/library/symbols", {"query": "Device"})
        footprints = request_json(f"{base}/api/library/footprints", {"query": "SOT"})
        diagnostics = request_json(f"{base}/api/diagnostics")
        after = request_json(f"{base}/api/project/summary")
        result = {
            "health": health,
            "summary_counts": {
                "placed_symbols": summary["summary"]["placed_symbols"],
                "wires": summary["summary"]["wires"],
                "labels": summary["summary"]["labels"],
            },
            "chat_plan": chat["plan"],
            "preview": preview["result"]["diff"],
            "apply": {
                "diff": apply["result"]["diff"],
                "erc": apply["validation"]["erc"].get("summary"),
                "netlist_ok": apply["validation"]["netlist"].get("ok"),
            },
            "erc_explain_groups": len(erc_explain["explanation"]["groups"]),
            "symbol_search_results": len(symbols["symbols"]["results"]),
            "footprint_search_results": len(footprints["footprints"]["results"]),
            "diagnostics_cli_exists": diagnostics["diagnostics"]["kicad_cli"]["exists"],
            "r4_after": next(item for item in after["summary"]["components"] if item["ref"] == "R4"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()
