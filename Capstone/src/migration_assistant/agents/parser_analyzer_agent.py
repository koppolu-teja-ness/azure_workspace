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
from migration_assistant.config.app_config import parse_app_config
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    app_config = parse_app_config(state.get("config"))
    bicep_files = app_config.discovered_bicep_files

    parsed = []
    for file_path in bicep_files:
        parsed.extend(parse_bicep_file(file_path))

    source_resources = to_source_resources(parsed_resources=parsed, run_id=state["run_id"])
    logger.info(
        "parser_analyzer_agent: parsed %d resources from %d files",
        len(source_resources),
        len(bicep_files),
    )
    return {
        "source_resources": source_resources,
        "status": MigrationStatus.PARSED,
    }
