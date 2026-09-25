"""Smoke test: the LangGraph skeleton should compile and run end-to-end with
every agent stubbed out. Run this after every merge point in Phase 1-3 to
catch drift between the two branches."""
from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.graph.workflow import build_graph


def test_graph_compiles_and_runs_end_to_end_with_stubs(monkeypatch):
    def _mock_report_llm(*, settings, prompt, runtime_client=None):
        _ = settings, prompt, runtime_client
        return "Smoke summary"

    monkeypatch.setattr(
        "migration_assistant.reporting.bedrock_report_writer.invoke_bedrock_text",
        _mock_report_llm,
    )

    app = build_graph()

    initial_state: GraphState = {
        "run_id": "test-run",
        "created_at": "2026-09-25T00:00:00+00:00",
        "source_resources": [],
        "target_resources": [],
        "mappings": [],
        "risk_assessments": [],
        "validation_results": [],
        "llm_traces": [],
        "status": MigrationStatus.DISCOVERED,
        "config": {
            "llm": {
                "enabled": True,
                "provider": "aws_bedrock",
                "bedrock": {
                    "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "temperature": 0.7,
                },
            }
        },
    }

    final_state = app.invoke(initial_state)

    # With the Phase-0 approval_gate stub auto-approving, the graph should
    # run all the way through deploy -> post_deploy_validate -> report,
    # ending with the status the last-run agent (post_deploy_validation_agent)
    # sets.
    assert final_state["status"] == MigrationStatus.VERIFIED
