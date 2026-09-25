"""Phase 0 discovery agent contract implementation."""

from __future__ import annotations

from .interfaces import AbstractAgent, AgentInput, AgentOutput


class DiscoveryAgent(AbstractAgent):
	"""Produces initial source inventory payload from Azure discovery inputs."""

	agent_name = "discovery"

	async def run(self, agent_input: AgentInput) -> AgentOutput:
		discovered_resources = agent_input.payload.get("discovered_resources", [])
		return self.success(
			payload={
				"discovered_resources": discovered_resources,
				"discovery_summary": {
					"resource_count": len(discovered_resources),
					"run_id": agent_input.run_id,
				},
			}
		)
