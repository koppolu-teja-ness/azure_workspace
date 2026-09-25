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

from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("discovery_agent: stub — no resources discovered yet")
    return {
        "source_resources": [],
        "status": MigrationStatus.DISCOVERED,
    }
