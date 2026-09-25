"""Deterministic schema checks for generated CloudFormation templates."""
from __future__ import annotations

from typing import Any

from migration_assistant.graph.state import (
	ValidationResult,
	ValidationStage,
	ValidationStatus,
)


def validate_template_schema(
	template: dict[str, Any],
	*,
	run_id: str,
) -> list[ValidationResult]:
	"""Run basic shape checks before external validators execute."""
	findings: list[ValidationResult] = []

	template_version = template.get("AWSTemplateFormatVersion")
	if not isinstance(template_version, str):
		findings.append(
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="schema-validator",
				status=ValidationStatus.WARNING,
				details="Template is missing AWSTemplateFormatVersion.",
			)
		)

	resources = template.get("Resources")
	if not isinstance(resources, dict):
		findings.append(
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="schema-validator",
				status=ValidationStatus.FAIL,
				details="Template must include a Resources object.",
			)
		)
		return findings

	if not resources:
		findings.append(
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="schema-validator",
				status=ValidationStatus.WARNING,
				details="Template has an empty Resources object.",
			)
		)

	for logical_id, resource in resources.items():
		resource_id = str(logical_id)
		if not isinstance(resource, dict):
			findings.append(
				ValidationResult(
					stage=ValidationStage.STATIC,
					resource_id=resource_id,
					check_name="schema-validator",
					status=ValidationStatus.FAIL,
					details="Resource entry must be an object.",
				)
			)
			continue

		resource_type = resource.get("Type")
		if not isinstance(resource_type, str) or not resource_type.strip():
			findings.append(
				ValidationResult(
					stage=ValidationStage.STATIC,
					resource_id=resource_id,
					check_name="schema-validator",
					status=ValidationStatus.FAIL,
					details="Resource is missing a valid Type field.",
				)
			)

		properties = resource.get("Properties")
		if properties is not None and not isinstance(properties, dict):
			findings.append(
				ValidationResult(
					stage=ValidationStage.STATIC,
					resource_id=resource_id,
					check_name="schema-validator",
					status=ValidationStatus.FAIL,
					details="Properties must be an object when provided.",
				)
			)

		depends_on = resource.get("DependsOn")
		if depends_on is not None:
			if isinstance(depends_on, str):
				continue
			if isinstance(depends_on, list) and all(
				isinstance(value, str) for value in depends_on
			):
				continue
			findings.append(
				ValidationResult(
					stage=ValidationStage.STATIC,
					resource_id=resource_id,
					check_name="schema-validator",
					status=ValidationStatus.FAIL,
					details="DependsOn must be a string or list of strings.",
				)
			)

	if findings:
		return findings

	return [
		ValidationResult(
			stage=ValidationStage.STATIC,
			resource_id=run_id,
			check_name="schema-validator",
			status=ValidationStatus.PASS,
			details="Template schema checks passed.",
		)
	]
