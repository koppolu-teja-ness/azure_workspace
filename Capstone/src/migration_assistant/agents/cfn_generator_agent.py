"""CFN Generator Agent — owner: saurav

Produces syntactically valid CloudFormation YAML from the mapped resource
graph (state["mappings"] + state["source_resources"]), populating
state["target_resources"].

Phase 0: stub. Real implementation lives in cfn_generation/ (template
builder + Jinja templates per resource type).
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("cfn_generator_agent: stub — no CFN generated yet")
    return {
        "target_resources": [],
        "status": MigrationStatus.GENERATED,
    }
