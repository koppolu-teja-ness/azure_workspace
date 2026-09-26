from migration_assistant.agents import approval_gate
from migration_assistant.graph.state import (
    ApprovalDecision,
    ApprovalDecisionValue,
    GraphState,
    MigrationStatus,
)


def test_approval_gate_marks_awaiting_when_pending_and_manual() -> None:
    state: GraphState = {
        "run_id": "approval-pending",
        "created_at": "2026-09-25T00:00:00+00:00",
        "approval": ApprovalDecision(),
        "status": MigrationStatus.PLANNED,
        "config": {
            "approval": {
                "auto_approve": False,
            }
        },
    }

    result = approval_gate.run(state)

    assert result["status"] == MigrationStatus.AWAITING_APPROVAL
    assert result["approval"].decision == ApprovalDecisionValue.PENDING


def test_approval_gate_auto_approves_when_configured() -> None:
    state: GraphState = {
        "run_id": "approval-auto",
        "created_at": "2026-09-25T00:00:00+00:00",
        "approval": ApprovalDecision(),
        "status": MigrationStatus.PLANNED,
        "config": {
            "approval": {
                "auto_approve": True,
                "auto_reviewer": "ci",
            }
        },
    }

    result = approval_gate.run(state)

    assert result["status"] == MigrationStatus.APPROVED
    assert result["approval"].decision == ApprovalDecisionValue.APPROVED
    assert result["approval"].reviewer == "ci"


def test_route_after_approval_routes_pending() -> None:
    state: GraphState = {
        "run_id": "approval-route",
        "created_at": "2026-09-25T00:00:00+00:00",
        "approval": ApprovalDecision(),
    }

    assert approval_gate.route_after_approval(state) == "pending"
