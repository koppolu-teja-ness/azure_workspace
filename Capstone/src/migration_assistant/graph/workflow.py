"""Exact Phase 0 workflow definition and LangGraph builder."""

from __future__ import annotations

from dataclasses import dataclass

from migration_assistant.agents import (
	AgentInput,
	CfnGeneratorAgent,
	DiscoveryAgent,
	MappingAgent,
	ParserAnalyzerAgent,
	ReportingAgent,
	SharedAgent,
	StaticValidationAgent,
)
from migration_assistant.graph.checkpoints import (
	CP_CFN_GENERATION,
	CP_DISCOVERY,
	CP_MAPPING,
	CP_PARSE_ANALYZE,
	CP_REPORTING,
	CP_STATIC_VALIDATION,
)
from migration_assistant.graph.state import WorkflowState

NODE_DISCOVERY = "discovery"
NODE_PARSER_ANALYZER = "parser_analyzer"
NODE_MAPPING = "mapping"
NODE_CFN_GENERATOR = "cfn_generator"
NODE_STATIC_VALIDATION = "static_validation"
NODE_REPORTING = "reporting"

EXACT_WORKFLOW_NODES: tuple[str, ...] = (
	NODE_DISCOVERY,
	NODE_PARSER_ANALYZER,
	NODE_MAPPING,
	NODE_CFN_GENERATOR,
	NODE_STATIC_VALIDATION,
	NODE_REPORTING,
)

EXACT_WORKFLOW_EDGES: tuple[tuple[str, str], ...] = (
	(NODE_DISCOVERY, NODE_PARSER_ANALYZER),
	(NODE_PARSER_ANALYZER, NODE_MAPPING),
	(NODE_MAPPING, NODE_CFN_GENERATOR),
	(NODE_CFN_GENERATOR, NODE_STATIC_VALIDATION),
	(NODE_STATIC_VALIDATION, NODE_REPORTING),
)


@dataclass(slots=True)
class WorkflowAgents:
	"""Container for all agent implementations used in the Phase 0 workflow."""

	discovery: SharedAgent
	parser_analyzer: SharedAgent
	mapping: SharedAgent
	cfn_generator: SharedAgent
	static_validation: SharedAgent
	reporting: SharedAgent


def default_workflow_agents() -> WorkflowAgents:
	"""Create default stub agent set shared by both branches in Phase 0."""

	return WorkflowAgents(
		discovery=DiscoveryAgent(),
		parser_analyzer=ParserAnalyzerAgent(),
		mapping=MappingAgent(),
		cfn_generator=CfnGeneratorAgent(),
		static_validation=StaticValidationAgent(),
		reporting=ReportingAgent(),
	)


async def _run_agent(
	agent: SharedAgent,
	state: WorkflowState,
	checkpoint_name: str,
) -> WorkflowState:
	agent_input = AgentInput(
		run_id=state["run_id"],
		spec_version=state.get("spec_version", "1.0.0"),
		payload={
			"discovered_resources": state.get("discovered_resources", []),
			"dependency_edges": state.get("parsed_graph", {}).get("edges", []),
			"parsed_graph": state.get("parsed_graph", {}),
			"retrieved_rules": state.get("retrieved_rules", []),
			"migration_spec": state.get("migration_spec", {}),
			"cfn_template": state.get("cfn_template", {}),
			"warnings": state.get("warnings", []),
			"errors": state.get("errors", []),
		},
	)

	result = await agent.run(agent_input)
	patch: WorkflowState = {}
	warnings = [*state.get("warnings", []), *result.warnings]
	errors = [*state.get("errors", []), *result.errors]

	patch["warnings"] = warnings
	patch["errors"] = errors
	patch["status"] = "failed" if result.status == "error" else "running"

	if "discovered_resources" in result.payload:
		patch["discovered_resources"] = result.payload["discovered_resources"]
	if "parsed_graph" in result.payload:
		patch["parsed_graph"] = result.payload["parsed_graph"]
	if "retrieved_rules" in result.payload:
		patch["retrieved_rules"] = result.payload["retrieved_rules"]
	if "migration_spec" in result.payload:
		patch["migration_spec"] = result.payload["migration_spec"]
	if "cfn_template" in result.payload:
		patch["cfn_template"] = result.payload["cfn_template"]
	if "static_validation_results" in result.payload:
		patch["static_validation_results"] = result.payload["static_validation_results"]
	if "report_summary" in result.payload:
		patch["report_summary"] = result.payload["report_summary"]

	checkpoints = dict(state.get("checkpoints", {}))
	checkpoints[checkpoint_name] = "done"
	patch["checkpoints"] = checkpoints
	return patch


def build_exact_workflow(agents: WorkflowAgents | None = None):
	"""Compile the exact Phase 0 LangGraph workflow.

	Node order is fixed as:
	discovery -> parser_analyzer -> mapping -> cfn_generator -> static_validation -> reporting
	"""

	agents = agents or default_workflow_agents()

	try:
		from langgraph.graph import END, StateGraph
	except ImportError as exc:
		raise RuntimeError(
			"langgraph is required to compile the workflow. Install it before running graph compilation."
		) from exc

	graph = StateGraph(WorkflowState)

	async def discovery_node(state: WorkflowState) -> WorkflowState:
		return await _run_agent(agents.discovery, state, CP_DISCOVERY)

	async def parser_analyzer_node(state: WorkflowState) -> WorkflowState:
		return await _run_agent(agents.parser_analyzer, state, CP_PARSE_ANALYZE)

	async def mapping_node(state: WorkflowState) -> WorkflowState:
		return await _run_agent(agents.mapping, state, CP_MAPPING)

	async def cfn_generator_node(state: WorkflowState) -> WorkflowState:
		return await _run_agent(agents.cfn_generator, state, CP_CFN_GENERATION)

	async def static_validation_node(state: WorkflowState) -> WorkflowState:
		return await _run_agent(agents.static_validation, state, CP_STATIC_VALIDATION)

	async def reporting_node(state: WorkflowState) -> WorkflowState:
		patch = await _run_agent(agents.reporting, state, CP_REPORTING)
		patch["status"] = "completed" if not patch.get("errors") else patch.get("status", "failed")
		return patch

	graph.add_node(NODE_DISCOVERY, discovery_node)
	graph.add_node(NODE_PARSER_ANALYZER, parser_analyzer_node)
	graph.add_node(NODE_MAPPING, mapping_node)
	graph.add_node(NODE_CFN_GENERATOR, cfn_generator_node)
	graph.add_node(NODE_STATIC_VALIDATION, static_validation_node)
	graph.add_node(NODE_REPORTING, reporting_node)

	graph.set_entry_point(NODE_DISCOVERY)
	graph.add_edge(NODE_DISCOVERY, NODE_PARSER_ANALYZER)
	graph.add_edge(NODE_PARSER_ANALYZER, NODE_MAPPING)
	graph.add_edge(NODE_MAPPING, NODE_CFN_GENERATOR)
	graph.add_edge(NODE_CFN_GENERATOR, NODE_STATIC_VALIDATION)
	graph.add_edge(NODE_STATIC_VALIDATION, NODE_REPORTING)
	graph.add_edge(NODE_REPORTING, END)

	return graph.compile()
