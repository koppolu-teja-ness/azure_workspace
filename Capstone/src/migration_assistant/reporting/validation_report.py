"""Validation report builder for migration run output."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_validation_report(state: dict[str, Any]) -> dict[str, Any]:
	validation_results = state.get("validation_results", [])

	by_stage: dict[str, dict[str, int]] = {}
	failed_checks: list[dict[str, str | None]] = []
	warning_checks: list[dict[str, str | None]] = []

	for item in validation_results:
		stage_name = item.stage.value
		status_name = item.status.value
		stage_summary = by_stage.setdefault(stage_name, {"pass": 0, "fail": 0, "warning": 0})
		stage_summary[status_name] += 1

		if status_name == "fail":
			failed_checks.append(
				{
					"resource_id": item.resource_id,
					"check_name": item.check_name,
					"details": item.details,
				}
			)
		elif status_name == "warning":
			warning_checks.append(
				{
					"resource_id": item.resource_id,
					"check_name": item.check_name,
					"details": item.details,
				}
			)

	overall = {
		"pass": sum(summary["pass"] for summary in by_stage.values()),
		"fail": sum(summary["fail"] for summary in by_stage.values()),
		"warning": sum(summary["warning"] for summary in by_stage.values()),
	}

	return {
		"report_type": "validation_report",
		"generated_at": datetime.now(UTC).isoformat(),
		"run_id": state.get("run_id"),
		"status": str(state.get("status")),
		"summary": {
			"total": len(validation_results),
			"overall": overall,
			"by_stage": by_stage,
		},
		"failed_checks": failed_checks,
		"warning_checks": warning_checks,
	}
