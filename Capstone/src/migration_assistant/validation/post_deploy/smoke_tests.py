"""Functional smoke-test checks for post-deployment validation."""
from __future__ import annotations

from migration_assistant.graph.state import (
	MappingRecord,
	ResourceType,
	SourceResource,
	TargetResource,
	ValidationResult,
	ValidationStage,
	ValidationStatus,
)


def run_smoke_tests(
	*,
	run_id: str,
	source_resources: list[SourceResource],
	target_resources: list[TargetResource],
	mappings: list[MappingRecord],
) -> list[ValidationResult]:
	"""Run deterministic smoke checks over source-to-target migration outputs.

	These checks are structural surrogates for live smoke tests and are safe in
	local/test environments where invoking cloud APIs is out of scope.
	"""
	return [
		_lambda_invocation_smoke(
			run_id=run_id,
			source_resources=source_resources,
			target_resources=target_resources,
			mappings=mappings,
		),
		_secret_access_smoke(
			run_id=run_id,
			source_resources=source_resources,
			target_resources=target_resources,
			mappings=mappings,
		),
		_network_reachability_smoke(
			run_id=run_id,
			source_resources=source_resources,
			target_resources=target_resources,
			mappings=mappings,
		),
	]


def _lambda_invocation_smoke(
	*,
	run_id: str,
	source_resources: list[SourceResource],
	target_resources: list[TargetResource],
	mappings: list[MappingRecord],
) -> ValidationResult:
	function_sources = [
		item for item in source_resources if item.resource_type == ResourceType.FUNCTION_APP
	]
	if not function_sources:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="smoke-lambda-invocation",
			status=ValidationStatus.WARNING,
			details="No Azure Function App resources found; Lambda smoke check skipped.",
		)

	mapped_logical_ids = {
		mapping.target_logical_id
		for mapping in mappings
		if mapping.target_logical_id
		and mapping.source_resource_id in {resource.resource_id for resource in function_sources}
	}
	lambda_targets = {
		resource.logical_id
		for resource in target_resources
		if resource.aws_resource_type == "AWS::Lambda::Function"
	}
	missing = sorted(mapped_logical_ids - lambda_targets)

	if missing:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="smoke-lambda-invocation",
			status=ValidationStatus.FAIL,
			details=(
				"Lambda smoke check failed: mapped Function targets are missing as "
				f"AWS::Lambda::Function resources ({', '.join(missing[:3])})."
			),
		)

	return ValidationResult(
		stage=ValidationStage.POST_DEPLOY,
		resource_id=run_id,
		check_name="smoke-lambda-invocation",
		status=ValidationStatus.PASS,
		details=(
			f"Lambda smoke check passed for {len(mapped_logical_ids)} mapped function resource(s)."
		),
	)


def _secret_access_smoke(
	*,
	run_id: str,
	source_resources: list[SourceResource],
	target_resources: list[TargetResource],
	mappings: list[MappingRecord],
) -> ValidationResult:
	secret_like_types = {
		ResourceType.KEY_VAULT,
		ResourceType.KEY_VAULT_SECRET,
		ResourceType.KEY_VAULT_KEY,
		ResourceType.KEY_VAULT_CERTIFICATE,
	}
	secret_sources = [
		item for item in source_resources if item.resource_type in secret_like_types
	]
	if not secret_sources:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="smoke-secret-fetch",
			status=ValidationStatus.WARNING,
			details="No Key Vault resources found; secret smoke check skipped.",
		)

	source_secret_ids = {item.resource_id for item in secret_sources}
	mapped_targets = {
		mapping.target_logical_id
		for mapping in mappings
		if mapping.target_logical_id and mapping.source_resource_id in source_secret_ids
	}
	aws_secret_targets = {
		resource.logical_id
		for resource in target_resources
		if resource.aws_resource_type in {"AWS::SecretsManager::Secret", "AWS::KMS::Key"}
	}
	missing = sorted(mapped_targets - aws_secret_targets)

	if missing:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="smoke-secret-fetch",
			status=ValidationStatus.FAIL,
			details=(
				"Secret smoke check failed: mapped secret/key targets are missing "
				f"from generated AWS resources ({', '.join(missing[:3])})."
			),
		)

	return ValidationResult(
		stage=ValidationStage.POST_DEPLOY,
		resource_id=run_id,
		check_name="smoke-secret-fetch",
		status=ValidationStatus.PASS,
		details=(
			f"Secret smoke check passed for {len(mapped_targets)} mapped secret/key resource(s)."
		),
	)


def _network_reachability_smoke(
	*,
	run_id: str,
	source_resources: list[SourceResource],
	target_resources: list[TargetResource],
	mappings: list[MappingRecord],
) -> ValidationResult:
	network_like_types = {
		ResourceType.VNET,
		ResourceType.SUBNET,
		ResourceType.NSG,
		ResourceType.ROUTE_TABLE,
		ResourceType.VNET_PEERING,
		ResourceType.PRIVATE_ENDPOINT,
	}
	network_sources = [
		item for item in source_resources if item.resource_type in network_like_types
	]
	if not network_sources:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="smoke-network-reachability",
			status=ValidationStatus.WARNING,
			details="No VNet resources found; network smoke check skipped.",
		)

	source_network_ids = {item.resource_id for item in network_sources}
	mapped_targets = {
		mapping.target_logical_id
		for mapping in mappings
		if mapping.target_logical_id and mapping.source_resource_id in source_network_ids
	}
	network_target_ids = {
		resource.logical_id
		for resource in target_resources
		if resource.aws_resource_type.startswith("AWS::EC2::")
	}
	missing = sorted(mapped_targets - network_target_ids)

	if missing:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="smoke-network-reachability",
			status=ValidationStatus.FAIL,
			details=(
				"Network smoke check failed: mapped network targets are missing "
				f"from generated AWS resources ({', '.join(missing[:3])})."
			),
		)

	return ValidationResult(
		stage=ValidationStage.POST_DEPLOY,
		resource_id=run_id,
		check_name="smoke-network-reachability",
		status=ValidationStatus.PASS,
		details=(
			f"Network smoke check passed for {len(mapped_targets)} mapped network resource(s)."
		),
	)
