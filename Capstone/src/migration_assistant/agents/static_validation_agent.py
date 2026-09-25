"""Static Validation Agent — owner: saurav

Runs cfn-lint, checkov/cfn_nag policy scans, and schema validation on the
generated CloudFormation templates, producing ValidationResult entries
(stage="static").

Phase 0: stub. Real implementation lives in validation/static/
(cfn_lint_runner.py, checkov_runner.py, schema_validator.py).
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("static_validation_agent: stub — no static checks run yet")
    return {
        "validation_results": [],
        "status": MigrationStatus.STATIC_VALIDATED,
    }
