"""Parser/Analyzer Agent — owner: charan

Parses Bicep (via `az bicep build` -> ARM JSON, or AST parsing) and extracts
the resource dependency graph and properties for each SourceResource
discovered upstream.

Phase 0: stub. Real implementation lives in bicep_parser/ (bicep_to_arm.py,
ast_parser.py, resource_graph.py).
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("parser_analyzer_agent: stub — nothing to parse yet")
    return {
        "status": MigrationStatus.PARSED,
    }
