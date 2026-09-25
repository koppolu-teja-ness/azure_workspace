"""Reporting Agent — owner: joint

charan writes the migration-plan/risk-report sections (Phase 3), saurav
writes the execution/validation-report sections (Phase 3). Produces the
final structured reports described in the design doc (migration plan,
execution report, validation report).

Phase 0: stub that just logs the final status.
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import GraphState

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("reporting_agent: stub report — status=%s", state.get("status"))
    return {}
