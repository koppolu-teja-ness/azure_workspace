"""Planning & Risk-Scoring Agent — owner: charan

Builds the migration plan: dependency-ordered sequencing, and classifies
each resource as auto-migratable / needs-review / high-risk, producing
RiskAssessment entries.

Phase 0: stub. Real implementation lives in planning/ (risk_scoring.py,
sequencing.py).
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.config.app_config import parse_app_config
from migration_assistant.graph.state import GraphState, MigrationStatus, RiskAssessment
from migration_assistant.llm.bedrock_runtime import parse_llm_provider_config
from migration_assistant.planning.bedrock_risk_reasoner import BedrockRiskReasoner
from migration_assistant.planning.risk_scoring import assess_risks

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    app_config = parse_app_config(state.get("config"))
    threshold = app_config.risk_thresholds.min_auto_migratable_confidence
    risk_assessments = assess_risks(
        mappings=state.get("mappings", []),
        min_auto_migratable_confidence=float(threshold),
    )
    llm_traces = []

    llm_provider = parse_llm_provider_config(app_config)
    if llm_provider.settings is not None:
        reasoner = BedrockRiskReasoner(settings=llm_provider.settings)
        enriched: list[RiskAssessment] = []
        for mapping, assessment in zip(
            state.get("mappings", []),
            risk_assessments,
            strict=False,
        ):
            try:
                extra_reasons, trace = reasoner.suggest_reasons(mapping, assessment)
                llm_traces.append(trace)
            except Exception as exc:  # pragma: no cover - network/provider failures
                logger.exception(
                    "planning_risk_agent: Bedrock enrichment failed (%s); "
                    "keeping deterministic reasons",
                    exc,
                )
                extra_reasons = []

            if extra_reasons:
                assessment.reasons = list(dict.fromkeys([*assessment.reasons, *extra_reasons]))
            enriched.append(assessment)
        risk_assessments = enriched

    logger.info("planning_risk_agent: produced %d risk assessments", len(risk_assessments))
    return {
        "risk_assessments": risk_assessments,
        "llm_traces": llm_traces,
        "status": MigrationStatus.PLANNED,
    }
