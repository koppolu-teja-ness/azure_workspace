import json

from migration_assistant.agents import mapping_agent
from migration_assistant.graph.state import (
	GraphState,
	MigrationStatus,
	ResourceType,
	SourceResource,
)
from migration_assistant.mapping.rag_retriever import RuleBasedMappingRetriever, VectorMatch


def test_mapping_agent_produces_mapping_for_supported_resources() -> None:
	state: GraphState = {
		"run_id": "run-1",
		"created_at": "2026-09-25T00:00:00+00:00",
		"source_resources": [
			SourceResource(
				resource_id="/r/kv1",
				resource_type=ResourceType.KEY_VAULT,
				name="kv1",
				bicep_symbolic_name="keyVault",
				api_version="2023-02-01",
				location="eastus",
				properties={"tenantId": "__present__", "sku": "__present__"},
			)
		],
		"status": MigrationStatus.DISCOVERED,
	}

	update = mapping_agent.run(state)

	assert len(update["mappings"]) == 1
	mapping = update["mappings"][0]
	assert mapping.mapping_rule_id == "rule-keyvault-secretsmanager"
	assert mapping.target_logical_id is not None
	assert mapping.confidence >= 0.85
	assert mapping.unmapped_properties == []


def test_mapping_retriever_reports_unmapped_properties(tmp_path) -> None:
	mapping_json = {
		"version": "1.0",
		"mappings": [
			{
				"azure_resource_type": "Microsoft.Web/sites",
				"aws_resource_type": "AWS::Lambda::Function",
				"mapping_rule_id": "rule-functionapp-lambda",
				"confidence": 0.88,
				"notes": [],
			}
		],
	}
	resource_type_file = tmp_path / "resource_type_mappings.json"
	resource_type_file.write_text(json.dumps(mapping_json), encoding="utf-8")

	property_mappings_dir = tmp_path / "property_mappings"
	property_mappings_dir.mkdir(parents=True, exist_ok=True)
	property_file = property_mappings_dir / "function_app.properties.json"
	property_file.write_text(
		json.dumps(
			{
				"azure_resource_type": "Microsoft.Web/sites",
				"property_mappings": [
					{
						"azure_property": "httpsOnly",
						"aws_property": "FunctionUrlConfig.AuthType"
					}
				],
			}
		),
		encoding="utf-8",
	)

	retriever = RuleBasedMappingRetriever(
		mapping_file_path=str(resource_type_file),
		property_mappings_dir=str(property_mappings_dir),
	)
	resource = SourceResource(
		resource_id="/r/func-1",
		resource_type=ResourceType.FUNCTION_APP,
		name="func-1",
		api_version="2023-01-01",
		location="eastus",
		properties={"httpsOnly": "__present__", "alwaysOn": "__present__"},
	)

	mapping = retriever.map_resource(resource)
	assert mapping.unmapped_properties == ["alwaysOn"]
	assert any("unmapped properties" in note for note in mapping.notes)


def test_mapping_retriever_loads_rules_from_json_file(tmp_path) -> None:
	mapping_json = {
		"version": "1.0",
		"mappings": [
			{
				"azure_resource_type": "Microsoft.KeyVault/vaults",
				"aws_resource_type": "AWS::SecretsManager::Secret",
				"mapping_rule_id": "rule-from-json",
				"confidence": 0.99,
				"notes": ["json-driven"],
			}
		],
	}
	file_path = tmp_path / "resource_type_mappings.json"
	file_path.write_text(json.dumps(mapping_json), encoding="utf-8")

	retriever = RuleBasedMappingRetriever(mapping_file_path=str(file_path))
	resource = SourceResource(
		resource_id="/r/kv-json",
		resource_type=ResourceType.KEY_VAULT,
		name="kv-json",
		api_version="2023-02-01",
		location="eastus",
	)

	mapping = retriever.map_resource(resource)
	assert mapping.mapping_rule_id == "rule-from-json"
	assert mapping.confidence == 0.99
	assert "json-driven" in mapping.notes


def test_mapping_retriever_uses_vector_match_when_available(monkeypatch) -> None:
	retriever = RuleBasedMappingRetriever(
		database_url="postgresql://unused",
		max_vector_distance=0.5,
	)

	resource = SourceResource(
		resource_id="/r/kv-vector",
		resource_type=ResourceType.KEY_VAULT,
		name="kv-vector",
		api_version="2023-02-01",
		location="eastus",
	)

	monkeypatch.setattr(
		retriever,
		"_embed_text",
		lambda text: [0.1, 0.2, 0.3],
	)

	def _query(*, embedding, azure_resource_type, top_k):
		_ = embedding, top_k
		if azure_resource_type == ResourceType.KEY_VAULT.value:
			return [
				VectorMatch(
					rule_id="kb-123",
					aws_resource_type="AWS::KMS::Key",
					confidence=0.96,
					distance=0.04,
					notes=("vector hit",),
				)
			]
		return []

	monkeypatch.setattr(retriever, "_query_vector_matches", _query)

	mapping = retriever.map_resource(resource)
	assert mapping.mapping_rule_id == "kb-123"
	assert mapping.confidence == 0.96
	assert mapping.target_logical_id is not None
	assert any("Hybrid retrieval" in note for note in mapping.notes)


def test_mapping_retriever_falls_back_when_vector_distance_too_high(monkeypatch) -> None:
	retriever = RuleBasedMappingRetriever(
		database_url="postgresql://unused",
		max_vector_distance=0.2,
	)

	resource = SourceResource(
		resource_id="/r/kv-fallback",
		resource_type=ResourceType.KEY_VAULT,
		name="kv-fallback",
		api_version="2023-02-01",
		location="eastus",
	)

	monkeypatch.setattr(retriever, "_embed_text", lambda text: [0.1, 0.2, 0.3])

	def _query(*, embedding, azure_resource_type, top_k):
		_ = embedding, azure_resource_type, top_k
		return [
			VectorMatch(
				rule_id="kb-too-far",
				aws_resource_type="AWS::KMS::Key",
				confidence=0.85,
				distance=0.75,
				notes=("too far",),
			)
		]

	monkeypatch.setattr(retriever, "_query_vector_matches", _query)

	mapping = retriever.map_resource(resource)
	assert mapping.mapping_rule_id == "rule-keyvault-secretsmanager"
	assert mapping.confidence == 0.9
