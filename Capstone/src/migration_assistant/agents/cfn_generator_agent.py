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

from migration_assistant.cfn_generation.template_builder import build_target_resources
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    config = state.get("config", {})
    naming = config.get("naming", {}) if isinstance(config, dict) else {}
    naming_prefix = naming.get("prefix", "mig") if isinstance(naming, dict) else "mig"

    target_resources = build_target_resources(
        run_id=state["run_id"],
        source_resources=state.get("source_resources", []),
        mappings=state.get("mappings", []),
        naming_prefix=naming_prefix,
    )
    logger.info(
        "cfn_generator_agent: generated %d target resources", len(target_resources)
    )
    return {
        "target_resources": target_resources,
        "status": MigrationStatus.GENERATED,
    }
