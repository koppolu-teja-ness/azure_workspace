"""Phase 0 parser/analyzer agent contract implementation."""

from __future__ import annotations

from .interfaces import AbstractAgent, AgentInput, AgentOutput


class ParserAnalyzerAgent(AbstractAgent):
	"""Transforms discovered resources into a normalized parsed graph."""

	agent_name = "parser_analyzer"

	async def run(self, agent_input: AgentInput) -> AgentOutput:
		discovered = agent_input.payload.get("discovered_resources", [])
		parsed_graph = {
			"nodes": discovered,
			"edges": agent_input.payload.get("dependency_edges", []),
		}
		return self.success(payload={"parsed_graph": parsed_graph})
