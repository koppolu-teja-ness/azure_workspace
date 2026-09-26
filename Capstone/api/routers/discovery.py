from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import dump_jsonable_state, get_run, list_runs, save_run
from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.graph.workflow import build_graph

router = APIRouter(prefix="/discovery", tags=["discovery"])


class DiscoveryRunRequest(BaseModel):
	run_id: str = Field(min_length=1, max_length=128)
	bicep_paths: list[str] = Field(default_factory=list)
	bicep_directories: list[str] = Field(default_factory=list)
	config: dict[str, Any] = Field(default_factory=dict)


@router.post("/runs")
def execute_discovery(payload: DiscoveryRunRequest) -> dict[str, object]:
	app = build_graph()
	state_config = dict(payload.config)
	state_config["bicep_paths"] = list(payload.bicep_paths)
	state_config["bicep_directories"] = list(payload.bicep_directories)

	initial_state: GraphState = {
		"run_id": payload.run_id,
		"created_at": datetime.now(UTC).isoformat(),
		"source_resources": [],
		"target_resources": [],
		"mappings": [],
		"risk_assessments": [],
		"validation_results": [],
		"llm_traces": [],
		"status": MigrationStatus.DISCOVERED,
		"config": state_config,
	}

	try:
		final_state = app.invoke(initial_state)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Discovery execution failed: {exc}") from exc

	save_run(final_state)
	return dump_jsonable_state(final_state)


@router.get("/runs")
def get_discovery_runs() -> dict[str, object]:
	runs = []
	for state in list_runs():
		config = state.get("config", {}) if isinstance(state.get("config", {}), dict) else {}
		runs.append(
			{
				"run_id": state["run_id"],
				"status": state.get("status", MigrationStatus.DISCOVERED).value,
				"counts": {
					"discovered_files": len(config.get("discovered_bicep_files", [])),
					"source_resources": len(state.get("source_resources", [])),
					"mappings": len(state.get("mappings", [])),
				},
			}
		)

	return {"runs": sorted(runs, key=lambda item: str(item["run_id"]))}


@router.get("/runs/{run_id}")
def get_discovery_run_detail(run_id: str) -> dict[str, object]:
	try:
		state = get_run(run_id)
	except KeyError as exc:
		raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc

	return dump_jsonable_state(state)
