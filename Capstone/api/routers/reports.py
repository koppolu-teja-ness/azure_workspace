from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from api.dependencies import get_run
from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.reporting.execution_report import build_execution_report
from migration_assistant.reporting.migration_plan_report import (
	build_migration_plan_report,
	build_risk_report,
)
from migration_assistant.reporting.validation_report import build_validation_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/runs/{run_id}")
def get_run_reports(run_id: str) -> dict[str, object]:
	state = _load_run_or_404(run_id)
	reports = {
		"migration_plan_report": _get_or_build_report(
			state,
			key="migration_plan_report",
			builder=build_migration_plan_report,
		),
		"risk_report": _get_or_build_report(
			state,
			key="risk_report",
			builder=build_risk_report,
		),
		"execution_report": _get_or_build_report(
			state,
			key="execution_report",
			builder=build_execution_report,
		),
		"validation_report": _get_or_build_report(
			state,
			key="validation_report",
			builder=build_validation_report,
		),
	}

	return {
		"run_id": state["run_id"],
		"status": state.get("status", MigrationStatus.DISCOVERED).value,
		"report_summary": _config_dict(state).get("report_summary"),
		"reports": reports,
	}


@router.get("/runs/{run_id}/migration-plan")
def get_migration_plan_report(run_id: str) -> dict[str, object]:
	state = _load_run_or_404(run_id)
	return _get_or_build_report(
		state,
		key="migration_plan_report",
		builder=build_migration_plan_report,
	)


@router.get("/runs/{run_id}/risk")
def get_risk_report(run_id: str) -> dict[str, object]:
	state = _load_run_or_404(run_id)
	return _get_or_build_report(
		state,
		key="risk_report",
		builder=build_risk_report,
	)


@router.get("/runs/{run_id}/execution")
def get_execution_report(run_id: str) -> dict[str, object]:
	state = _load_run_or_404(run_id)
	return _get_or_build_report(
		state,
		key="execution_report",
		builder=build_execution_report,
	)


@router.get("/runs/{run_id}/validation")
def get_validation_report(run_id: str) -> dict[str, object]:
	state = _load_run_or_404(run_id)
	return _get_or_build_report(
		state,
		key="validation_report",
		builder=build_validation_report,
	)


def _load_run_or_404(run_id: str) -> GraphState:
	try:
		return get_run(run_id)
	except KeyError as exc:
		raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc


def _config_dict(state: GraphState) -> dict[str, Any]:
	config = state.get("config", {})
	if isinstance(config, dict):
		return config
	return {}


def _get_or_build_report(
	state: GraphState,
	*,
	key: str,
	builder: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
	config = _config_dict(state)
	stored = config.get(key)
	if isinstance(stored, dict):
		return stored
	return builder(state)
