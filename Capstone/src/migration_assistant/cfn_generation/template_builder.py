"""Deterministic CloudFormation resource generation helpers.

These helpers transform mapped Azure SourceResource entries into
TargetResource objects, which the CFN generator agent writes into graph
state["target_resources"].
"""
from __future__ import annotations

from typing import Any

from migration_assistant.graph.state import MappingRecord, SourceResource, TargetResource


def build_target_resources(
	*,
	run_id: str,
	source_resources: list[SourceResource],
	mappings: list[MappingRecord],
	naming_prefix: str = "mig",
) -> list[TargetResource]:
	"""Build deterministic CloudFormation resources from mapping output."""
	source_by_id = {resource.resource_id: resource for resource in source_resources}
	logical_by_source_id = {
		mapping.source_resource_id: mapping.target_logical_id
		for mapping in mappings
		if mapping.target_logical_id
	}

	results: list[TargetResource] = []
	for mapping in mappings:
		logical_id = mapping.target_logical_id
		if not logical_id:
			continue

		source = source_by_id.get(mapping.source_resource_id)
		if source is None:
			continue

		aws_resource_type = _resource_type_from_rule(mapping.mapping_rule_id)
		if aws_resource_type is None:
			aws_resource_type = _infer_aws_type_from_logical_id(logical_id)
		if aws_resource_type is None:
			continue

		depends_on = [
			logical_by_source_id[source_id]
			for source_id in source.depends_on
			if source_id in logical_by_source_id
		]

		properties = _build_resource_properties(
			aws_resource_type=aws_resource_type,
			source=source,
			run_id=run_id,
			naming_prefix=naming_prefix,
			depends_on=depends_on,
		)
		results.append(
			TargetResource(
				logical_id=logical_id,
				aws_resource_type=aws_resource_type,
				properties=properties,
				depends_on=depends_on,
			)
		)

	return results


def build_template(target_resources: list[TargetResource]) -> dict[str, Any]:
	"""Create an in-memory CloudFormation template document."""
	resources: dict[str, Any] = {}
	for resource in target_resources:
		entry: dict[str, Any] = {
			"Type": resource.aws_resource_type,
			"Properties": resource.properties,
		}
		if resource.depends_on:
			entry["DependsOn"] = resource.depends_on
		resources[resource.logical_id] = entry

	return {
		"AWSTemplateFormatVersion": "2010-09-09",
		"Resources": resources,
	}


def _build_resource_properties(
	*,
	aws_resource_type: str,
	source: SourceResource,
	run_id: str,
	naming_prefix: str,
	depends_on: list[str],
) -> dict[str, Any]:
	tags = _build_tag_list(source.tags, run_id)
	source_properties = source.properties
	migrated_name = _prefixed_name(naming_prefix, source.name)

	if aws_resource_type == "AWS::SecretsManager::Secret":
		return {
			"Name": migrated_name,
			"Description": f"Migrated from Azure Key Vault resource {source.name}",
			"Tags": tags,
		}

	if aws_resource_type == "AWS::Lambda::Function":
		return {
			"FunctionName": migrated_name,
			"Runtime": "python3.11",
			"Handler": "index.handler",
			"Role": "arn:aws:iam::123456789012:role/migration-placeholder-lambda-role",
			"Timeout": _extract_lambda_timeout_seconds(source_properties),
			"MemorySize": 256,
			"Environment": {"Variables": {"MIGRATION_RUN_ID": run_id}},
			"Tags": tags,
		}

	if aws_resource_type == "AWS::EC2::VPC":
		return {
			"CidrBlock": _extract_vpc_cidr(source_properties),
			"EnableDnsSupport": True,
			"EnableDnsHostnames": True,
			"Tags": tags,
		}

	if aws_resource_type == "AWS::EC2::Subnet":
		properties: dict[str, Any] = {
			"CidrBlock": _extract_subnet_cidr(source_properties),
			"Tags": tags,
		}
		if depends_on:
			properties["VpcId"] = {"Ref": depends_on[0]}
		return properties

	if aws_resource_type == "AWS::EC2::SecurityGroup":
		properties = {
			"GroupDescription": f"Migrated NSG from Azure resource {source.name}",
			"SecurityGroupIngress": [],
			"SecurityGroupEgress": [],
			"Tags": tags,
		}
		if depends_on:
			properties["VpcId"] = {"Ref": depends_on[0]}
		return properties

	if aws_resource_type == "AWS::EC2::RouteTable":
		properties = {"Tags": tags}
		if depends_on:
			properties["VpcId"] = {"Ref": depends_on[0]}
		return properties

	if aws_resource_type == "AWS::EC2::VPCPeeringConnection":
		properties: dict[str, Any] = {"Tags": tags}
		if depends_on:
			properties["VpcId"] = {"Ref": depends_on[0]}
		if len(depends_on) > 1:
			properties["PeerVpcId"] = {"Ref": depends_on[1]}
		return properties

	if aws_resource_type == "AWS::EC2::VPCEndpoint":
		properties = {
			"VpcEndpointType": "Interface",
			"ServiceName": "com.amazonaws.${AWS::Region}.s3",
			"Tags": tags,
		}
		if depends_on:
			properties["VpcId"] = {"Ref": depends_on[0]}
		return properties

	if aws_resource_type == "AWS::KMS::Key":
		return {
			"Description": f"Migrated key material placeholder for {source.name}",
			"EnableKeyRotation": True,
			"Tags": tags,
		}

	if aws_resource_type == "AWS::CertificateManager::Certificate":
		return {
			"DomainName": f"{source.name}.example.com",
			"ValidationMethod": "DNS",
			"Tags": tags,
		}

	return {"Tags": tags}


def _resource_type_from_rule(mapping_rule_id: str | None) -> str | None:
	if not mapping_rule_id:
		return None

	rule_map = {
		"rule-keyvault-secretsmanager": "AWS::SecretsManager::Secret",
		"rule-keyvaultsecret-secret": "AWS::SecretsManager::Secret",
		"rule-keyvaultkey-kmskey": "AWS::KMS::Key",
		"rule-keyvaultcert-acm": "AWS::CertificateManager::Certificate",
		"rule-functionapp-lambda": "AWS::Lambda::Function",
		"rule-vnet-vpc": "AWS::EC2::VPC",
		"rule-subnet-subnet": "AWS::EC2::Subnet",
		"rule-nsg-securitygroup": "AWS::EC2::SecurityGroup",
		"rule-routetable-routetable": "AWS::EC2::RouteTable",
		"rule-vnetpeering-vpcpeering": "AWS::EC2::VPCPeeringConnection",
		"rule-privateendpoint-privatelink": "AWS::EC2::VPCEndpoint",
	}
	return rule_map.get(mapping_rule_id)


def _infer_aws_type_from_logical_id(logical_id: str) -> str | None:
	suffix_map = {
		"Secret": "AWS::SecretsManager::Secret",
		"Function": "AWS::Lambda::Function",
		"Vpc": "AWS::EC2::VPC",
		"Subnet": "AWS::EC2::Subnet",
		"SecurityGroup": "AWS::EC2::SecurityGroup",
		"RouteTable": "AWS::EC2::RouteTable",
		"PeeringConnection": "AWS::EC2::VPCPeeringConnection",
		"VpcEndpoint": "AWS::EC2::VPCEndpoint",
		"Key": "AWS::KMS::Key",
		"Certificate": "AWS::CertificateManager::Certificate",
	}
	for suffix, aws_type in suffix_map.items():
		if logical_id.endswith(suffix):
			return aws_type
	return None


def _build_tag_list(source_tags: dict[str, str], run_id: str) -> list[dict[str, str]]:
	merged = {
		"MigratedFrom": "azure",
		"MigrationRunId": run_id,
		**source_tags,
	}
	return [{"Key": key, "Value": value} for key, value in sorted(merged.items())]


def _prefixed_name(prefix: str, source_name: str) -> str:
	normalized = source_name.replace("_", "-").replace(" ", "-")
	collapsed = "-".join(part for part in normalized.split("-") if part)
	if not prefix:
		return collapsed.lower()
	return f"{prefix}-{collapsed}".lower()


def _extract_vpc_cidr(source_properties: dict[str, Any]) -> str:
	address_space = source_properties.get("addressSpace", {})
	if isinstance(address_space, dict):
		prefixes = address_space.get("addressPrefixes", [])
		if isinstance(prefixes, list) and prefixes:
			first = prefixes[0]
			if isinstance(first, str):
				return first
	return "10.0.0.0/16"


def _extract_subnet_cidr(source_properties: dict[str, Any]) -> str:
	for key in ("addressPrefix", "cidr", "address_prefix"):
		value = source_properties.get(key)
		if isinstance(value, str) and value:
			return value
	prefixes = source_properties.get("addressPrefixes")
	if isinstance(prefixes, list) and prefixes:
		first = prefixes[0]
		if isinstance(first, str):
			return first
	return "10.0.1.0/24"


def _extract_lambda_timeout_seconds(source_properties: dict[str, Any]) -> int:
	site_config = source_properties.get("siteConfig")
	if isinstance(site_config, dict):
		timeout = site_config.get("functionTimeout")
		if isinstance(timeout, str):
			parts = timeout.split(":")
			if len(parts) == 3 and all(part.isdigit() for part in parts):
				hours, minutes, seconds = (int(part) for part in parts)
				return max(1, hours * 3600 + minutes * 60 + seconds)
		if isinstance(timeout, int):
			return max(1, timeout)
	return 30
