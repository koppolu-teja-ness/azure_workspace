"""Phase 0 CloudFormation generator agent contract implementation."""

from __future__ import annotations

from .interfaces import AbstractAgent, AgentInput, AgentOutput


class CfnGeneratorAgent(AbstractAgent):
	"""Builds CloudFormation template payload from migration spec input."""

	agent_name = "cfn_generator"

	async def run(self, agent_input: AgentInput) -> AgentOutput:
		template = agent_input.payload.get(
			"cfn_template",
			{
				"AWSTemplateFormatVersion": "2010-09-09",
				"Description": "Generated template placeholder from Phase 0 contract",
				"Resources": {},
			},
		)
		return self.success(payload={"cfn_template": template})
