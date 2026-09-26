from fastapi import HTTPException

from api.dependencies import save_run
from api.routers import reports
from migration_assistant.graph.state import (
    GraphState,
    MappingRecord,
    MigrationStatus,
    RiskAssessment,
    RiskLevel,
    ValidationResult,
    ValidationStage,
    ValidationStatus,
)


def _build_state(run_id: str) -> GraphState:
    return {
        "run_id": run_id,
        "created_at": "2026-09-26T00:00:00+00:00",
        "mappings": [
            MappingRecord(
                source_resource_id="/r/1",
                target_logical_id="CoreVpc",
                confidence=0.93,
            )
        ],
        "risk_assessments": [
            RiskAssessment(
                resource_id="/r/1",
                risk_level=RiskLevel.AUTO_MIGRATABLE,
                reasons=[],
            )
        ],
        "validation_results": [
            ValidationResult(
                stage=ValidationStage.STATIC,
                resource_id=run_id,
                check_name="schema-validator",
                status=ValidationStatus.PASS,
                details="ok",
            ),
            ValidationResult(
                stage=ValidationStage.POST_DEPLOY,
                resource_id=run_id,
                check_name="security-public-exposure-diff",
                status=ValidationStatus.WARNING,
                details="warning",
            ),
        ],
        "status": MigrationStatus.VERIFIED,
        "config": {
            "report_summary": "Stored summary",
            "migration_plan": {
                "resource_count": 1,
                "mapping_count": 1,
                "risk_summary": {
                    "auto_migratable": 1,
                    "needs_review": 0,
                    "high_risk": 0,
                },
                "sequence": [{"sequence": 1, "resource_id": "/r/1"}],
            },
            "migration_test_suite": {
                "summary": {"total": 3, "passed": 3, "failed": 0},
                "checks": [],
            },
            "deployment_preview": {
                "mode": "dry_run",
                "resource_count": 1,
            },
        },
    }


def test_get_run_reports_builds_reports_when_missing_in_config() -> None:
    run_id = "reports-fallback-1"
    save_run(_build_state(run_id))

    payload = reports.get_run_reports(run_id)

    assert payload["run_id"] == run_id
    assert payload["status"] == "verified"
    assert payload["report_summary"] == "Stored summary"
    assert payload["reports"]["migration_plan_report"]["report_type"] == "migration_plan"
    assert payload["reports"]["risk_report"]["report_type"] == "risk_report"
    assert payload["reports"]["execution_report"]["report_type"] == "execution_report"
    assert payload["reports"]["validation_report"]["report_type"] == "validation_report"


def test_get_report_endpoints_return_individual_reports() -> None:
    run_id = "reports-individual-1"
    save_run(_build_state(run_id))

    migration_plan = reports.get_migration_plan_report(run_id)
    risk = reports.get_risk_report(run_id)
    execution = reports.get_execution_report(run_id)
    validation = reports.get_validation_report(run_id)

    assert migration_plan["report_type"] == "migration_plan"
    assert risk["report_type"] == "risk_report"
    assert execution["report_type"] == "execution_report"
    assert validation["report_type"] == "validation_report"


def test_get_reports_returns_404_for_unknown_run() -> None:
    try:
        reports.get_run_reports("missing-run")
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 404
        assert "not found" in str(exc.detail).lower()