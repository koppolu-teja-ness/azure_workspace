"""LangGraph skeleton wiring every agent node together.

This is Phase-0 joint-ownership territory: both of you add/adjust nodes
here as your agents mature, so treat changes to this file as small,
reviewed-by-both PRs rather than bundling them into a feature-branch PR.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from migration_assistant.agents import (
    approval_gate,
    cfn_generator_agent,
    deployment_agent,
    discovery_agent,
    mapping_agent,
    parser_analyzer_agent,
    planning_risk_agent,
    post_deploy_validation_agent,
    reporting_agent,
    static_validation_agent,
)
from migration_assistant.graph.state import GraphState


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("discovery", discovery_agent.run)
    graph.add_node("parse_analyze", parser_analyzer_agent.run)
    graph.add_node("map", mapping_agent.run)
    graph.add_node("generate_cfn", cfn_generator_agent.run)
    graph.add_node("static_validate", static_validation_agent.run)
    graph.add_node("plan_risk", planning_risk_agent.run)
    graph.add_node("human_approval", approval_gate.run)
    graph.add_node("deploy", deployment_agent.run)
    graph.add_node("post_deploy_validate", post_deploy_validation_agent.run)
    graph.add_node("report", reporting_agent.run)

    graph.set_entry_point("discovery")
    graph.add_edge("discovery", "parse_analyze")
    graph.add_edge("parse_analyze", "map")
    graph.add_edge("map", "generate_cfn")
    graph.add_edge("generate_cfn", "static_validate")
    graph.add_edge("static_validate", "plan_risk")
    graph.add_edge("plan_risk", "human_approval")

    graph.add_conditional_edges(
        "human_approval",
        approval_gate.route_after_approval,
        {
            "approved": "deploy",
            "rejected": END,
            "modified": "map",
        },
    )

    graph.add_edge("deploy", "post_deploy_validate")
    graph.add_edge("post_deploy_validate", "report")
    graph.add_edge("report", END)

    # Phase 2+ TODO: consider
    #   graph.compile(interrupt_before=["human_approval"])
    # so a real UI can pause the graph, collect a decision, and resume it,
    # instead of approval_gate.run() auto-approving as it does today.
    return graph.compile()


if __name__ == "__main__":
    # Smoke test: run the full stub pipeline end-to-end. This is the Phase 0
    # exit criterion referenced in docs/phase0_checklist.md.
    import logging

    from migration_assistant.graph.state import MigrationStatus

    logging.basicConfig(level=logging.INFO)
    app = build_graph()
    initial_state: GraphState = {
        "run_id": "phase0-smoke-test",
        "created_at": "2026-09-25T00:00:00+00:00",
        "source_resources": [],
        "target_resources": [],
        "mappings": [],
        "risk_assessments": [],
        "validation_results": [],
        "llm_traces": [],
        "status": MigrationStatus.DISCOVERED,
        "config": {},
    }
    final_state = app.invoke(initial_state)
    # Runs discovery -> ... -> human_approval (auto-approves) -> deploy ->
    # post_deploy_validate -> report, so the final status is VERIFIED.
    print("Final status:", final_state["status"])
