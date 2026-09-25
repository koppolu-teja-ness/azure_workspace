"""Typed application configuration carried in GraphState.config."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BedrockConfig(BaseModel):
    model_id: str = ""
    region_name: str | None = None
    temperature: float = 0.0
    max_tokens: int = 800


class LLMConfig(BaseModel):
    enabled: bool = False
    provider: str = ""
    bedrock: BedrockConfig = Field(default_factory=BedrockConfig)


class RiskThresholdsConfig(BaseModel):
    min_auto_migratable_confidence: float = 0.85


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    bicep_paths: list[str] = Field(default_factory=list)
    bicep_directories: list[str] = Field(default_factory=list)
    discovered_bicep_files: list[str] = Field(default_factory=list)
    risk_thresholds: RiskThresholdsConfig = Field(default_factory=RiskThresholdsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    report_summary: str | None = None


def parse_app_config(raw: dict[str, Any] | AppConfig | None) -> AppConfig:
    if isinstance(raw, AppConfig):
        return raw
    if isinstance(raw, dict):
        normalized = dict(raw)
        llm_raw = normalized.get("llm")
        if isinstance(llm_raw, dict):
            normalized["llm"] = _normalize_llm_shape(llm_raw)
        return AppConfig.model_validate(normalized)
    return AppConfig()


def app_config_to_state(config: AppConfig) -> dict[str, Any]:
    return config.model_dump(mode="json")


def _normalize_llm_shape(llm_raw: dict[str, Any]) -> dict[str, Any]:
    # Backward compatibility: support the previous flat llm fields while moving
    # to a nested typed bedrock section.
    bedrock_raw = llm_raw.get("bedrock")
    if isinstance(bedrock_raw, dict):
        bedrock = dict(bedrock_raw)
    else:
        bedrock = {}

    if "model_id" in llm_raw and "model_id" not in bedrock:
        bedrock["model_id"] = llm_raw.get("model_id")
    if "region_name" in llm_raw and "region_name" not in bedrock:
        bedrock["region_name"] = llm_raw.get("region_name")
    if "temperature" in llm_raw and "temperature" not in bedrock:
        bedrock["temperature"] = llm_raw.get("temperature")
    if "max_tokens" in llm_raw and "max_tokens" not in bedrock:
        bedrock["max_tokens"] = llm_raw.get("max_tokens")

    normalized = dict(llm_raw)
    normalized["bedrock"] = bedrock
    return normalized
