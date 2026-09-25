"""Reporting Agent — owner: joint

charan writes the migration-plan/risk-report sections (Phase 3), saurav
writes the execution/validation-report sections (Phase 3). Produces the
final structured reports described in the design doc (migration plan,
execution report, validation report).

Phase 0: stub that just logs the final status.
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.config.app_config import app_config_to_state, parse_app_config
from migration_assistant.graph.state import GraphState
from migration_assistant.llm.bedrock_runtime import parse_llm_provider_config
from migration_assistant.reporting.bedrock_report_writer import BedrockReportWriter

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("reporting_agent: stub report — status=%s", state.get("status"))
    app_config = parse_app_config(state.get("config"))
    llm_provider = parse_llm_provider_config(app_config)
    llm_traces = []

    if llm_provider.settings is not None:
        try:
            writer = BedrockReportWriter(settings=llm_provider.settings)
            summary, trace = writer.write_summary(state)
            app_config.report_summary = summary
            llm_traces.append(trace)
            logger.info("reporting_agent: Bedrock summary generated")
        except Exception as exc:  # pragma: no cover - network/provider failures
            logger.exception(
                "reporting_agent: Bedrock summary generation failed (%s); "
                "keeping deterministic path",
                exc,
            )

    return {
        "config": app_config_to_state(app_config),
        "llm_traces": llm_traces,
    }
