"""Shared AWS Bedrock runtime helpers.

Centralizes config parsing and invoke_model response handling so multiple
agents can use one provider contract.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import boto3

from migration_assistant.config.app_config import AppConfig
from migration_assistant.graph.state import LLMTraceEvent


@dataclass(frozen=True, slots=True)
class BedrockSettings:
    model_id: str
    region_name: str | None = None
    temperature: float = 0.7
    max_tokens: int = 800


@dataclass(frozen=True, slots=True)
class LLMProviderConfig:
    enabled: bool
    provider: str
    settings: BedrockSettings | None


def parse_llm_provider_config(app_config: AppConfig) -> LLMProviderConfig:
    llm_config = app_config.llm
    enabled = bool(llm_config.enabled)
    provider = str(llm_config.provider)

    if not enabled or provider != "aws_bedrock":
        return LLMProviderConfig(enabled=enabled, provider=provider, settings=None)

    model_id = str(llm_config.bedrock.model_id).strip()
    if not model_id:
        return LLMProviderConfig(enabled=enabled, provider=provider, settings=None)

    raw_temperature = float(llm_config.bedrock.temperature)
    # Reasoning-enabled agents should not run at temperature 0.0 (greedy mode).
    effective_temperature = raw_temperature if raw_temperature > 0.0 else 0.7

    settings = BedrockSettings(
        model_id=model_id,
        region_name=llm_config.bedrock.region_name,
        temperature=effective_temperature,
        max_tokens=int(llm_config.bedrock.max_tokens),
    )
    return LLMProviderConfig(enabled=enabled, provider=provider, settings=settings)


def require_bedrock_settings(*, app_config: AppConfig, agent_name: str) -> BedrockSettings:
    provider = parse_llm_provider_config(app_config)
    if not provider.enabled:
        raise ValueError(f"{agent_name}: llm.enabled must be true")
    if provider.provider != "aws_bedrock":
        raise ValueError(
            f"{agent_name}: llm.provider must be 'aws_bedrock', got '{provider.provider}'"
        )
    if provider.settings is None:
        raise ValueError(
            f"{agent_name}: incomplete Bedrock config; set llm.bedrock.model_id"
        )
    return provider.settings


def build_runtime_client(region_name: str | None = None) -> Any:
    return boto3.client("bedrock-runtime", region_name=region_name)


def invoke_bedrock_text(
    *,
    settings: BedrockSettings,
    prompt: str,
    runtime_client: Any | None = None,
) -> str:
    client = runtime_client or build_runtime_client(region_name=settings.region_name)
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    response = client.invoke_model(
        modelId=settings.model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    body = response.get("body")
    text_payload = body.read().decode("utf-8") if body else "{}"
    data = json.loads(text_payload)
    return extract_text_from_bedrock_response(data)


def extract_text_from_bedrock_response(response_json: dict[str, Any]) -> str:
    content = response_json.get("content", [])
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "\n".join(part for part in parts if part)


def parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = stripped[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def build_trace_event(
    *,
    node: str,
    prompt_version: str,
    settings: BedrockSettings,
    status: str,
    prompt_text: str,
    response_text: str | None = None,
    error: str | None = None,
) -> LLMTraceEvent:
    return LLMTraceEvent(
        node=node,
        provider="aws_bedrock",
        model_id=settings.model_id,
        prompt_version=prompt_version,
        status=status,
        timestamp=datetime.now(UTC),
        prompt_sha256=_sha256_hex(prompt_text),
        response_sha256=_sha256_hex(response_text) if response_text is not None else None,
        error=error,
    )


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
