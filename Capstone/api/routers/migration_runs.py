from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import dump_jsonable_state, get_run, save_run
from migration_assistant.agents import (
	cfn_generator_agent,
	deployment_agent,
	post_deploy_validation_agent,
	reporting_agent,
	static_validation_agent,
)
from migration_assistant.graph.state import (
	GraphState,
	MigrationSpec,
	MigrationStatus,
	graph_state_to_spec,
	spec_to_graph_state,
)
from migration_assistant.graph.workflow import build_graph

router = APIRouter(prefix="/runs", tags=["migration-runs"])


class ExecuteRunRequest(BaseModel):
	run_id: str = Field(min_length=1, max_length=128)
	bicep_paths: list[str] = Field(default_factory=list)
	bicep_directories: list[str] = Field(default_factory=list)
	config: dict[str, Any] = Field(default_factory=dict)


class ExecuteTargetFromSpecRequest(BaseModel):
	migration_spec: dict[str, Any]


LIST_MERGE_KEYS = {
	"source_resources",
	"target_resources",
	"mappings",
	"risk_assessments",
	"validation_results",
	"llm_traces",
}


@router.post("/execute")
def execute_run(payload: ExecuteRunRequest) -> dict[str, object]:
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
		raise HTTPException(status_code=500, detail=f"Run execution failed: {exc}") from exc

	save_run(final_state)
	return dump_jsonable_state(final_state)


@router.get("/{run_id}")
def get_run_detail(run_id: str) -> dict[str, object]:
	try:
		state = get_run(run_id)
	except KeyError as exc:
		raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc
	return dump_jsonable_state(state)


@router.post("/execute-target")
def execute_target_from_spec(payload: ExecuteTargetFromSpecRequest) -> dict[str, object]:
	try:
		spec = MigrationSpec.model_validate(payload.migration_spec)
	except Exception as exc:
		raise HTTPException(status_code=400, detail=f"Invalid migration_spec payload: {exc}") from exc

	state = spec_to_graph_state(spec)
	_execute_target_stages_or_raise(state)

	save_run(state)
	return dump_jsonable_state(state)


@router.post("/{run_id}/execute-target")
def execute_target_for_run(run_id: str) -> dict[str, object]:
	try:
		state = get_run(run_id)
	except KeyError as exc:
		raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc

	if not state.get("source_resources"):
		raise HTTPException(
			status_code=400,
			detail="Run has no source resources; execute discovery/parsing before target stages.",
		)

	# Normalize persisted state through contract validation before target execution.
	spec = graph_state_to_spec(state)
	state = spec_to_graph_state(spec)

	_execute_target_stages_or_raise(state)

	save_run(state)
	return dump_jsonable_state(state)


def _apply_graph_update(state: GraphState, update: dict[str, Any]) -> None:
	for key, value in update.items():
		if key in LIST_MERGE_KEYS and isinstance(value, list):
			existing = state.get(key, [])
			if isinstance(existing, list):
				state[key] = [*existing, *value]
			else:
				state[key] = list(value)
			continue

		state[key] = value


def _execute_target_stages_or_raise(state: GraphState) -> None:
	target_stage_agents = [
		cfn_generator_agent.run,
		static_validation_agent.run,
		deployment_agent.run,
		post_deploy_validation_agent.run,
		reporting_agent.run,
	]

	try:
		for stage_runner in target_stage_agents:
			update = stage_runner(state)
			_apply_graph_update(state, update)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=f"Target pipeline config error: {exc}") from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Target pipeline execution failed: {exc}") from exc
