"""Mapping Agent (RAG) — owner: charan

Retrieves relevant mapping rules from the knowledge base (see
knowledge_base/schema/pgvector_schema.sql) and proposes the AWS-equivalent
resource for each discovered SourceResource, producing MappingRecord
entries.

This is the one agent shown as a class instead of a bare function, since it
naturally holds a retriever/LLM client as instance state. `run()` still has
the exact signature LangGraph expects — see base.py.
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.agents.base import BaseAgent
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


class MappingAgent(BaseAgent):
    name = "mapping_agent"

    def __init__(self, retriever: Any | None = None) -> None:
        # Phase 1 TODO (charan): wire in the real RAG retriever here, e.g.
        #   self.retriever = retriever or build_default_retriever()
        self.retriever = retriever

    def run(self, state: GraphState) -> dict[str, Any]:
        logger.info("mapping_agent: stub — no mappings produced yet")
        return {
            "mappings": [],
            "status": MigrationStatus.MAPPED,
        }


# Module-level singleton so workflow.py can import a plain callable, matching
# every other agent's `run` function signature.
_default_agent = MappingAgent()


def run(state: GraphState) -> dict[str, Any]:
    return _default_agent.run(state)
