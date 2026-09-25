from pathlib import Path

from migration_assistant.bicep_parser.ast_parser import parse_bicep_file
from migration_assistant.bicep_parser.resource_graph import to_source_resources
from migration_assistant.graph.state import ResourceType


def test_parse_sample_bicep_files_extracts_resource_metadata() -> None:
	fixtures_dir = Path("tests/fixtures/sample_bicep")
	keyvault_resources = parse_bicep_file(str(fixtures_dir / "keyvault.bicep"))
	function_resources = parse_bicep_file(str(fixtures_dir / "function_app.bicep"))
	vnet_resources = parse_bicep_file(str(fixtures_dir / "vnet.bicep"))

	assert len(keyvault_resources) == 1
	assert len(function_resources) == 1
	assert len(vnet_resources) == 1

	assert keyvault_resources[0].resource_type == "Microsoft.KeyVault/vaults"
	assert function_resources[0].resource_type == "Microsoft.Web/sites"
	assert vnet_resources[0].resource_type == "Microsoft.Network/virtualNetworks"
	assert "tenantId" in keyvault_resources[0].properties
	assert "httpsOnly" in function_resources[0].properties
	assert "addressSpace" in vnet_resources[0].properties


def test_to_source_resources_converts_supported_resource_types() -> None:
	fixtures_dir = Path("tests/fixtures/sample_bicep")
	parsed = parse_bicep_file(str(fixtures_dir / "keyvault.bicep"))

	result = to_source_resources(parsed, run_id="unit-test-run")

	assert len(result) == 1
	assert result[0].resource_type == ResourceType.KEY_VAULT
	assert result[0].name == "sample-kv"
	assert result[0].resource_id.endswith("/Microsoft.KeyVault/vaults/sample-kv")
