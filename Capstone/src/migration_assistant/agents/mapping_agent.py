"""Phase 0 mapping agent contract implementation."""

from __future__ import annotations

from datetime import datetime, timezone

from .interfaces import AbstractAgent, AgentInput, AgentOutput


class MappingAgent(AbstractAgent):
	"""Maps parsed graph content to migration spec contract skeleton."""

	agent_name = "mapping"

	async def run(self, agent_input: AgentInput) -> AgentOutput:
		migration_spec = agent_input.payload.get("migration_spec")
		if migration_spec is None:
			migration_spec = {
				"spec_version": agent_input.spec_version,
				"generated_at": datetime.now(timezone.utc).isoformat(),
				"source": agent_input.payload.get("source", {}),
				"resources": agent_input.payload.get("discovered_resources", []),
				"dependencies": agent_input.payload.get("dependency_edges", []),
				"mapping_decisions": [],
				"target_drafts": [],
				"validation_hints": {
					"lint_profile": "default",
					"checkov_policies_required": [],
					"checkov_policies_suppressed": [],
				},
				"assumptions": [],
				"warnings": [],
			}

		return self.success(
			payload={
				"migration_spec": migration_spec,
				"retrieved_rules": agent_input.payload.get("retrieved_rules", []),
			}
		)
