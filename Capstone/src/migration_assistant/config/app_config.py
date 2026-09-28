"""Typed application configuration carried in GraphState.config."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BedrockConfig(BaseModel):
    model_id: str = ""
    region_name: str | None = None
    temperature: float = 0.7
    max_tokens: int = 800


class LLMConfig(BaseModel):
    enabled: bool = False
    provider: str = ""
    bedrock: BedrockConfig = Field(default_factory=BedrockConfig)


class RiskThresholdsConfig(BaseModel):
    min_auto_migratable_confidence: float = 0.85


class ParserConfig(BaseModel):
    prefer_azure_cli_compile: bool = True
    allow_fallback_parser: bool = True


class AzureDiscoveryConfig(BaseModel):
    enable_sdk_discovery: bool = False
    subscription_id: str | None = None
    resource_group: str | None = None


class MappingPolicyConfig(BaseModel):
    llm_override_threshold: float = 0.9


class DeploymentConfig(BaseModel):
    rollback_cleanup_mode: str = "delete_artifacts"


class CheckpointConfig(BaseModel):
    backend: str = "postgres"
    enabled: bool = True


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    bicep_paths: list[str] = Field(default_factory=list)
    bicep_directories: list[str] = Field(default_factory=list)
    discovered_bicep_files: list[str] = Field(default_factory=list)
    risk_thresholds: RiskThresholdsConfig = Field(default_factory=RiskThresholdsConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    azure_discovery: AzureDiscoveryConfig = Field(default_factory=AzureDiscoveryConfig)
    mapping_policy: MappingPolicyConfig = Field(default_factory=MappingPolicyConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    checkpoints: CheckpointConfig = Field(default_factory=CheckpointConfig)
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
