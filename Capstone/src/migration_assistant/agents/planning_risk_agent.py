"""Planning & Risk-Scoring Agent — owner: charan

Builds the migration plan: dependency-ordered sequencing, and classifies
each resource as auto-migratable / needs-review / high-risk, producing
RiskAssessment entries.

Phase 0: stub. Real implementation lives in planning/ (risk_scoring.py,
sequencing.py).
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("planning_risk_agent: stub — no risk assessments produced yet")
    return {
        "risk_assessments": [],
        "status": MigrationStatus.PLANNED,
    }
