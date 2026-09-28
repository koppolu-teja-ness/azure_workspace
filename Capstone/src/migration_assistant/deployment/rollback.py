"""Rollback helpers for failed CloudFormation live deployments."""

from __future__ import annotations

from typing import Any


def cleanup_failed_deployment(
    *,
    cloudformation_client: Any,
    stack_name: str,
    change_set_name: str,
    change_set_type: str,
) -> dict[str, Any]:
    """Best-effort cleanup after live deploy failure.

    - Always attempts to delete the created change set.
    - Deletes stack only for CREATE change sets.
    """
    result: dict[str, Any] = {
        "change_set_deleted": False,
        "stack_deleted": False,
        "errors": [],
    }

    try:
        cloudformation_client.delete_change_set(
            StackName=stack_name,
            ChangeSetName=change_set_name,
        )
        result["change_set_deleted"] = True
    except Exception as exc:  # pragma: no cover - provider/runtime behavior
        result["errors"].append(f"delete_change_set failed: {exc}")

    if str(change_set_type).upper() == "CREATE":
        try:
            cloudformation_client.delete_stack(StackName=stack_name)
            result["stack_deleted"] = True
        except Exception as exc:  # pragma: no cover - provider/runtime behavior
            result["errors"].append(f"delete_stack failed: {exc}")

    return result
