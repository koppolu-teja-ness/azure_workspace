"""Human Approval Gate — owner: charan.

Phase 2 behavior:
- if approval.decision is already provided by UI/API, honor it
- if decision is pending and config.approval.auto_approve is true, auto-approve
- otherwise park the run in awaiting_approval so orchestration can stop safely
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
    config = state.get("config", {})
    approval_cfg = config.get("approval", {}) if isinstance(config, dict) else {}
    auto_approve = bool(approval_cfg.get("auto_approve", False))
    auto_reviewer = str(approval_cfg.get("auto_reviewer", "system-auto-approve"))

    decision = state.get("approval", ApprovalDecision())
    now = datetime.now(UTC)

    if decision.decision == ApprovalDecisionValue.PENDING:
        if auto_approve:
            auto_decision = ApprovalDecision(
                decision=ApprovalDecisionValue.APPROVED,
                reviewer=auto_reviewer,
                timestamp=now,
                comments="Auto-approved by config.approval.auto_approve",
            )
            logger.info("approval_gate: auto-approved by configuration")
            return {
                "approval": auto_decision,
                "status": MigrationStatus.APPROVED,
            }

        logger.info("approval_gate: awaiting human approval decision")
        return {
            "approval": decision,
            "status": MigrationStatus.AWAITING_APPROVAL,
        }

    if decision.decision == ApprovalDecisionValue.APPROVED:
        return {
            "approval": _ensure_timestamp(decision, now),
            "status": MigrationStatus.APPROVED,
        }
    if decision.decision == ApprovalDecisionValue.REJECTED:
        return {
            "approval": _ensure_timestamp(decision, now),
            "status": MigrationStatus.REJECTED,
        }

    return {
        "approval": _ensure_timestamp(decision, now),
        "status": MigrationStatus.AWAITING_APPROVAL,
    }


def _ensure_timestamp(decision: ApprovalDecision, now: datetime) -> ApprovalDecision:
    if decision.timestamp is not None:
        return decision
    return ApprovalDecision(
        decision=decision.decision,
        reviewer=decision.reviewer,
        timestamp=now,
        comments=decision.comments,
    )


def route_after_approval(state: GraphState) -> str:
    """Conditional-edge router used by workflow.py to branch on the human
    decision: approved -> deploy, rejected -> end, modified -> back to
    mapping for another pass."""
    decision = state.get("approval", ApprovalDecision()).decision
    if decision == ApprovalDecisionValue.PENDING:
        return "pending"
    if decision == ApprovalDecisionValue.APPROVED:
        return "approved"
    if decision == ApprovalDecisionValue.REJECTED:
        return "rejected"
    return "modified"
