"""Security posture diff checks for post-deployment validation."""
from __future__ import annotations

from typing import Any

from migration_assistant.graph.state import (
	TargetResource,
	ValidationResult,
	ValidationStage,
	ValidationStatus,
)


def run_security_posture_diff(
	*,
	run_id: str,
	target_resources: list[TargetResource],
) -> list[ValidationResult]:
	return [
		_check_public_exposure(run_id=run_id, target_resources=target_resources),
		_check_iam_over_broadening(run_id=run_id, target_resources=target_resources),
	]


def _check_public_exposure(*, run_id: str, target_resources: list[TargetResource]) -> ValidationResult:
	violations: list[str] = []

	for resource in target_resources:
		props = resource.properties
		if not isinstance(props, dict):
			continue

		if props.get("PubliclyAccessible") is True:
			violations.append(f"{resource.logical_id}: PubliclyAccessible=true")

		if props.get("AssociatePublicIpAddress") is True:
			violations.append(f"{resource.logical_id}: AssociatePublicIpAddress=true")

		for rule_block in ("SecurityGroupIngress", "Ingress"):
			rules = props.get(rule_block)
			if not isinstance(rules, list):
				continue
			for rule in rules:
				if not isinstance(rule, dict):
					continue
				if _is_world_open(rule):
					violations.append(f"{resource.logical_id}: {rule_block} open to 0.0.0.0/0")

	if violations:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="security-public-exposure-diff",
			status=ValidationStatus.FAIL,
			details=(
				"Public exposure risk detected in generated target resources: "
				+ "; ".join(violations[:3])
			),
		)

	return ValidationResult(
		stage=ValidationStage.POST_DEPLOY,
		resource_id=run_id,
		check_name="security-public-exposure-diff",
		status=ValidationStatus.PASS,
		details="No new public exposure indicators detected in target resources.",
	)


def _check_iam_over_broadening(*, run_id: str, target_resources: list[TargetResource]) -> ValidationResult:
	violations: list[str] = []

	for resource in target_resources:
		if resource.aws_resource_type not in {"AWS::IAM::Policy", "AWS::IAM::Role"}:
			continue
		props = resource.properties
		if not isinstance(props, dict):
			continue

		policy_doc = props.get("PolicyDocument")
		if resource.aws_resource_type == "AWS::IAM::Role" and not isinstance(policy_doc, dict):
			policies = props.get("Policies")
			if isinstance(policies, list):
				for policy in policies:
					if isinstance(policy, dict):
						_collect_policy_violations(
							policy.get("PolicyDocument"),
							logical_id=resource.logical_id,
							violations=violations,
						)
			continue

		_collect_policy_violations(policy_doc, logical_id=resource.logical_id, violations=violations)

	if violations:
		return ValidationResult(
			stage=ValidationStage.POST_DEPLOY,
			resource_id=run_id,
			check_name="security-iam-overbroadening-diff",
			status=ValidationStatus.FAIL,
			details=(
				"Potential IAM over-broadening detected: " + "; ".join(violations[:3])
			),
		)

	return ValidationResult(
		stage=ValidationStage.POST_DEPLOY,
		resource_id=run_id,
		check_name="security-iam-overbroadening-diff",
		status=ValidationStatus.PASS,
		details="No over-broad IAM actions/resources detected in generated policies.",
	)


def _collect_policy_violations(
	policy_doc: Any,
	*,
	logical_id: str,
	violations: list[str],
) -> None:
	if not isinstance(policy_doc, dict):
		return
	statements = policy_doc.get("Statement")
	if isinstance(statements, dict):
		statements = [statements]
	if not isinstance(statements, list):
		return

	for statement in statements:
		if not isinstance(statement, dict):
			continue
		if _is_wildcard(statement.get("Action")) or _is_wildcard(statement.get("NotAction")):
			violations.append(f"{logical_id}: wildcard action")
		if _is_wildcard(statement.get("Resource")) or _is_wildcard(statement.get("NotResource")):
			violations.append(f"{logical_id}: wildcard resource")


def _is_world_open(rule: dict[str, Any]) -> bool:
	for key in ("CidrIp", "CidrIpv6", "SourceIp"):
		value = rule.get(key)
		if value in {"0.0.0.0/0", "::/0"}:
			return True
	return False


def _is_wildcard(value: Any) -> bool:
	if isinstance(value, str):
		return value.strip() == "*"
	if isinstance(value, list):
		for item in value:
			if isinstance(item, str) and item.strip() == "*":
				return True
	return False
