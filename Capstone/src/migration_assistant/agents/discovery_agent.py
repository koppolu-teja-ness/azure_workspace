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

from migration_assistant.azure_discovery.sdk_client import discover_resource_group_resources
from migration_assistant.azure_discovery.resource_inventory import discover_bicep_files
from migration_assistant.config.app_config import parse_app_config
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    app_config = parse_app_config(state.get("config"))
    config = dict(state.get("config", {}))
    bicep_paths = config.get("bicep_paths", [])
    bicep_directories = config.get("bicep_directories", [])

    discovered_files = discover_bicep_files(
        bicep_paths=bicep_paths if isinstance(bicep_paths, list) else [],
        bicep_directories=bicep_directories if isinstance(bicep_directories, list) else [],
    )
    config["discovered_bicep_files"] = discovered_files

    discovery_summary: dict[str, Any] = {
        "source": "local_bicep",
        "discovered_file_count": len(discovered_files),
    }

    sdk_config = app_config.azure_discovery
    if sdk_config.enable_sdk_discovery:
        subscription_id = (sdk_config.subscription_id or "").strip()
        resource_group = (sdk_config.resource_group or "").strip()
        if subscription_id and resource_group:
            try:
                resources = discover_resource_group_resources(
                    subscription_id=subscription_id,
                    resource_group=resource_group,
                )
                discovery_summary["sdk_mode"] = "resource_group"
                discovery_summary["sdk_resource_count"] = len(resources)
                config["sdk_discovered_resources"] = resources
            except Exception as exc:  # pragma: no cover - runtime/cloud errors
                discovery_summary["sdk_error"] = str(exc)
        else:
            discovery_summary["sdk_error"] = (
                "azure_discovery.subscription_id and azure_discovery.resource_group are required"
            )

    config["discovery_summary"] = discovery_summary

    logger.info("discovery_agent: discovered %d bicep files", len(discovered_files))
    return {
        "config": config,
        "status": MigrationStatus.DISCOVERED,
    }
