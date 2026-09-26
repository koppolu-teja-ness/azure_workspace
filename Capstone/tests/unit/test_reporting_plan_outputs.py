from migration_assistant.agents import reporting_agent
from migration_assistant.graph.state import (
    GraphState,
    MappingRecord,
    MigrationStatus,
    RiskAssessment,
    RiskLevel,
)
from migration_assistant.reporting.migration_plan_report import (
    build_migration_plan_report,
    build_risk_report,
)


def test_build_migration_plan_report_includes_test_suite() -> None:
    state: GraphState = {
        "run_id": "report-plan-1",
        "created_at": "2026-09-26T00:00:00+00:00",
        "mappings": [
            MappingRecord(
                source_resource_id="/r/1",
                target_logical_id="VpcMain",
                confidence=0.92,
            )
        ],
        "risk_assessments": [
            RiskAssessment(
                resource_id="/r/1",
                risk_level=RiskLevel.AUTO_MIGRATABLE,
                reasons=[],
            )
        ],
        "status": MigrationStatus.PLANNED,
        "config": {
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
        },
    }

    report = build_migration_plan_report(state)
    assert report["report_type"] == "migration_plan"
    assert report["run_id"] == "report-plan-1"
    assert report["risk_summary"]["auto_migratable"] == 1
    assert report["migration_test_suite"]["summary"]["passed"] == 3


def test_build_risk_report_partitions_by_risk_level() -> None:
    state: GraphState = {
        "run_id": "risk-partition-1",
        "created_at": "2026-09-26T00:00:00+00:00",
        "risk_assessments": [
            RiskAssessment(
                resource_id="/r/high",
                risk_level=RiskLevel.HIGH_RISK,
                reasons=["No mapped target resource."],
            ),
            RiskAssessment(
                resource_id="/r/review",
                risk_level=RiskLevel.NEEDS_REVIEW,
                reasons=["Low confidence."],
            ),
            RiskAssessment(
                resource_id="/r/auto",
                risk_level=RiskLevel.AUTO_MIGRATABLE,
                reasons=[],
            ),
        ],
        "status": MigrationStatus.PLANNED,
        "config": {},
    }

    report = build_risk_report(state)
    assert report["risk_summary"] == {
        "auto_migratable": 1,
        "needs_review": 1,
        "high_risk": 1,
    }
    assert len(report["high_risk_resources"]) == 1
    assert len(report["needs_review_resources"]) == 1
    assert len(report["auto_migratable_resources"]) == 1


def test_reporting_agent_writes_plan_and_risk_reports(monkeypatch) -> None:
    def _mock_report_llm(*, settings, prompt, runtime_client=None):
        _ = settings, prompt, runtime_client
        return "Summary line"

    monkeypatch.setattr(
        "migration_assistant.reporting.bedrock_report_writer.invoke_bedrock_text",
        _mock_report_llm,
    )

    state: GraphState = {
        "run_id": "reporting-agent-1",
        "created_at": "2026-09-26T00:00:00+00:00",
        "risk_assessments": [
            RiskAssessment(
                resource_id="/r/1",
                risk_level=RiskLevel.AUTO_MIGRATABLE,
                reasons=[],
            )
        ],
        "status": MigrationStatus.VERIFIED,
        "config": {
            "llm": {
                "enabled": True,
                "provider": "aws_bedrock",
                "bedrock": {
                    "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "temperature": 0.7,
                },
            },
            "migration_plan": {
                "resource_count": 0,
                "mapping_count": 0,
                "risk_summary": {
                    "auto_migratable": 1,
                    "needs_review": 0,
                    "high_risk": 0,
                },
                "sequence": [],
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

    update = reporting_agent.run(state)
    config = update["config"]

    assert config["report_summary"] == "Summary line"
    assert config["migration_plan_report"]["run_id"] == "reporting-agent-1"
    assert config["risk_report"]["risk_summary"]["auto_migratable"] == 1
    assert config["execution_report"]["deployment_mode"] == "dry_run"
    assert config["validation_report"]["report_type"] == "validation_report"
    assert len(update["llm_traces"]) == 1
