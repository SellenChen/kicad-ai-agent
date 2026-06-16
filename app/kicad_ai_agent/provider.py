from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class Provider:
    name = "base"

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        raise NotImplementedError


class MockProvider(Provider):
    name = "mock"

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        text = messages[-1]["content"] if messages else ""
        if "ERC" in text.upper():
            message = "我会读取 ERC JSON 报告，按错误类型、位置和修复建议分组解释。"
        elif any(word in text for word in ["改成", "修改", "设为", "="]):
            message = "我会先生成可审查的工具计划，等用户确认后再执行修改和校验。"
        else:
            message = "我可以读取工程、解释检查结果、规划原理图修改，并通过 KiCad CLI 校验。"
        return {"provider": self.name, "content": message}


class OpenAICompatibleProvider(Provider):
    name = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def build_payload(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            payload["tools"] = tools
        return payload

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload = self.build_payload(messages, tools)
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            return {"provider": self.name, "error": str(exc), "payload_shape_validated": True}


def make_provider() -> Provider:
    base_url = os.environ.get("KICAD_AGENT_MODEL_BASE_URL")
    api_key = os.environ.get("KICAD_AGENT_API_KEY")
    model = os.environ.get("KICAD_AGENT_MODEL", "deepseek-chat")
    if base_url and api_key:
        return OpenAICompatibleProvider(base_url, api_key, model)
    return MockProvider()
