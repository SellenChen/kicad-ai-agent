from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .settings import load_settings


class Provider:
    name = "base"

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        raise NotImplementedError


class MockProvider(Provider):
    name = "mock"

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        text = messages[-1]["content"] if messages else ""
        if "ERC" in text.upper():
            message = "我可以读取 ERC JSON 报告，并按错误类型、位置和修复建议分组解释。"
        elif any(word in text for word in ["改成", "修改", "设为", "设置为", "="]):
            message = "我会生成可审查的工具计划，等你确认后再执行修改和校验。"
        elif any(word in text for word in ["生成", "搭建", "创建", "电路"]):
            message = "我会生成简单电路的可执行原理图计划，等你确认后完成元件摆放、连线和校验。"
        else:
            message = "我可以读取工程特征、解释检查结果、规划原理图修改，并通过 KiCad CLI 校验。"
        return {"provider": self.name, "content": message, "offline": True}


class OpenAICompatibleProvider(Provider):
    name = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str, *, provider_name: str = "openai-compatible"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = provider_name

    def build_payload(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            payload["tools"] = tools
        return payload

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload = self.build_payload(messages, tools)
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = json.loads(response.read().decode("utf-8"))
            content = _extract_content(raw)
            return {"provider": self.name, "model": self.model, "content": content, "raw": raw}
        except urllib.error.URLError as exc:
            return {"provider": self.name, "model": self.model, "error": str(exc), "content": "模型请求失败，请检查 API Key、网络和模型名称。"}


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__(base_url, api_key, model, provider_name="deepseek")


def _extract_content(raw: dict[str, Any]) -> str:
    try:
        return raw["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(raw, ensure_ascii=False, indent=2)


def make_provider(settings: dict[str, Any] | None = None) -> Provider:
    config = settings or load_settings()
    provider = str(config.get("provider", "deepseek")).lower()
    api_key = str(config.get("api_key", "")).strip()
    if not api_key:
        return MockProvider()
    if provider == "deepseek":
        return DeepSeekProvider(
            str(config.get("base_url", "https://api.deepseek.com")),
            api_key,
            str(config.get("model", "deepseek-v4-pro")),
        )
    return OpenAICompatibleProvider(
        str(config.get("base_url", "https://api.deepseek.com")),
        api_key,
        str(config.get("model", "deepseek-v4-pro")),
        provider_name=provider,
    )
