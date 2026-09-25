"""Discovery Agent — owner: charan

Enumerates Azure Key Vault, Function App, and VNet resources via the Azure
SDK/CLI, and/or ingests existing Bicep files, producing SourceResource
entries (see graph/state.py).

Phase 0: this is a stub. It returns the state unchanged (plus a log line) so
the graph can be wired and smoke-tested end-to-end before real logic lands
in Phase 1. See azure_discovery/ for where the real implementation should
live (sdk_client.py, bicep_decompiler.py, resource_inventory.py).
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.azure_discovery.resource_inventory import discover_bicep_files
from migration_assistant.config.app_config import app_config_to_state, parse_app_config
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    app_config = parse_app_config(state.get("config"))
    bicep_files = discover_bicep_files(
        bicep_paths=app_config.bicep_paths,
        bicep_directories=app_config.bicep_directories,
    )
    app_config.discovered_bicep_files = bicep_files
    logger.info("discovery_agent: discovered %d bicep files", len(bicep_files))
    return {
        "config": app_config_to_state(app_config),
        "status": MigrationStatus.DISCOVERED,
    }
