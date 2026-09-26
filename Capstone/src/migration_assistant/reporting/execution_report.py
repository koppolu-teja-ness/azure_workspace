"""Execution report builder for migration run output."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_execution_report(state: dict[str, Any]) -> dict[str, Any]:
	config = state.get("config", {}) if isinstance(state.get("config", {}), dict) else {}
	deployment_preview = config.get("deployment_preview")
	deployment_result = config.get("deployment_result")

	if isinstance(deployment_result, dict):
		mode = deployment_result.get("mode", "live")
		deployment_status = deployment_result.get("status", "completed")
		details = deployment_result
	elif isinstance(deployment_preview, dict):
		mode = deployment_preview.get("mode", "dry_run")
		deployment_status = "preview"
		details = deployment_preview
	else:
		mode = "unknown"
		deployment_status = "not_available"
		details = {
			"message": "No deployment preview/result found in run config.",
		}

	return {
		"report_type": "execution_report",
		"generated_at": datetime.now(UTC).isoformat(),
		"run_id": state.get("run_id"),
		"status": str(state.get("status")),
		"deployment_mode": mode,
		"deployment_status": deployment_status,
		"target_resource_count": len(state.get("target_resources", [])),
		"details": details,
	}
