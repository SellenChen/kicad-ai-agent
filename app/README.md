# KiCad AI Agent MVP

This is the Phase 1 MVP for a Windows KiCad AI Agent.

## What Works

- Local HTTP Agent service.
- Lightweight side panel web UI.
- KiCad project and schematic summary.
- Natural-language plan for component value edits.
- Format-preserving `.kicad_sch` property patch.
- Snapshot before write.
- ERC and netlist validation through `kicad-cli`.
- KiCad PCB Editor launcher plugin.
- OpenAI-compatible provider skeleton with mock fallback.

## Run

```powershell
python .\run_agent.py --project .\samples\amplifier-ac-stage1\amplifier-ac.kicad_pro --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

## Self Test

```powershell
python .\scripts\self_test.py
```

The self test starts the service, reads a KiCad project, plans `R4 -> 2K`, previews a small diff, applies the patch, runs ERC and exports a netlist.

## KiCad Plugin

Installed target:

```text
C:\Users\Sellen\AppData\Roaming\kicad\10.0\scripting\plugins\kicad_ai_agent_launcher
```

Open KiCad PCB Editor and refresh/restart plugins. The plugin is named:

```text
KiCad AI Agent
```

It starts the local Agent service and opens the side panel page.

## Model Configuration

Without credentials, the service uses `MockProvider`.

To call an OpenAI-compatible endpoint:

```text
KICAD_AGENT_MODEL_BASE_URL=https://api.deepseek.com
KICAD_AGENT_API_KEY=<your-api-key>
KICAD_AGENT_MODEL=<model-name>
```

## Runtime Outputs

```text
work\stage1_runtime\snapshots
work\stage1_runtime\reports
```

## Main Files

```text
app\run_agent.py
app\kicad_ai_agent\server.py
app\kicad_ai_agent\schematic.py
app\kicad_ai_agent\kicad_cli.py
app\kicad_ai_agent\provider.py
app\static\index.html
app\static\styles.css
app\static\app.js
app\kicad_plugin\kicad_ai_agent_launcher
```
