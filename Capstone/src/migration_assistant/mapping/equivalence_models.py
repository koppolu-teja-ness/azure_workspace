"""Phase 0 RAG knowledge base schema models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PropertyMapping(BaseModel):
	"""Maps one source property path to one target property path."""

	model_config = ConfigDict(extra="forbid")

	source_path: str
	target_path: str
	transform: str = "identity"
	required: bool = True
	notes: str | None = None


class EquivalenceRule(BaseModel):
	"""Top-level mapping rule used by the mapping agent retrieval pipeline."""

	model_config = ConfigDict(extra="forbid")

	rule_id: str
	azure_resource_type: str
	aws_resource_type: str
	preconditions: list[str] = Field(default_factory=list)
	property_mappings: list[PropertyMapping] = Field(default_factory=list)
	incompatibilities: list[str] = Field(default_factory=list)
	fallback_strategy: str = "manual_review"
	confidence_baseline: float = Field(ge=0.0, le=1.0)
	references: list[str] = Field(default_factory=list)
	tags: list[str] = Field(default_factory=list)


class ResourceTypeMappingsDocument(BaseModel):
	"""Versioned collection model for resource type mapping rules JSON."""

	model_config = ConfigDict(extra="forbid")

	schema_version: str = "1.0.0"
	rules: list[EquivalenceRule] = Field(default_factory=list)


class RbacToIamRule(BaseModel):
	"""RBAC-to-IAM translation entry."""

	model_config = ConfigDict(extra="forbid")

	rule_id: str
	azure_role: str
	aws_actions: list[str] = Field(default_factory=list)
	aws_resource_scope_template: str
	conditions: list[str] = Field(default_factory=list)
	notes: str | None = None


class RbacToIamDocument(BaseModel):
	"""Versioned collection model for RBAC translation rules."""

	model_config = ConfigDict(extra="forbid")

	schema_version: str = "1.0.0"
	rules: list[RbacToIamRule] = Field(default_factory=list)


class TriggerMappingRule(BaseModel):
	"""Function trigger mapping rule."""

	model_config = ConfigDict(extra="forbid")

	rule_id: str
	azure_trigger_type: str
	aws_integration_type: str
	required_services: list[str] = Field(default_factory=list)
	caveats: list[str] = Field(default_factory=list)
	confidence_baseline: float = Field(ge=0.0, le=1.0)


class TriggerMappingsDocument(BaseModel):
	"""Versioned collection model for function trigger mapping rules."""

	model_config = ConfigDict(extra="forbid")

	schema_version: str = "1.0.0"
	rules: list[TriggerMappingRule] = Field(default_factory=list)


class KnowledgeBaseIssue(BaseModel):
	"""JSONL issue log row for rule quality and incompatibility tracking."""

	model_config = ConfigDict(extra="forbid")

	timestamp: datetime
	rule_id: str
	source_resource_id: str
	issue_type: Literal["mapping_gap", "incompatibility", "validation_failure", "manual_override"]
	severity: Literal["low", "medium", "high", "critical"]
	message: str
	suggested_action: str
