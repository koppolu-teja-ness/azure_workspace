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
from migration_assistant.bicep_parser.bicep_to_arm import compile_bicep_file_to_arm_resources
from migration_assistant.bicep_parser.models import ParsedBicepResource
from migration_assistant.bicep_parser.resource_graph import to_source_resources
from migration_assistant.config.app_config import parse_app_config
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    app_config = parse_app_config(state.get("config"))
    config = dict(state.get("config", {}))
    run_id = state.get("run_id", "unknown-run")

    discovered_files = config.get("discovered_bicep_files", [])
    if not isinstance(discovered_files, list):
        discovered_files = []

    parsed_resources = []
    parser_metadata: list[dict[str, str]] = []
    for file_path in discovered_files:
        source = "fallback_ast_parser"
        if app_config.parser.prefer_azure_cli_compile:
            compile_result = compile_bicep_file_to_arm_resources(str(file_path))
            if compile_result is not None:
                arm_resources = _parsed_resources_from_arm(compile_result.resources)
                if arm_resources:
                    parsed_resources.extend(arm_resources)
                    source = compile_result.provenance
                    parser_metadata.append({"file": str(file_path), "parser": source})
                    continue

        if app_config.parser.allow_fallback_parser:
            parsed_resources.extend(parse_bicep_file(str(file_path)))
            parser_metadata.append({"file": str(file_path), "parser": source})

    if parser_metadata:
        config["parser_provenance"] = parser_metadata

    source_resources = to_source_resources(parsed_resources, run_id=run_id)
    logger.info(
        "parser_analyzer_agent: parsed %d resources from %d files",
        len(source_resources),
        len(discovered_files),
    )

    return {
        "config": config,
        "source_resources": source_resources,
        "status": MigrationStatus.PARSED,
    }


def _parsed_resources_from_arm(resources: list[dict[str, Any]]) -> list[ParsedBicepResource]:
    parsed: list[ParsedBicepResource] = []
    for item in resources:
        resource_type = item.get("type")
        api_version = item.get("apiVersion")
        name = item.get("name")
        location = item.get("location", "unknown")
        properties = item.get("properties")
        depends_on = item.get("dependsOn")

        if not isinstance(resource_type, str) or not resource_type:
            continue
        if not isinstance(api_version, str) or not api_version:
            continue
        if not isinstance(name, str) or not name:
            continue

        parsed.append(
            ParsedBicepResource(
                symbolic_name=_arm_name_to_symbol(name),
                resource_type=resource_type,
                api_version=api_version,
                name=name,
                location=location if isinstance(location, str) else "unknown",
                depends_on=list(depends_on) if isinstance(depends_on, list) else [],
                properties=properties if isinstance(properties, dict) else {},
            )
        )

    return parsed


def _arm_name_to_symbol(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else " " for ch in name)
    symbol = "".join(part.capitalize() for part in cleaned.split())
    return symbol or "Resource"
