"""Optional Azure SDK discovery helpers.

These APIs are intentionally best-effort and should never block local
Bicep-driven execution.
"""
from __future__ import annotations

from typing import Any

try:
	from azure.identity import DefaultAzureCredential
	from azure.mgmt.resource import ResourceManagementClient
except Exception:  # pragma: no cover - optional dependency/runtime auth
	DefaultAzureCredential = None
	ResourceManagementClient = None


def discover_resource_group_resources(
	*,
	subscription_id: str,
	resource_group: str,
) -> list[dict[str, Any]]:
	"""List resources in one Azure resource group.

	Returns an empty list when Azure SDK dependencies are unavailable.
	"""
	if not subscription_id.strip() or not resource_group.strip():
		return []
	if DefaultAzureCredential is None or ResourceManagementClient is None:
		return []

	credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
	client = ResourceManagementClient(credential, subscription_id)
	resources = client.resources.list_by_resource_group(resource_group)

	items: list[dict[str, Any]] = []
	for item in resources:
		raw = item.as_dict() if hasattr(item, "as_dict") else {}
		if isinstance(raw, dict):
			items.append(raw)
	return items

