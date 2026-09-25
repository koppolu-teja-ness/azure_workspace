"""Phase 0 migration specification contract models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
	"""Fixed risk levels agreed for Phase 0."""

	AUTO_MIGRATABLE = "auto_migratable"
	NEEDS_REVIEW = "needs_review"
	HIGH_RISK = "high_risk"


class ResourceRelationship(str, Enum):
	"""Allowed dependency edge relationship types."""

	DEPENDS_ON = "depends_on"
	NETWORK_ATTACHED_TO = "network_attached_to"
	SECRET_REFERENCE = "secret_reference"
	IDENTITY_BINDING = "identity_binding"


AzureResourceType = Literal[
	"Microsoft.KeyVault/vaults",
	"Microsoft.Web/sites",
	"Microsoft.Network/virtualNetworks",
	"Microsoft.Network/networkSecurityGroups",
]


class SpecMetadata(BaseModel):
	"""Metadata describing where the source inventory came from."""

	model_config = ConfigDict(extra="forbid")

	tenant_id: str
	subscription_id: str
	resource_group: str
	region: str
	discovery_run_id: str


class ResourceNode(BaseModel):
	"""Cloud-neutral node extracted from Azure resources."""

	model_config = ConfigDict(extra="forbid")

	resource_id: str
	resource_type: AzureResourceType
	name: str
	location: str
	api_version: str | None = None
	properties: dict[str, Any] = Field(default_factory=dict)
	tags: dict[str, str] = Field(default_factory=dict)
	identity_refs: list[str] = Field(default_factory=list)
	depends_on: list[str] = Field(default_factory=list)


class DependencyEdge(BaseModel):
	"""Explicit graph edge between two source resources."""

	model_config = ConfigDict(extra="forbid")

	from_resource_id: str
	to_resource_id: str
	relation: ResourceRelationship


class MappingDecision(BaseModel):
	"""Decision details produced by the mapping agent."""

	model_config = ConfigDict(extra="forbid")

	source_resource_id: str
	target_resource_type: str
	confidence: float = Field(ge=0.0, le=1.0)
	risk: RiskLevel
	applied_rule_ids: list[str] = Field(default_factory=list)
	rationale: str
	unresolved_items: list[str] = Field(default_factory=list)


class TargetResourceDraft(BaseModel):
	"""Target-side IaC draft object, not yet final template text."""

	model_config = ConfigDict(extra="forbid")

	logical_id: str
	type: str
	properties: dict[str, Any] = Field(default_factory=dict)
	depends_on: list[str] = Field(default_factory=list)
	condition: str | None = None


class ValidationHint(BaseModel):
	"""Validation profile and policy hints for target pipeline."""

	model_config = ConfigDict(extra="forbid")

	lint_profile: str = "default"
	checkov_policies_required: list[str] = Field(default_factory=list)
	checkov_policies_suppressed: list[str] = Field(default_factory=list)


class MigrationSpec(BaseModel):
	"""Shared contract produced by source pipeline and consumed by target pipeline."""

	model_config = ConfigDict(extra="forbid")

	spec_version: str = "1.0.0"
	generated_at: datetime
	source: SpecMetadata
	resources: list[ResourceNode] = Field(default_factory=list)
	dependencies: list[DependencyEdge] = Field(default_factory=list)
	mapping_decisions: list[MappingDecision] = Field(default_factory=list)
	target_drafts: list[TargetResourceDraft] = Field(default_factory=list)
	validation_hints: ValidationHint = Field(default_factory=ValidationHint)
	assumptions: list[str] = Field(default_factory=list)
	warnings: list[str] = Field(default_factory=list)
