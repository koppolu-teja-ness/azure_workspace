from migration_assistant.agents import static_validation_agent
from migration_assistant.graph.state import (
    GraphState,
    MigrationStatus,
    TargetResource,
    ValidationResult,
    ValidationStage,
    ValidationStatus,
)


def _build_state(target_resources: list[TargetResource]) -> GraphState:
    return {
        "run_id": "run-static-1",
        "created_at": "2026-09-25T00:00:00+00:00",
        "target_resources": target_resources,
        "validation_results": [],
        "status": MigrationStatus.GENERATED,
        "config": {},
    }


def test_static_validation_agent_aggregates_runner_results(monkeypatch) -> None:
    target_resources = [
        TargetResource(
            logical_id="CoreVpc",
            aws_resource_type="AWS::EC2::VPC",
            properties={"CidrBlock": "10.0.0.0/16"},
            depends_on=[],
        )
    ]

    schema_result = ValidationResult(
        stage=ValidationStage.STATIC,
        resource_id="run-static-1",
        check_name="schema-validator",
        status=ValidationStatus.PASS,
        details="ok",
    )
    lint_result = ValidationResult(
        stage=ValidationStage.STATIC,
        resource_id="CoreVpc",
        check_name="E3001",
        status=ValidationStatus.WARNING,
        details="warning",
    )
    checkov_result = ValidationResult(
        stage=ValidationStage.STATIC,
        resource_id="CoreVpc",
        check_name="CKV_AWS_1",
        status=ValidationStatus.FAIL,
        details="failed",
    )

    monkeypatch.setattr(
        static_validation_agent,
        "validate_template_schema",
        lambda template, run_id: [schema_result],
    )
    monkeypatch.setattr(
        static_validation_agent,
        "run_cfn_lint",
        lambda template_path, run_id: [lint_result],
    )
    monkeypatch.setattr(
        static_validation_agent,
        "run_checkov",
        lambda template_path, run_id: [checkov_result],
    )

    update = static_validation_agent.run(_build_state(target_resources))

    assert update["status"] == MigrationStatus.STATIC_VALIDATED
    assert len(update["validation_results"]) == 3
    check_names = {result.check_name for result in update["validation_results"]}
    assert check_names == {"schema-validator", "E3001", "CKV_AWS_1"}


def test_static_validation_agent_warns_when_no_target_resources() -> None:
    update = static_validation_agent.run(_build_state([]))

    assert update["status"] == MigrationStatus.STATIC_VALIDATED
    assert len(update["validation_results"]) == 1
    result = update["validation_results"][0]
    assert result.check_name == "static-validation"
    assert result.status == ValidationStatus.WARNING
