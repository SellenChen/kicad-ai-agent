from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "app" / "samples" / "amplifier-ac-stage1" / "amplifier-ac.kicad_pro"

os.environ["KICAD_AI_AGENT_SKIP_REGISTER"] = "1"
os.environ["KICAD_AI_AGENT_PROJECT"] = str(PROJECT)
os.environ["KICAD_AI_AGENT_PORT"] = "8878"
os.environ["KICAD_AI_AGENT_NO_BROWSER"] = "1"

sys.path.insert(0, str(ROOT / "app" / "kicad_plugin"))

from kicad_ai_agent_launcher.launcher import KiCadAIAgentLauncher  # noqa: E402


plugin = KiCadAIAgentLauncher()
plugin.defaults()
process = plugin.Run()
try:
    last_error: Exception | None = None
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8878/api/health", timeout=1) as response:
                health = json.loads(response.read().decode("utf-8"))
                print(json.dumps({"plugin": plugin.name, "health": health}, ensure_ascii=False, indent=2))
                break
        except Exception as exc:
            last_error = exc
            time.sleep(0.25)
    else:
        raise SystemExit(f"Agent service did not become healthy: {last_error}")
finally:
    if process:
        process.terminate()
        process.wait(timeout=10)
