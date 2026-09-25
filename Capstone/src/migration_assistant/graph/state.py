"""Shared LangGraph state contract for the Phase 0 workflow."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from migration_assistant.mapping.equivalence_models import EquivalenceRule
from migration_assistant.planning.plan_models import MigrationSpec, ResourceNode

WorkflowStatus = Literal["pending", "running", "failed", "completed"]


class WorkflowState(TypedDict, total=False):
	"""Typed state dictionary that flows through workflow nodes."""

	run_id: str
	spec_version: str
	input_manifest_path: str
	discovered_resources: list[ResourceNode] | list[dict[str, Any]]
	parsed_graph: dict[str, Any]
	retrieved_rules: list[EquivalenceRule] | list[dict[str, Any]]
	migration_spec: MigrationSpec | dict[str, Any]
	cfn_template: dict[str, Any]
	static_validation_results: dict[str, Any]
	report_summary: dict[str, Any]
	deployment_plan: dict[str, Any]
	checkpoints: dict[str, str]
	warnings: list[str]
	errors: list[str]
	status: WorkflowStatus


def new_workflow_state(
	run_id: str,
	spec_version: str = "1.0.0",
	input_manifest_path: str = "",
) -> WorkflowState:
	"""Build initial workflow state with standard default fields."""

	return {
		"run_id": run_id,
		"spec_version": spec_version,
		"input_manifest_path": input_manifest_path,
		"discovered_resources": [],
		"parsed_graph": {},
		"retrieved_rules": [],
		"migration_spec": {},
		"cfn_template": {},
		"static_validation_results": {},
		"report_summary": {},
		"deployment_plan": {},
		"checkpoints": {},
		"warnings": [],
		"errors": [],
		"status": "pending",
	}


def merge_patch(state: WorkflowState, patch: WorkflowState) -> WorkflowState:
	"""Return a shallow-merged new state object."""

	merged = dict(state)
	merged.update(patch)
	return merged
