"""AWS Bedrock-backed mapping helper for the mapping agent.

This module keeps LLM interaction isolated so the agent can switch between
rule-based deterministic mapping and Bedrock-enhanced mapping via config.
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import LLMTraceEvent, MappingRecord, SourceResource
from migration_assistant.llm.bedrock_runtime import (
    BedrockSettings,
    build_trace_event,
    invoke_bedrock_text,
    parse_json_object,
)

logger = logging.getLogger(__name__)


class BedrockMappingClient:
    """Generates mapping refinements using an AWS Bedrock chat model."""

    def __init__(
        self,
        settings: BedrockSettings,
        runtime_client: Any | None = None,
    ) -> None:
        self.settings = settings
        self._client = runtime_client

    def map_resource(
        self,
        resource: SourceResource,
        deterministic_mapping: MappingRecord,
    ) -> tuple[MappingRecord, LLMTraceEvent]:
        prompt = _build_prompt(resource, deterministic_mapping)
        llm_text = invoke_bedrock_text(
            settings=self.settings,
            prompt=prompt,
            runtime_client=self._client,
        )
        trace = build_trace_event(
            node="map",
            prompt_version=MAPPING_PROMPT_VERSION,
            settings=self.settings,
            status="ok",
            prompt_text=prompt,
            response_text=llm_text,
        )
        parsed = parse_json_object(llm_text)
        if not parsed:
            logger.warning(
                "bedrock_client: LLM output could not be parsed; using deterministic mapping"
            )
            trace.status = "unparsed_json"
            return deterministic_mapping, trace

        return MappingRecord(
            source_resource_id=resource.resource_id,
            target_logical_id=parsed.get("target_logical_id")
            or deterministic_mapping.target_logical_id,
            mapping_rule_id=parsed.get("mapping_rule_id")
            or deterministic_mapping.mapping_rule_id,
            confidence=float(parsed.get("confidence", deterministic_mapping.confidence)),
            notes=list(parsed.get("notes", deterministic_mapping.notes)),
            unmapped_properties=list(
                parsed.get("unmapped_properties", deterministic_mapping.unmapped_properties)
            ),
        ), trace


MAPPING_PROMPT_VERSION = "mapping_v1"


def _build_prompt(resource: SourceResource, deterministic_mapping: MappingRecord) -> str:
    # Keep prompt explicit and JSON-only to minimize parser ambiguity.
    return (
        "You are an Azure-to-AWS infrastructure mapping expert. "
        "Use the baseline mapping as context, then choose the best target mapping.\n\n"
        "Return ONLY valid JSON with keys: "
        "target_logical_id, mapping_rule_id, confidence, notes, unmapped_properties.\n"
        "- confidence must be in [0, 1].\n"
        "- notes must be a list of short strings.\n"
        "- unmapped_properties must be a list of property names not confidently mapped.\n\n"
        f"Source resource:\n{resource.model_dump_json(indent=2)}\n\n"
        f"Baseline mapping context:\n{deterministic_mapping.model_dump_json(indent=2)}\n"
    )

