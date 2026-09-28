from migration_assistant.graph.state import ResourceType, SourceResource
from migration_assistant.mapping.rag_retriever import RuleBasedMappingRetriever


def test_keyvault_domain_rule_adds_acl_note_and_adjusts_confidence() -> None:
	retriever = RuleBasedMappingRetriever()
	resource = SourceResource(
		resource_id="/r/kv-acl",
		resource_type=ResourceType.KEY_VAULT,
		name="kv-acl",
		api_version="2023-07-01",
		location="eastus",
		properties={"networkAcls": {"defaultAction": "Deny"}},
	)

	mapping = retriever.map_resource(resource)
	assert mapping.confidence < 0.9
	assert any("network ACL" in note for note in mapping.notes)


def test_function_domain_rule_adds_runtime_notes() -> None:
	retriever = RuleBasedMappingRetriever()
	resource = SourceResource(
		resource_id="/r/func-1",
		resource_type=ResourceType.FUNCTION_APP,
		name="func-1",
		api_version="2023-01-01",
		location="eastus",
		properties={
			"kind": "functionapp",
			"httpsOnly": False,
			"siteConfig": {"alwaysOn": True, "functionTimeout": "00:10:00"},
		},
	)

	mapping = retriever.map_resource(resource)
	assert mapping.confidence < 0.88
	assert any("cold-start" in note for note in mapping.notes)


def test_vnet_domain_rule_flags_missing_cidr_data() -> None:
	retriever = RuleBasedMappingRetriever()
	resource = SourceResource(
		resource_id="/r/subnet-1",
		resource_type=ResourceType.SUBNET,
		name="subnet-1",
		api_version="2023-05-01",
		location="eastus",
		properties={},
	)

	mapping = retriever.map_resource(resource)
	assert mapping.confidence < 0.92
	assert any("CIDR" in note for note in mapping.notes)
