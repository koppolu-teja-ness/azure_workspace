from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import dump_jsonable_state, get_run, list_runs, save_run
from migration_assistant.agents.approval_gate import route_after_approval
from migration_assistant.graph.state import ApprovalDecision, ApprovalDecisionValue, MigrationStatus

router = APIRouter(prefix="/approval", tags=["approval"])


class ApprovalDecisionRequest(BaseModel):
	decision: ApprovalDecisionValue
	reviewer: str = Field(min_length=1, max_length=100)
	comments: str | None = Field(default=None, max_length=2000)


@router.get("/runs")
def get_runs() -> dict[str, object]:
	results = []
	for state in list_runs():
		risk_items = state.get("risk_assessments", [])
		high_risk = sum(1 for item in risk_items if item.risk_level.value == "high_risk")
		results.append(
			{
				"run_id": state["run_id"],
				"status": state.get("status", MigrationStatus.DISCOVERED).value,
				"counts": {
					"mappings": len(state.get("mappings", [])),
					"risk_assessments": len(risk_items),
					"high_risk": high_risk,
				},
			}
		)
	return {"runs": sorted(results, key=lambda item: str(item["run_id"]))}


@router.get("/runs/{run_id}")
def get_run_detail(run_id: str) -> dict[str, object]:
	try:
		state = get_run(run_id)
	except KeyError as exc:
		raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc
	return dump_jsonable_state(state)


@router.post("/runs/{run_id}/decision")
def submit_decision(run_id: str, payload: ApprovalDecisionRequest) -> dict[str, object]:
	if payload.decision == ApprovalDecisionValue.PENDING:
		raise HTTPException(status_code=400, detail="Decision cannot be pending for submission")

	try:
		state = get_run(run_id)
	except KeyError as exc:
		raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc
	decision = ApprovalDecision(
		decision=payload.decision,
		reviewer=payload.reviewer,
		timestamp=datetime.now(UTC),
		comments=payload.comments,
	)
	state["approval"] = decision

	route = route_after_approval(state)
	if route == "approved":
		state["status"] = MigrationStatus.APPROVED
	elif route == "rejected":
		state["status"] = MigrationStatus.REJECTED
	else:
		state["status"] = MigrationStatus.AWAITING_APPROVAL

	save_run(state)
	return {
		"run_id": run_id,
		"status": state["status"].value,
		"approval": decision.model_dump(mode="json"),
	}
