"""Migration plan and risk report builders.

These reports summarize Person A Phase 3 planning outputs.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_migration_plan_report(state: dict[str, Any]) -> dict[str, Any]:
	config = state.get("config", {}) if isinstance(state.get("config", {}), dict) else {}
	migration_plan = config.get("migration_plan", {})
	migration_tests = config.get("migration_test_suite", {})
	risk_assessments = state.get("risk_assessments", [])

	report = {
		"report_type": "migration_plan",
		"generated_at": datetime.now(UTC).isoformat(),
		"run_id": state.get("run_id"),
		"status": str(state.get("status")),
		"resource_count": migration_plan.get("resource_count", len(state.get("source_resources", []))),
		"mapping_count": migration_plan.get("mapping_count", len(state.get("mappings", []))),
		"risk_summary": migration_plan.get(
			"risk_summary",
			_build_risk_summary(risk_assessments),
		),
		"sequence": migration_plan.get("sequence", []),
		"migration_test_suite": migration_tests,
	}
	return report


def build_risk_report(state: dict[str, Any]) -> dict[str, Any]:
	risk_assessments = state.get("risk_assessments", [])
	entries = []
	for item in risk_assessments:
		entries.append(
			{
				"resource_id": item.resource_id,
				"risk_level": item.risk_level.value,
				"reasons": list(item.reasons),
			}
		)

	return {
		"report_type": "risk_report",
		"generated_at": datetime.now(UTC).isoformat(),
		"run_id": state.get("run_id"),
		"status": str(state.get("status")),
		"risk_summary": _build_risk_summary(risk_assessments),
		"high_risk_resources": [
			entry for entry in entries if entry["risk_level"] == "high_risk"
		],
		"needs_review_resources": [
			entry for entry in entries if entry["risk_level"] == "needs_review"
		],
		"auto_migratable_resources": [
			entry for entry in entries if entry["risk_level"] == "auto_migratable"
		],
	}


def _build_risk_summary(risk_assessments: list[Any]) -> dict[str, int]:
	auto_count = sum(
		1 for item in risk_assessments if getattr(item.risk_level, "value", "") == "auto_migratable"
	)
	review_count = sum(
		1 for item in risk_assessments if getattr(item.risk_level, "value", "") == "needs_review"
	)
	high_count = sum(
		1 for item in risk_assessments if getattr(item.risk_level, "value", "") == "high_risk"
	)
	return {
		"auto_migratable": auto_count,
		"needs_review": review_count,
		"high_risk": high_count,
	}
