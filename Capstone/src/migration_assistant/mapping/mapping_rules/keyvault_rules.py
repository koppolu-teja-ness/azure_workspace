"""Key Vault-specific mapping heuristics."""

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

    if resource.resource_type == ResourceType.KEY_VAULT:
        network_acls = properties.get("networkAcls")
        if isinstance(network_acls, dict) and network_acls:
            updated -= 0.05
            appended.append(
                "Key Vault network ACL behavior differs from Secrets Manager resource policies."
            )

        if properties.get("enableRbacAuthorization") is True:
            updated -= 0.03
            appended.append(
                "RBAC-backed vault authorization requires IAM policy translation review."
            )

    if resource.resource_type == ResourceType.KEY_VAULT_KEY:
        appended.append(
            "Key material is not exportable as-is; rotate or import into AWS KMS as needed."
        )

    if resource.resource_type == ResourceType.KEY_VAULT_CERTIFICATE:
        updated -= 0.04
        appended.append(
            "Certificate issuance and validation flows may need ACM-specific DNS/email setup."
        )

    updated = max(0.0, min(1.0, updated))
    if not appended:
        return updated, notes
    return updated, tuple(dict.fromkeys([*notes, *appended]))
