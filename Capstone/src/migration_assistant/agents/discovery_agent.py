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
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    config = dict(state.get("config", {}))
    bicep_paths = config.get("bicep_paths", [])
    bicep_directories = config.get("bicep_directories", [])

    discovered_files = discover_bicep_files(
        bicep_paths=bicep_paths if isinstance(bicep_paths, list) else [],
        bicep_directories=bicep_directories if isinstance(bicep_directories, list) else [],
    )
    config["discovered_bicep_files"] = discovered_files

    logger.info("discovery_agent: discovered %d bicep files", len(discovered_files))
    return {
        "config": config,
        "status": MigrationStatus.DISCOVERED,
    }
