import pytest

from migration_assistant.agents import mapping_agent, planning_risk_agent, reporting_agent
from migration_assistant.graph.state import GraphState, MigrationStatus


def test_mapping_agent_raises_when_llm_config_missing() -> None:
    state: GraphState = {
        "run_id": "missing-llm-map",
        "created_at": "2026-09-25T00:00:00+00:00",
        "source_resources": [],
        "status": MigrationStatus.DISCOVERED,
        "config": {},
    }

    with pytest.raises(ValueError, match=r"mapping_agent: llm.enabled must be true"):
        mapping_agent.run(state)


def test_planning_risk_agent_raises_when_bedrock_model_id_missing() -> None:
    state: GraphState = {
        "run_id": "missing-model-risk",
        "created_at": "2026-09-25T00:00:00+00:00",
        "mappings": [],
        "status": MigrationStatus.STATIC_VALIDATED,
        "config": {
            "llm": {
                "enabled": True,
                "provider": "aws_bedrock",
                "bedrock": {
                    "model_id": "",
                },
            }
        },
    }

    with pytest.raises(
        ValueError,
        match=r"planning_risk_agent: incomplete Bedrock config; set llm.bedrock.model_id",
    ):
        planning_risk_agent.run(state)


def test_reporting_agent_raises_when_llm_provider_invalid() -> None:
    state: GraphState = {
        "run_id": "bad-provider-report",
        "created_at": "2026-09-25T00:00:00+00:00",
        "status": MigrationStatus.VERIFIED,
        "config": {
            "llm": {
                "enabled": True,
                "provider": "openai",
            }
        },
    }

    with pytest.raises(
        ValueError,
        match=r"reporting_agent: llm.provider must be 'aws_bedrock', got 'openai'",
    ):
        reporting_agent.run(state)
