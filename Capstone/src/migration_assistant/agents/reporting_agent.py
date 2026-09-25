"""Phase 0 reporting agent contract implementation."""

from __future__ import annotations

from .interfaces import AbstractAgent, AgentInput, AgentOutput


class ReportingAgent(AbstractAgent):
	"""Compiles run summary artifacts from prior workflow outputs."""

	agent_name = "reporting"

	async def run(self, agent_input: AgentInput) -> AgentOutput:
		return self.success(
			payload={
				"report_summary": {
					"run_id": agent_input.run_id,
					"status": "completed",
					"warnings": len(agent_input.payload.get("warnings", [])),
					"errors": len(agent_input.payload.get("errors", [])),
				}
			}
		)
