import os

from .launcher import KiCadAIAgentLauncher


if os.environ.get("KICAD_AI_AGENT_SKIP_REGISTER") != "1":
    KiCadAIAgentLauncher().register()
