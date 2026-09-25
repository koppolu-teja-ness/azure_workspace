"""Bedrock report summary helper for reporting agent."""
from __future__ import annotations

from typing import Any

from migration_assistant.graph.state import GraphState, LLMTraceEvent
from migration_assistant.llm.bedrock_runtime import (
    BedrockSettings,
    build_trace_event,
    invoke_bedrock_text,
)


class BedrockReportWriter:
    def __init__(self, settings: BedrockSettings, runtime_client: Any | None = None) -> None:
        self.settings = settings
        self._client = runtime_client

    def write_summary(self, state: GraphState) -> tuple[str, LLMTraceEvent]:
        prompt = _build_prompt(state)
        text = invoke_bedrock_text(
            settings=self.settings,
            prompt=prompt,
            runtime_client=self._client,
        ).strip()
        trace = build_trace_event(
            node="report",
            prompt_version=REPORT_SUMMARY_PROMPT_VERSION,
            settings=self.settings,
            status="ok",
            prompt_text=prompt,
            response_text=text,
        )
        return text, trace


def _build_prompt(state: GraphState) -> str:
    source_count = len(state.get("source_resources", []))
    mapping_count = len(state.get("mappings", []))
    risk_count = len(state.get("risk_assessments", []))
    validation_count = len(state.get("validation_results", []))

    return (
        "Write a concise Azure-to-AWS migration run summary in 5 to 8 lines.\n"
        "Mention current status, risk posture, and validation outcome if present.\n"
        "Do not invent resource counts.\n\n"
        f"run_id: {state.get('run_id')}\n"
        f"status: {state.get('status')}\n"
        f"source_resources: {source_count}\n"
        f"mappings: {mapping_count}\n"
        f"risk_assessments: {risk_count}\n"
        f"validation_results: {validation_count}\n"
    )


REPORT_SUMMARY_PROMPT_VERSION = "report_summary_v1"
