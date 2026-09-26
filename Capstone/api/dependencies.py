"""Shared in-memory run store for API routers.

This is intentionally lightweight for capstone/demo usage.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from threading import Lock
from typing import Any

try:
	from migration_assistant.graph.state import (
		ApprovalDecision,
		GraphState,
		MappingRecord,
		MigrationStatus,
	)
	from migration_assistant.planning.risk_scoring import assess_risks
except ModuleNotFoundError:
	src_path = Path(__file__).resolve().parents[1] / "src"
	if str(src_path) not in sys.path:
		sys.path.insert(0, str(src_path))
	from migration_assistant.graph.state import (  # type: ignore[no-redef]
		ApprovalDecision,
		GraphState,
		MappingRecord,
		MigrationStatus,
	)
	from migration_assistant.planning.risk_scoring import assess_risks  # type: ignore[no-redef]

_RUNS: dict[str, GraphState] = {}
_LOCK = Lock()


def _seed_state(run_id: str) -> GraphState:
	mappings = [
		MappingRecord(
			source_resource_id="/subscriptions/demo/resourceGroups/rg-demo/providers/"
			"Microsoft.KeyVault/vaults/kv-demo",
			target_logical_id="KvDemo",
			mapping_rule_id="rule-keyvault-secretsmanager",
			confidence=0.94,
			notes=["Direct vault to Secrets Manager mapping available."],
			unmapped_properties=[],
		),
		MappingRecord(
			source_resource_id="/subscriptions/demo/resourceGroups/rg-demo/providers/"
			"Microsoft.Web/sites/fn-demo",
			target_logical_id="FnDemo",
			mapping_rule_id="rule-functions-lambda",
			confidence=0.79,
			notes=["Runtime and trigger mapping is possible."],
			unmapped_properties=["authSettingsV2"],
		),
		MappingRecord(
			source_resource_id="/subscriptions/demo/resourceGroups/rg-demo/providers/"
			"Microsoft.Network/virtualNetworks/vnet-demo",
			target_logical_id=None,
			mapping_rule_id=None,
			confidence=0.41,
			notes=["Complex peering and endpoint constraints detected."],
			unmapped_properties=["virtualNetworkPeerings"],
		),
	]
	risk_assessments = assess_risks(mappings, min_auto_migratable_confidence=0.85)
	config: dict[str, Any] = {
		"approval": {
			"auto_approve": False,
		},
		"migration_plan": {
			"resource_count": 3,
			"mapping_count": 3,
			"risk_summary": {
				"auto_migratable": sum(
					1 for item in risk_assessments if item.risk_level.value == "auto_migratable"
				),
				"needs_review": sum(
					1 for item in risk_assessments if item.risk_level.value == "needs_review"
				),
				"high_risk": sum(1 for item in risk_assessments if item.risk_level.value == "high_risk"),
			},
			"sequence": [
				{
					"sequence": 1,
					"resource_id": mappings[0].source_resource_id,
					"resource_type": "Microsoft.KeyVault/vaults",
					"name": "kv-demo",
				},
				{
					"sequence": 2,
					"resource_id": mappings[1].source_resource_id,
					"resource_type": "Microsoft.Web/sites",
					"name": "fn-demo",
				},
				{
					"sequence": 3,
					"resource_id": mappings[2].source_resource_id,
					"resource_type": "Microsoft.Network/virtualNetworks",
					"name": "vnet-demo",
				},
			],
		},
	}
	return {
		"run_id": run_id,
		"created_at": "2026-09-25T00:00:00+00:00",
		"mappings": mappings,
		"risk_assessments": risk_assessments,
		"approval": ApprovalDecision(),
		"status": MigrationStatus.AWAITING_APPROVAL,
		"config": config,
	}


def get_run(run_id: str) -> GraphState:
	with _LOCK:
		state = _RUNS.get(run_id)
		if state is None:
			raise KeyError(run_id)
		return deepcopy(state)


def save_run(state: GraphState) -> None:
	with _LOCK:
		_RUNS[state["run_id"]] = deepcopy(state)


def list_runs() -> list[GraphState]:
	with _LOCK:
		return [deepcopy(state) for state in _RUNS.values()]


def dump_jsonable_state(state: GraphState) -> dict[str, Any]:
	def _dump_item(item: Any) -> Any:
		if hasattr(item, "model_dump"):
			return item.model_dump(mode="json")
		if isinstance(item, dict):
			return dict(item)
		return item

	return {
		"run_id": state["run_id"],
		"created_at": state["created_at"],
		"source_resources": [_dump_item(item) for item in state.get("source_resources", [])],
		"target_resources": [_dump_item(item) for item in state.get("target_resources", [])],
		"mappings": [item.model_dump(mode="json") for item in state.get("mappings", [])],
		"risk_assessments": [
			item.model_dump(mode="json") for item in state.get("risk_assessments", [])
		],
		"validation_results": [_dump_item(item) for item in state.get("validation_results", [])],
		"llm_traces": [_dump_item(item) for item in state.get("llm_traces", [])],
		"approval": state.get("approval", ApprovalDecision()).model_dump(mode="json"),
		"status": state.get("status", MigrationStatus.DISCOVERED).value,
		"config": state.get("config", {}),
	}
