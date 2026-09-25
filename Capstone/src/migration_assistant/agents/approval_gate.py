"""Human Approval Gate — owner: charan

In the compiled graph this node is a natural interrupt point: LangGraph can
pause execution here (e.g. `graph.compile(interrupt_before=["human_approval"])`)
so a human can inspect state["risk_assessments"] and state["mappings"] before
the graph is resumed with an ApprovalDecision written into state["approval"].

Phase 0: stub that auto-approves, purely so the skeleton graph can run
end-to-end without a human in the loop yet. Replace the `run()` body with a
real UI-backed wait before Phase 2 (Streamlit or React, per the design doc).
`route_after_approval` is the actual contract workflow.py depends on and
should stay stable regardless of how `run()` evolves.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from migration_assistant.graph.state import (
    ApprovalDecision,
    ApprovalDecisionValue,
    GraphState,
    MigrationStatus,
)

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.warning(
        "approval_gate: stub auto-approval in effect — replace with a real "
        "human-in-the-loop UI before Phase 2"
    )
    decision = ApprovalDecision(
        decision=ApprovalDecisionValue.APPROVED,
        reviewer="stub",
        timestamp=datetime.now(UTC),
        comments="Phase 0 stub auto-approval",
    )
    return {
        "approval": decision,
        "status": MigrationStatus.APPROVED,
    }


def route_after_approval(state: GraphState) -> str:
    """Conditional-edge router used by workflow.py to branch on the human
    decision: approved -> deploy, rejected -> end, modified -> back to
    mapping for another pass."""
    decision = state.get("approval", ApprovalDecision()).decision
    if decision == ApprovalDecisionValue.APPROVED:
        return "approved"
    if decision == ApprovalDecisionValue.REJECTED:
        return "rejected"
    return "modified"
