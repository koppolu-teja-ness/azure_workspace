"""
Migration Spec — the shared contract between the source pipeline (discovery,
parsing, mapping, planning — owned by charan) and the target pipeline
(CFN generation, validation, deployment — owned by saurav).

Treat the shape of MigrationSpec as FROZEN once Phase 0 is signed off by both
of you. Any change here should be its own small PR reviewed by both people,
not bundled into a feature-branch PR — see docs/migration_spec_schema.md.

This file also defines GraphState, the TypedDict LangGraph actually threads
through the graph at runtime. GraphState wraps the same pydantic models
below; each node returns a partial dict update and LangGraph merges
list-typed fields via `operator.add` (append), replacing scalar fields.
"""
from __future__ import annotations

import operator
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ResourceType(str, Enum):
    KEY_VAULT = "Microsoft.KeyVault/vaults"
    KEY_VAULT_SECRET = "Microsoft.KeyVault/vaults/secrets"
    KEY_VAULT_KEY = "Microsoft.KeyVault/vaults/keys"
    KEY_VAULT_CERTIFICATE = "Microsoft.KeyVault/vaults/certificates"
    FUNCTION_APP = "Microsoft.Web/sites"
    VNET = "Microsoft.Network/virtualNetworks"
    SUBNET = "Microsoft.Network/virtualNetworks/subnets"
    NSG = "Microsoft.Network/networkSecurityGroups"
    ROUTE_TABLE = "Microsoft.Network/routeTables"
    VNET_PEERING = "Microsoft.Network/virtualNetworks/virtualNetworkPeerings"
    PRIVATE_ENDPOINT = "Microsoft.Network/privateEndpoints"


class MigrationStatus(str, Enum):
    DISCOVERED = "discovered"
    PARSED = "parsed"
    MAPPED = "mapped"
    GENERATED = "generated"
    STATIC_VALIDATED = "static_validated"
    PLANNED = "planned"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    VERIFIED = "verified"
    FAILED = "failed"


class RiskLevel(str, Enum):
    AUTO_MIGRATABLE = "auto_migratable"
    NEEDS_REVIEW = "needs_review"
    HIGH_RISK = "high_risk"


class ApprovalDecisionValue(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ValidationStage(str, Enum):
    STATIC = "static"
    POST_DEPLOY = "post_deploy"


class ValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


# ---------------------------------------------------------------------------
# Core contract models
# ---------------------------------------------------------------------------


class SourceResource(BaseModel):
    """One Azure resource, as discovered/parsed from Bicep or the live Azure
    SDK. Owned by: charan (discovery_agent, parser_analyzer_agent)."""

    resource_id: str
    resource_type: ResourceType
    name: str
    bicep_symbolic_name: str | None = None
    api_version: str
    location: str
    properties: dict[str, Any] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class TargetResource(BaseModel):
    """One proposed AWS CloudFormation resource.
    Owned by: saurav (cfn_generator_agent)."""

    logical_id: str
    aws_resource_type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class MappingRecord(BaseModel):
    """Links one SourceResource to its proposed TargetResource, with
    provenance back to the knowledge-base rule that produced it.
    Owned by: charan (mapping_agent)."""

    source_resource_id: str
    target_logical_id: str | None = None
    mapping_rule_id: str | None = None
    confidence: float = 0.0
    notes: list[str] = Field(default_factory=list)
    unmapped_properties: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Owned by: charan (planning_risk_agent)."""

    resource_id: str
    risk_level: RiskLevel
    reasons: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    """Owned by: charan (approval_gate)."""

    decision: ApprovalDecisionValue = ApprovalDecisionValue.PENDING
    reviewer: str | None = None
    timestamp: datetime | None = None
    comments: str | None = None


class ValidationResult(BaseModel):
    """Owned by: saurav (static_validation_agent, post_deploy_validation_agent)."""

    stage: ValidationStage
    resource_id: str
    check_name: str
    status: ValidationStatus
    details: str | None = None


class LLMTraceEvent(BaseModel):
    """Trace record for one LLM invocation in a graph node."""

    node: str
    provider: str
    model_id: str
    prompt_version: str
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    prompt_sha256: str
    response_sha256: str | None = None
    error: str | None = None


class MigrationSpec(BaseModel):
    """The full shared contract. An instance of this is what Person A's
    pipeline produces and Person B's pipeline consumes — this is the object
    to eyeball in code review whenever the two branches integrate."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    source_resources: list[SourceResource] = Field(default_factory=list)
    target_resources: list[TargetResource] = Field(default_factory=list)
    mappings: list[MappingRecord] = Field(default_factory=list)
    risk_assessments: list[RiskAssessment] = Field(default_factory=list)
    approval: ApprovalDecision = Field(default_factory=ApprovalDecision)
    validation_results: list[ValidationResult] = Field(default_factory=list)
    llm_traces: list[LLMTraceEvent] = Field(default_factory=list)

    status: MigrationStatus = MigrationStatus.DISCOVERED
    config: dict[str, Any] = Field(default_factory=dict)

    def to_json_schema(self) -> dict[str, Any]:
        return self.model_json_schema()


# ---------------------------------------------------------------------------
# LangGraph runtime state
# ---------------------------------------------------------------------------


class GraphState(TypedDict, total=False):
    """What actually flows through the LangGraph graph. Each node function
    takes a GraphState and returns a partial dict of updates; LangGraph
    merges list-typed fields with operator.add (append) and replaces scalar
    fields."""

    run_id: str
    created_at: str
    source_resources: Annotated[list[SourceResource], operator.add]
    target_resources: Annotated[list[TargetResource], operator.add]
    mappings: Annotated[list[MappingRecord], operator.add]
    risk_assessments: Annotated[list[RiskAssessment], operator.add]
    approval: ApprovalDecision
    validation_results: Annotated[list[ValidationResult], operator.add]
    llm_traces: Annotated[list[LLMTraceEvent], operator.add]
    status: MigrationStatus
    config: dict[str, Any]


def spec_to_graph_state(spec: MigrationSpec) -> GraphState:
    """Convert a MigrationSpec (e.g. loaded from JSON) into the initial
    GraphState used to invoke the compiled graph."""
    return GraphState(
        run_id=spec.run_id,
        created_at=spec.created_at.isoformat(),
        source_resources=list(spec.source_resources),
        target_resources=list(spec.target_resources),
        mappings=list(spec.mappings),
        risk_assessments=list(spec.risk_assessments),
        approval=spec.approval,
        validation_results=list(spec.validation_results),
        llm_traces=list(spec.llm_traces),
        status=spec.status,
        config=dict(spec.config),
    )


def graph_state_to_spec(state: GraphState) -> MigrationSpec:
    """Convert a finished/in-progress GraphState back into a MigrationSpec,
    e.g. for persistence or handing to the reporting agent."""
    return MigrationSpec(
        run_id=state["run_id"],
        created_at=datetime.fromisoformat(state["created_at"]),
        source_resources=state.get("source_resources", []),
        target_resources=state.get("target_resources", []),
        mappings=state.get("mappings", []),
        risk_assessments=state.get("risk_assessments", []),
        approval=state.get("approval", ApprovalDecision()),
        validation_results=state.get("validation_results", []),
        llm_traces=state.get("llm_traces", []),
        status=state.get("status", MigrationStatus.DISCOVERED),
        config=state.get("config", {}),
    )
