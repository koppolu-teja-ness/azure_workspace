"""CloudFormation deployment orchestration (dry-run only for Phase 1)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from migration_assistant.deployment.boto3_client import Boto3ClientFactory
from migration_assistant.graph.state import TargetResource


@dataclass(frozen=True, slots=True)
class DeploymentPreview:
	stack_name: str
	mode: str
	resource_count: int
	ordered_logical_ids: list[str]
	live_deploy_requested: bool
	live_deploy_supported: bool
	region_name: str | None
	would_call: dict[str, Any]

	def to_dict(self) -> dict[str, Any]:
		return {
			"stack_name": self.stack_name,
			"mode": self.mode,
			"resource_count": self.resource_count,
			"ordered_logical_ids": list(self.ordered_logical_ids),
			"live_deploy_requested": self.live_deploy_requested,
			"live_deploy_supported": self.live_deploy_supported,
			"region_name": self.region_name,
			"would_call": dict(self.would_call),
		}


class CloudFormationDeployer:
	"""Build deployment plans and dry-run metadata.

	Live deployment is intentionally not implemented in Phase 1.
	"""

	def __init__(
		self,
		*,
		client_factory: Boto3ClientFactory,
		live_deploy_enabled: bool = False,
	) -> None:
		self._client_factory = client_factory
		self._live_deploy_enabled = live_deploy_enabled

	def preview_deployment(
		self,
		*,
		run_id: str,
		target_resources: list[TargetResource],
		template_body: str,
		stack_name: str | None = None,
		live_deploy_requested: bool = False,
	) -> dict[str, Any]:
		ordered = order_resources_for_deployment(target_resources)
		ordered_ids = [resource.logical_id for resource in ordered]
		resolved_stack_name = stack_name or build_stack_name(run_id)
		change_set_name = f"{resolved_stack_name}-preview"

		preview = DeploymentPreview(
			stack_name=resolved_stack_name,
			mode="dry_run",
			resource_count=len(target_resources),
			ordered_logical_ids=ordered_ids,
			live_deploy_requested=live_deploy_requested,
			live_deploy_supported=self._live_deploy_enabled,
			region_name=self._client_factory.region_name,
			would_call={
				"service": "cloudformation",
				"operation": "create_change_set",
				"parameters": {
					"StackName": resolved_stack_name,
					"ChangeSetName": change_set_name,
					"Capabilities": ["CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"],
					"TemplateBodySha256": hashlib.sha256(
						template_body.encode("utf-8")
					).hexdigest(),
				},
			},
		)
		return preview.to_dict()

	def deploy_stack(
		self,
		*,
		run_id: str,
		template_body: str,
		stack_name: str | None = None,
		execute_change_set: bool = True,
	) -> dict[str, Any]:
		"""Create (and optionally execute) a CloudFormation change set."""
		if not self._live_deploy_enabled:
			raise RuntimeError("Live deployment is disabled by configuration.")

		resolved_stack_name = stack_name or build_stack_name(run_id)
		change_set_name = f"{resolved_stack_name}-exec"
		change_set_type = self._detect_change_set_type(resolved_stack_name)

		client = self._client_factory.cloudformation_client()
		response = client.create_change_set(
			StackName=resolved_stack_name,
			ChangeSetName=change_set_name,
			ChangeSetType=change_set_type,
			TemplateBody=template_body,
			Capabilities=["CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"],
		)
		change_set_id = response.get("Id")

		result: dict[str, Any] = {
			"mode": "live",
			"stack_name": resolved_stack_name,
			"change_set_name": change_set_name,
			"change_set_type": change_set_type,
			"change_set_id": change_set_id,
			"executed": False,
			"region_name": self._client_factory.region_name,
		}

		if execute_change_set:
			waiter = client.get_waiter("change_set_create_complete")
			waiter.wait(StackName=resolved_stack_name, ChangeSetName=change_set_name)
			client.execute_change_set(
				StackName=resolved_stack_name,
				ChangeSetName=change_set_name,
			)
			result["executed"] = True

		return result

	def _detect_change_set_type(self, stack_name: str) -> str:
		client = self._client_factory.cloudformation_client()
		try:
			client.describe_stacks(StackName=stack_name)
		except Exception:
			return "CREATE"
		return "UPDATE"


def order_resources_for_deployment(
	target_resources: list[TargetResource],
) -> list[TargetResource]:
	"""Topologically sort resources by DependsOn relationships."""
	by_logical_id = {resource.logical_id: resource for resource in target_resources}

	dependency_edges: dict[str, set[str]] = {
		resource.logical_id: set() for resource in target_resources
	}
	in_degree = {resource.logical_id: 0 for resource in target_resources}

	for resource in target_resources:
		for dependency in resource.depends_on:
			if dependency not in by_logical_id:
				continue
			if resource.logical_id in dependency_edges[dependency]:
				continue
			dependency_edges[dependency].add(resource.logical_id)
			in_degree[resource.logical_id] += 1

	ready = sorted(logical_id for logical_id, degree in in_degree.items() if degree == 0)
	ordered_ids: list[str] = []

	while ready:
		current = ready.pop(0)
		ordered_ids.append(current)
		for dependent in sorted(dependency_edges[current]):
			in_degree[dependent] -= 1
			if in_degree[dependent] == 0:
				ready.append(dependent)
		ready.sort()

	if len(ordered_ids) != len(target_resources):
		# Cycle or unresolved graph: preserve deterministic ordering for leftovers.
		leftovers = sorted(set(by_logical_id).difference(ordered_ids))
		ordered_ids.extend(leftovers)

	return [by_logical_id[logical_id] for logical_id in ordered_ids]


def build_stack_name(run_id: str, *, prefix: str = "migration") -> str:
	"""Create a CloudFormation-safe stack name from run_id."""
	normalized_prefix = _slugify(prefix) or "migration"
	normalized_run_id = _slugify(run_id)
	base = normalized_prefix if not normalized_run_id else f"{normalized_prefix}-{normalized_run_id}"

	if not base[0].isalpha():
		base = f"m-{base}"

	return base[:128]


def _slugify(value: str) -> str:
	lowered = value.lower()
	replaced = re.sub(r"[^a-z0-9-]", "-", lowered)
	collapsed = re.sub(r"-+", "-", replaced)
	return collapsed.strip("-")
