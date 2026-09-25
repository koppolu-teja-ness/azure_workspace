from migration_assistant.agents import cfn_generator_agent
from migration_assistant.cfn_generation.template_builder import build_template
from migration_assistant.graph.state import (
	GraphState,
	MappingRecord,
	MigrationStatus,
	ResourceType,
	SourceResource,
)


def test_cfn_generator_builds_keyvault_secret_lambda_and_vpc() -> None:
	source_resources = [
		SourceResource(
			resource_id="/r/kv1",
			resource_type=ResourceType.KEY_VAULT,
			name="kv1",
			api_version="2023-02-01",
			location="eastus",
			properties={"tenantId": "x"},
			tags={"Environment": "dev"},
		),
		SourceResource(
			resource_id="/r/fn1",
			resource_type=ResourceType.FUNCTION_APP,
			name="orders-func",
			api_version="2023-01-01",
			location="eastus",
			properties={"siteConfig": {"functionTimeout": "00:02:00"}},
			tags={"Environment": "dev"},
		),
		SourceResource(
			resource_id="/r/vpc1",
			resource_type=ResourceType.VNET,
			name="core-vnet",
			api_version="2023-09-01",
			location="eastus",
			properties={"addressSpace": {"addressPrefixes": ["10.10.0.0/16"]}},
			tags={"Environment": "dev"},
		),
	]
	mappings = [
		MappingRecord(
			source_resource_id="/r/kv1",
			target_logical_id="Kv1Secret",
			mapping_rule_id="rule-keyvault-secretsmanager",
			confidence=0.9,
		),
		MappingRecord(
			source_resource_id="/r/fn1",
			target_logical_id="OrdersFuncFunction",
			mapping_rule_id="rule-functionapp-lambda",
			confidence=0.88,
		),
		MappingRecord(
			source_resource_id="/r/vpc1",
			target_logical_id="CoreVpc",
			mapping_rule_id="rule-vnet-vpc",
			confidence=0.92,
		),
	]
	state: GraphState = {
		"run_id": "run-abc",
		"created_at": "2026-09-25T00:00:00+00:00",
		"source_resources": source_resources,
		"mappings": mappings,
		"status": MigrationStatus.MAPPED,
		"config": {"naming": {"prefix": "mig"}},
	}

	update = cfn_generator_agent.run(state)

	assert update["status"] == MigrationStatus.GENERATED
	target_resources = update["target_resources"]
	assert len(target_resources) == 3

	by_type = {resource.aws_resource_type: resource for resource in target_resources}
	assert "AWS::SecretsManager::Secret" in by_type
	assert "AWS::Lambda::Function" in by_type
	assert "AWS::EC2::VPC" in by_type

	secret = by_type["AWS::SecretsManager::Secret"]
	assert secret.properties["Name"] == "mig-kv1"

	function = by_type["AWS::Lambda::Function"]
	assert function.properties["Timeout"] == 120
	assert function.properties["FunctionName"] == "mig-orders-func"

	vpc = by_type["AWS::EC2::VPC"]
	assert vpc.properties["CidrBlock"] == "10.10.0.0/16"


def test_cfn_generator_wires_depends_on_for_subnet() -> None:
	source_resources = [
		SourceResource(
			resource_id="/r/vpc1",
			resource_type=ResourceType.VNET,
			name="core-vnet",
			api_version="2023-09-01",
			location="eastus",
			properties={"addressSpace": {"addressPrefixes": ["10.20.0.0/16"]}},
		),
		SourceResource(
			resource_id="/r/subnet1",
			resource_type=ResourceType.SUBNET,
			name="app-subnet",
			api_version="2023-09-01",
			location="eastus",
			properties={"addressPrefix": "10.20.1.0/24"},
			depends_on=["/r/vpc1"],
		),
	]
	mappings = [
		MappingRecord(
			source_resource_id="/r/vpc1",
			target_logical_id="CoreVpc",
			mapping_rule_id="rule-vnet-vpc",
			confidence=0.92,
		),
		MappingRecord(
			source_resource_id="/r/subnet1",
			target_logical_id="AppSubnet",
			mapping_rule_id="rule-subnet-subnet",
			confidence=0.92,
		),
	]
	state: GraphState = {
		"run_id": "run-deps",
		"created_at": "2026-09-25T00:00:00+00:00",
		"source_resources": source_resources,
		"mappings": mappings,
		"status": MigrationStatus.MAPPED,
		"config": {},
	}

	update = cfn_generator_agent.run(state)
	template = build_template(update["target_resources"])

	subnet = next(
		resource
		for resource in update["target_resources"]
		if resource.aws_resource_type == "AWS::EC2::Subnet"
	)
	assert subnet.depends_on == ["CoreVpc"]
	assert subnet.properties["VpcId"] == {"Ref": "CoreVpc"}
	assert template["Resources"]["AppSubnet"]["DependsOn"] == ["CoreVpc"]


def test_cfn_generator_skips_unmapped_entries() -> None:
	source_resources = [
		SourceResource(
			resource_id="/r/kv1",
			resource_type=ResourceType.KEY_VAULT,
			name="kv1",
			api_version="2023-02-01",
			location="eastus",
		)
	]
	mappings = [
		MappingRecord(
			source_resource_id="/r/kv1",
			target_logical_id=None,
			mapping_rule_id=None,
			confidence=0.0,
		)
	]
	state: GraphState = {
		"run_id": "run-none",
		"created_at": "2026-09-25T00:00:00+00:00",
		"source_resources": source_resources,
		"mappings": mappings,
		"status": MigrationStatus.MAPPED,
		"config": {},
	}

	update = cfn_generator_agent.run(state)
	assert update["target_resources"] == []
