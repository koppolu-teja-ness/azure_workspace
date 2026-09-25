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
from migration_assistant.config.app_config import parse_app_config
from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.llm.bedrock_runtime import parse_llm_provider_config
from migration_assistant.mapping.bedrock_client import (
    BedrockMappingClient,
)
from migration_assistant.mapping.rag_retriever import RuleBasedMappingRetriever

logger = logging.getLogger(__name__)


class MappingAgent(BaseAgent):
    name = "mapping_agent"

    def __init__(self, retriever: Any | None = None) -> None:
        self.retriever = retriever or RuleBasedMappingRetriever()

    def run(self, state: GraphState) -> dict[str, Any]:
        source_resources = state.get("source_resources", [])
        llm_traces = []

        deterministic_mappings = [
            self.retriever.map_resource(resource) for resource in source_resources
        ]

        app_config = parse_app_config(state.get("config"))
        llm_provider = parse_llm_provider_config(app_config)
        use_bedrock = llm_provider.settings is not None

        if use_bedrock:
            settings = llm_provider.settings
            assert settings is not None
            try:
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
            except Exception as exc:  # pragma: no cover - network/provider failures
                logger.exception(
                    "mapping_agent: Bedrock mapping failed (%s); "
                    "falling back to deterministic mappings",
                    exc,
                )
                mappings = deterministic_mappings
        else:
            if llm_provider.enabled and llm_provider.provider == "aws_bedrock":
                logger.warning(
                    "mapping_agent: Bedrock is enabled but configuration is incomplete; "
                    "falling back to deterministic mapping"
                )
            mappings = deterministic_mappings

        logger.info("mapping_agent: produced %d mappings", len(mappings))
        return {
            "mappings": mappings,
            "llm_traces": llm_traces,
            "status": MigrationStatus.MAPPED,
        }


# Module-level singleton so workflow.py can import a plain callable, matching
# every other agent's `run` function signature.
_default_agent = MappingAgent()


def run(state: GraphState) -> dict[str, Any]:
    return _default_agent.run(state)
