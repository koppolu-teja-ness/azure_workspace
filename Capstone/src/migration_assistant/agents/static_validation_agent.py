"""Phase 0 static validation agent contract implementation."""

from __future__ import annotations

from .interfaces import AbstractAgent, AgentInput, AgentOutput


class StaticValidationAgent(AbstractAgent):
	"""Validates generated CloudFormation using static policy/lint checks."""

	agent_name = "static_validation"

	async def run(self, agent_input: AgentInput) -> AgentOutput:
		return self.success(
			payload={
				"static_validation_results": {
					"cfn_lint": "not_run",
					"checkov": "not_run",
					"status": "contract_only",
				}
			}
		)
