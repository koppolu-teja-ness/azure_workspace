"""Integration test for Bedrock-enabled end-to-end graph behavior."""
from __future__ import annotations

import json

from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.graph.workflow import build_graph


def test_graph_runs_end_to_end_with_mocked_bedrock(monkeypatch, tmp_path) -> None:
	bicep_file = tmp_path / "sample.bicep"
	bicep_file.write_text(
		"""
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv1'
  location: 'eastus'
  properties: {
	tenantId: 't1'
	sku: 'standard'
  }
}
""".strip(),
		encoding="utf-8",
	)

	def _mock_mapping_llm(*, settings, prompt, runtime_client=None):
		_ = settings, runtime_client
		return json.dumps(
			{
				"target_logical_id": "Kv1Secret",
				"mapping_rule_id": "rule-keyvault-secretsmanager",
				"confidence": 0.95,
				"notes": ["Bedrock refinement applied."],
				"unmapped_properties": [],
			}
		)

	def _mock_risk_llm(*, settings, prompt, runtime_client=None):
		_ = settings, runtime_client
		return json.dumps(
			{
				"additional_reasons": [
					"Resource type mapping confidence is strong.",
				]
			}
		)

	def _mock_report_llm(*, settings, prompt, runtime_client=None):
		_ = settings, runtime_client, prompt
		return "Run is healthy. 1 resource mapped. No blockers detected."

	monkeypatch.setattr(
		"migration_assistant.mapping.bedrock_client.invoke_bedrock_text",
		_mock_mapping_llm,
	)
	monkeypatch.setattr(
		"migration_assistant.planning.bedrock_risk_reasoner.invoke_bedrock_text",
		_mock_risk_llm,
	)
	monkeypatch.setattr(
		"migration_assistant.reporting.bedrock_report_writer.invoke_bedrock_text",
		_mock_report_llm,
	)

	app = build_graph()

	initial_state: GraphState = {
		"run_id": "integration-bedrock-run",
		"created_at": "2026-09-25T00:00:00+00:00",
		"source_resources": [],
		"target_resources": [],
		"mappings": [],
		"risk_assessments": [],
		"validation_results": [],
		"llm_traces": [],
		"status": MigrationStatus.DISCOVERED,
		"config": {
			"approval": {
				"auto_approve": True,
				"auto_reviewer": "integration-test",
			},
			"bicep_paths": [str(bicep_file)],
			"llm": {
				"enabled": True,
				"provider": "aws_bedrock",
				"bedrock": {
					"model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
					"region_name": "us-east-1",
					"temperature": 0.7,
					"max_tokens": 512,
				},
			},
		},
	}

	final_state = app.invoke(initial_state)

	assert final_state["status"] == MigrationStatus.VERIFIED
	assert len(final_state["source_resources"]) == 1
	assert len(final_state["mappings"]) == 1
	assert final_state["mappings"][0].confidence == 0.95
	assert final_state["config"]["report_summary"]

	traces = final_state.get("llm_traces", [])
	assert len(traces) == 3
	assert {trace.node for trace in traces} == {"map", "plan_risk", "report"}
	assert {trace.prompt_version for trace in traces} == {
		"mapping_v1",
		"risk_reasoning_v1",
		"report_summary_v1",
	}
