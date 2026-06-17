from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import DATA_ROOT, ensure_runtime_dirs


SETTINGS_PATH = DATA_ROOT / "settings.json"

DEEPSEEK_MODELS = [
    {
        "id": "deepseek-v4-pro",
        "label": "DeepSeek V4 Pro",
        "base_url": "https://api.deepseek.com",
    },
    {
        "id": "deepseek-v4-flash",
        "label": "DeepSeek V4 Flash",
        "base_url": "https://api.deepseek.com",
    },
]

DEFAULT_SETTINGS: dict[str, Any] = {
    "provider": "deepseek",
    "model": "deepseek-v4-pro",
    "base_url": "https://api.deepseek.com",
    "api_key": "",
    "upload_schematic_features": True,
    "max_feature_components": 120,
}


def public_settings(settings: dict[str, Any]) -> dict[str, Any]:
    result = dict(settings)
    result["api_key_set"] = bool(result.get("api_key"))
    result["api_key"] = ""
    return result


def load_settings() -> dict[str, Any]:
    ensure_runtime_dirs()
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        loaded = {}
    merged = dict(DEFAULT_SETTINGS)
    merged.update({key: value for key, value in loaded.items() if key in DEFAULT_SETTINGS})
    return merged


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    ensure_runtime_dirs()
    current = load_settings() if SETTINGS_PATH.exists() else dict(DEFAULT_SETTINGS)
    for key in DEFAULT_SETTINGS:
        if key in settings:
            current[key] = settings[key]
    if not current.get("base_url"):
        current["base_url"] = "https://api.deepseek.com"
    SETTINGS_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return current
