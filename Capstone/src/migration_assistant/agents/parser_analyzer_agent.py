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

from migration_assistant.bicep_parser.ast_parser import parse_bicep_file
from migration_assistant.bicep_parser.resource_graph import to_source_resources
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    config = dict(state.get("config", {}))
    run_id = state.get("run_id", "unknown-run")

    discovered_files = config.get("discovered_bicep_files", [])
    if not isinstance(discovered_files, list):
        discovered_files = []

    parsed_resources = []
    for file_path in discovered_files:
        parsed_resources.extend(parse_bicep_file(str(file_path)))

    source_resources = to_source_resources(parsed_resources, run_id=run_id)
    logger.info(
        "parser_analyzer_agent: parsed %d resources from %d files",
        len(source_resources),
        len(discovered_files),
    )

    return {
        "source_resources": source_resources,
        "status": MigrationStatus.PARSED,
    }
