"""Structural equivalence checks between source and generated resources."""
from __future__ import annotations

from typing import Any

from migration_assistant.graph.state import (
	MappingRecord,
	SourceResource,
	TargetResource,
	ValidationResult,
	ValidationStage,
	ValidationStatus,
)
from migration_assistant.mapping.equivalence_models import (
	PropertyMappingRule,
	load_property_rules,
)


def compare_resource_counts(
	*,
	run_id: str,
	source_resources: list[SourceResource],
	target_resources: list[TargetResource],
	mappings: list[MappingRecord],
) -> ValidationResult:
	"""Validate that generated target resources match mapped source resources."""
	expected_targets = sum(1 for mapping in mappings if mapping.target_logical_id)
	actual_targets = len(target_resources)

	if expected_targets == actual_targets:
		status = ValidationStatus.PASS
		details = (
			"Generated target resource count matches mapped resource count "
			f"({actual_targets})."
		)
	else:
		status = ValidationStatus.FAIL
		details = (
			"Target resource count mismatch: "
			f"expected {expected_targets} from mappings, got {actual_targets}. "
			f"Source resources: {len(source_resources)}."
		)

	return ValidationResult(
		stage=ValidationStage.POST_DEPLOY,
		resource_id=run_id,
		check_name="resource-count-equivalence",
		status=status,
		details=details,
	)


def compare_property_parity(
	*,
	run_id: str,
	source_resources: list[SourceResource],
	target_resources: list[TargetResource],
	mappings: list[MappingRecord],
) -> list[ValidationResult]:
	"""Check parity for mapped properties using knowledge-base property rules."""
	by_source_id = {resource.resource_id: resource for resource in source_resources}
	by_target_id = {resource.logical_id: resource for resource in target_resources}
	property_rules = load_property_rules()

	results: list[ValidationResult] = []
	for mapping in mappings:
		if not mapping.target_logical_id:
			results.append(
				ValidationResult(
					stage=ValidationStage.POST_DEPLOY,
					resource_id=mapping.source_resource_id,
					check_name="property-parity",
					status=ValidationStatus.FAIL,
					details="No target logical ID available for parity checks.",
				)
			)
			continue

		source = by_source_id.get(mapping.source_resource_id)
		target = by_target_id.get(mapping.target_logical_id)
		if source is None or target is None:
			results.append(
				ValidationResult(
					stage=ValidationStage.POST_DEPLOY,
					resource_id=mapping.source_resource_id,
					check_name="property-parity",
					status=ValidationStatus.FAIL,
					details=(
						"Mapped source/target resource not found in run state "
						"for parity checks."
					),
				)
			)
			continue

		rules = property_rules.get(source.resource_type, [])
		if not rules:
			results.append(
				ValidationResult(
					stage=ValidationStage.POST_DEPLOY,
					resource_id=source.resource_id,
					check_name="property-parity",
					status=ValidationStatus.WARNING,
					details=(
						"No property-mapping rules found for resource type "
						f"{source.resource_type.value}."
					),
				)
			)
			continue

		results.append(
			_compare_resource_property_rules(
				run_id=run_id,
				source=source,
				target=target,
				rules=rules,
			)
		)

	return results


def _compare_resource_property_rules(
	*,
	run_id: str,
	source: SourceResource,
	target: TargetResource,
	rules: list[PropertyMappingRule],
) -> ValidationResult:
	checked = 0
	mismatches: list[str] = []

	for rule in rules:
		source_value = _extract_property(source.properties, rule.azure_property)
		if source_value is None:
			continue

		checked += 1
		target_value = _extract_property(target.properties, rule.aws_property)
		if target_value is None:
			mismatches.append(
				f"Missing target property '{rule.aws_property}' for source '{rule.azure_property}'."
			)
			continue

		if _normalize(source_value) != _normalize(target_value):
			mismatches.append(
				"Value mismatch "
				f"{rule.azure_property}={source_value!r} vs {rule.aws_property}={target_value!r}."
			)

	if checked == 0:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=source.resource_id,
			check_name="property-parity",
			status=ValidationStatus.WARNING,
			details=(
				"No comparable source properties were present for known parity rules "
				f"on run {run_id}."
			),
		)

	if mismatches:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=source.resource_id,
			check_name="property-parity",
			status=ValidationStatus.WARNING,
			details=(
				f"Checked {checked} rule(s); {len(mismatches)} mismatch(es): "
				+ "; ".join(mismatches[:3])
			),
		)

	return ValidationResult(
		stage=ValidationStage.POST_DEPLOY,
		resource_id=source.resource_id,
		check_name="property-parity",
		status=ValidationStatus.PASS,
		details=f"Checked {checked} rule(s); all comparable properties matched.",
	)


def _extract_property(data: dict[str, Any], dotted_path: str) -> Any:
	current: Any = data
	for segment in dotted_path.split("."):
		if not isinstance(current, dict):
			return None
		if segment not in current:
			return None
		current = current[segment]
	return current


def _normalize(value: Any) -> Any:
	if isinstance(value, str):
		return value.strip()
	return value
