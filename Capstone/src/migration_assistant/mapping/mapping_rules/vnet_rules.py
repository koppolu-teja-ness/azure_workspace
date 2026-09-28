"""VNet-specific mapping heuristics."""

from __future__ import annotations

from migration_assistant.graph.state import ResourceType, SourceResource


def apply(
    resource: SourceResource,
    *,
    confidence: float,
    notes: tuple[str, ...],
) -> tuple[float, tuple[str, ...]]:
    updated = confidence
    appended: list[str] = []
    properties = resource.properties

    if resource.resource_type == ResourceType.VNET:
        address_space = properties.get("addressSpace")
        if not isinstance(address_space, dict) or not address_space.get("addressPrefixes"):
            updated -= 0.05
            appended.append(
                "VNet address prefixes are missing; default CIDR assumptions may be unsafe."
            )

    if resource.resource_type == ResourceType.SUBNET:
        if not any(key in properties for key in ("addressPrefix", "addressPrefixes", "cidr")):
            updated -= 0.05
            appended.append("Subnet CIDR data is missing; manual validation required.")

    if resource.resource_type in {ResourceType.NSG, ResourceType.ROUTE_TABLE}:
        appended.append("Review rule semantics because Azure and AWS network controls differ.")

    if resource.resource_type == ResourceType.VNET_PEERING:
        updated -= 0.03
        appended.append(
            "Peering route propagation and DNS resolution behavior should be validated."
        )

    if resource.resource_type == ResourceType.PRIVATE_ENDPOINT:
        updated -= 0.04
        appended.append(
            "Private endpoint service mapping may require endpoint type-specific decisions."
        )

    updated = max(0.0, min(1.0, updated))
    if not appended:
        return updated, notes
    return updated, tuple(dict.fromkeys([*notes, *appended]))
