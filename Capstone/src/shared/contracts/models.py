from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal["auto-migratable", "needs-review", "high-risk"]


class ResourceNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    service_area: Literal["KeyVault", "Functions", "VNet"]
    source_type: str
    target_type: str
    name: str
    decision: Decision
    properties: dict[str, Any]
    notes: str | None = None


class DependencyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    kind: str


class RiskDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity_exposure: float = Field(alias="identityExposure", ge=0, le=100)
    network_exposure: float = Field(alias="networkExposure", ge=0, le=100)
    unsupported_mapping_risk: float = Field(alias="unsupportedMappingRisk", ge=0, le=100)
    blast_radius: float = Field(alias="blastRadius", ge=0, le=100)


class RiskModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(alias="overallScore", ge=0, le=100)
    classification: Decision
    dimensions: RiskDimensions


class Traceability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_commit: str = Field(alias="sourceCommit", min_length=7)
    generated_at: datetime = Field(alias="generatedAt")
    generated_by: str = Field(alias="generatedBy")


class DiscoveryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_version: str = Field(alias="specVersion")
    source: dict[str, str]
    target: dict[str, str]
    resources: list[ResourceNode]
    dependencies: list[DependencyEdge]
    traceability: Traceability


class AnalysisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discovery: DiscoveryOutput
    unsupported_constructs: list[str]
    validation_hints: list[str] = Field(alias="validationHints")


class MappingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: AnalysisOutput
    risk: RiskModel
    mapping_notes: list[str]


class GenerationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mapping: MappingOutput
    generated_templates: dict[str, str]
    deterministic_id: str
