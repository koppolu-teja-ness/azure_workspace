"""Bedrock-based risk reasoning helper.

Used to enrich deterministic risk assessments with concise rationale.
"""
from __future__ import annotations

from typing import Any

from migration_assistant.graph.state import LLMTraceEvent, MappingRecord, RiskAssessment
from migration_assistant.llm.bedrock_runtime import (
    BedrockSettings,
    build_trace_event,
    invoke_bedrock_text,
    parse_json_object,
)


class BedrockRiskReasoner:
    def __init__(self, settings: BedrockSettings, runtime_client: Any | None = None) -> None:
        self.settings = settings
        self._client = runtime_client

    def suggest_reasons(
        self,
        mapping: MappingRecord,
        risk: RiskAssessment,
    ) -> tuple[list[str], LLMTraceEvent]:
        prompt = _build_prompt(mapping, risk)
        text = invoke_bedrock_text(
            settings=self.settings,
            prompt=prompt,
            runtime_client=self._client,
        )
        trace = build_trace_event(
            node="plan_risk",
            prompt_version=RISK_REASONING_PROMPT_VERSION,
            settings=self.settings,
            status="ok",
            prompt_text=prompt,
            response_text=text,
        )
        payload = parse_json_object(text)
        if not payload:
            trace.status = "unparsed_json"
            return [], trace

        raw = payload.get("additional_reasons", [])
        if not isinstance(raw, list):
            trace.status = "invalid_payload"
            return [], trace
        return [str(item).strip() for item in raw if str(item).strip()], trace


def _build_prompt(mapping: MappingRecord, risk: RiskAssessment) -> str:
    return (
        "You are a cloud migration risk reviewer.\n"
        "Given a baseline risk assessment, propose up to 3 concise additional reasons.\n"
        "Do not change the risk level.\n\n"
        "Return ONLY JSON: {\"additional_reasons\": [\"...\"]}.\n\n"
        f"Mapping:\n{mapping.model_dump_json(indent=2)}\n\n"
        f"Risk assessment:\n{risk.model_dump_json(indent=2)}\n"
    )


RISK_REASONING_PROMPT_VERSION = "risk_reasoning_v1"
