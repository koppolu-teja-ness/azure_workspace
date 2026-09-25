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
from migration_assistant.llm.bedrock_runtime import require_bedrock_settings
from migration_assistant.mapping.bedrock_client import (
    BedrockMappingClient,
)
from migration_assistant.mapping.rag_retriever import RuleBasedMappingRetriever

logger = logging.getLogger(__name__)


class MappingAgent(BaseAgent):
    name = "mapping_agent"

    def __init__(self, retriever: Any | None = None) -> None:
        # Phase 1 TODO (charan): wire in the real RAG retriever here, e.g.
        #   self.retriever = retriever or build_default_retriever()
        self.retriever = retriever

    def run(self, state: GraphState) -> dict[str, Any]:
        logger.info("mapping_agent: stub — no mappings produced yet")
        source_resources = state.get("source_resources", [])
        llm_traces = []

        deterministic_mappings = [
            self.retriever.map_resource(resource) for resource in source_resources
        ]

        app_config = parse_app_config(state.get("config"))
        settings = require_bedrock_settings(
            app_config=app_config,
            agent_name=self.name,
        )

        llm_client = BedrockMappingClient(settings=settings)
        mappings = []
        for resource, base_mapping in zip(
            source_resources,
            deterministic_mappings,
            strict=False,
        ):
            mapped, trace = llm_client.map_resource(resource, base_mapping)
            mappings.append(mapped)
            llm_traces.append(trace)

        logger.info(
            "mapping_agent: Bedrock LLM mapping enabled with model %s",
            settings.model_id,
        )

        logger.info("mapping_agent: produced %d mappings", len(mappings))
        return {
            "mappings": [],
            "status": MigrationStatus.MAPPED,
        }


# Module-level singleton so workflow.py can import a plain callable, matching
# every other agent's `run` function signature.
_default_agent = MappingAgent()


def run(state: GraphState) -> dict[str, Any]:
    return _default_agent.run(state)
