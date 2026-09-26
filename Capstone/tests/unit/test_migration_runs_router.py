from fastapi import HTTPException

from api.dependencies import save_run
from api.routers import migration_runs
from migration_assistant.graph.state import MigrationStatus


def test_execute_target_from_spec_runs_target_stages(monkeypatch) -> None:
    payload = migration_runs.ExecuteTargetFromSpecRequest(
        migration_spec={
            "run_id": "target-run-1",
            "created_at": "2026-09-26T00:00:00+00:00",
            "source_resources": [
                {
                    "resource_id": "/r/vnet1",
                    "resource_type": "Microsoft.Network/virtualNetworks",
                    "name": "vnet1",
                    "api_version": "2023-05-01",
                    "location": "eastus",
                    "properties": {"addressSpace": "10.0.0.0/16"},
                    "depends_on": [],
                }
            ],
            "mappings": [
                {
                    "source_resource_id": "/r/vnet1",
                    "target_logical_id": "CoreVpc",
                    "mapping_rule_id": "rule-vnet-vpc",
                    "confidence": 0.95,
                    "notes": [],
                    "unmapped_properties": [],
                }
            ],
            "status": "approved",
            "config": {},
        }
    )

    monkeypatch.setattr(
        migration_runs.cfn_generator_agent,
        "run",
        lambda state: {
            "target_resources": [
                {
                    "logical_id": "CoreVpc",
                    "aws_resource_type": "AWS::EC2::VPC",
                    "properties": {"CidrBlock": "10.0.0.0/16"},
                    "depends_on": [],
                }
            ],
            "status": MigrationStatus.GENERATED,
        },
    )
    monkeypatch.setattr(
        migration_runs.static_validation_agent,
        "run",
        lambda state: {
            "validation_results": [
                {
                    "stage": "static",
                    "resource_id": "target-run-1",
                    "check_name": "schema-validator",
                    "status": "pass",
                    "details": "ok",
                }
            ],
            "status": MigrationStatus.STATIC_VALIDATED,
        },
    )
    monkeypatch.setattr(
        migration_runs.deployment_agent,
        "run",
        lambda state: {
            "config": {
                **state.get("config", {}),
                "deployment_preview": {"mode": "dry_run", "resource_count": 1},
            },
            "status": MigrationStatus.DEPLOYED,
        },
    )
    monkeypatch.setattr(
        migration_runs.post_deploy_validation_agent,
        "run",
        lambda state: {
            "validation_results": [
                {
                    "stage": "post_deploy",
                    "resource_id": "target-run-1",
                    "check_name": "resource-count-equivalence",
                    "status": "pass",
                    "details": "ok",
                }
            ],
            "status": MigrationStatus.VERIFIED,
        },
    )
    monkeypatch.setattr(
        migration_runs.reporting_agent,
        "run",
        lambda state: {
            "config": {**state.get("config", {}), "report_summary": "summary"},
            "llm_traces": [
                {
                    "node": "report",
                    "provider": "aws_bedrock",
                    "model_id": "model",
                    "prompt_version": "report_summary_v1",
                    "status": "ok",
                    "prompt_sha256": "abc",
                    "response_sha256": "def",
                }
            ],
        },
    )

    result = migration_runs.execute_target_from_spec(payload)

    assert result["run_id"] == "target-run-1"
    assert result["status"] == MigrationStatus.VERIFIED.value
    assert len(result["validation_results"]) == 2
    assert result["config"]["deployment_preview"]["mode"] == "dry_run"
    assert result["config"]["report_summary"] == "summary"


def test_execute_target_from_spec_returns_400_for_invalid_payload() -> None:
    payload = migration_runs.ExecuteTargetFromSpecRequest(
        migration_spec={
            "run_id": "bad",
            "created_at": "2026-09-26T00:00:00+00:00",
            "source_resources": [{"resource_id": "/broken"}],
        }
    )

    try:
        migration_runs.execute_target_from_spec(payload)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "Invalid migration_spec payload" in str(exc.detail)


def test_execute_target_for_stored_run_executes_target_stages(monkeypatch) -> None:
    run_id = "target-run-stored-1"
    save_run(
        {
            "run_id": run_id,
            "created_at": "2026-09-26T00:00:00+00:00",
            "source_resources": [
                {
                    "resource_id": "/r/vnet2",
                    "resource_type": "Microsoft.Network/virtualNetworks",
                    "name": "vnet2",
                    "api_version": "2023-05-01",
                    "location": "eastus",
                    "properties": {"addressSpace": "10.1.0.0/16"},
                    "depends_on": [],
                }
            ],
            "mappings": [
                {
                    "source_resource_id": "/r/vnet2",
                    "target_logical_id": "CoreVpc",
                    "mapping_rule_id": "rule-vnet-vpc",
                    "confidence": 0.95,
                    "notes": [],
                    "unmapped_properties": [],
                }
            ],
            "status": MigrationStatus.APPROVED,
            "config": {},
        }
    )

    monkeypatch.setattr(
        migration_runs.cfn_generator_agent,
        "run",
        lambda state: {
            "target_resources": [
                {
                    "logical_id": "CoreVpc",
                    "aws_resource_type": "AWS::EC2::VPC",
                    "properties": {"CidrBlock": "10.1.0.0/16"},
                    "depends_on": [],
                }
            ],
            "status": MigrationStatus.GENERATED,
        },
    )
    monkeypatch.setattr(
        migration_runs.static_validation_agent,
        "run",
        lambda state: {"validation_results": [], "status": MigrationStatus.STATIC_VALIDATED},
    )
    monkeypatch.setattr(
        migration_runs.deployment_agent,
        "run",
        lambda state: {
            "config": {**state.get("config", {}), "deployment_preview": {"mode": "dry_run"}},
            "status": MigrationStatus.DEPLOYED,
        },
    )
    monkeypatch.setattr(
        migration_runs.post_deploy_validation_agent,
        "run",
        lambda state: {"validation_results": [], "status": MigrationStatus.VERIFIED},
    )
    monkeypatch.setattr(
        migration_runs.reporting_agent,
        "run",
        lambda state: {"config": {**state.get("config", {}), "report_summary": "ok"}},
    )

    result = migration_runs.execute_target_for_run(run_id)

    assert result["run_id"] == run_id
    assert result["status"] == MigrationStatus.VERIFIED.value
    assert result["config"]["deployment_preview"]["mode"] == "dry_run"
    assert result["config"]["report_summary"] == "ok"


def test_execute_target_for_stored_run_requires_source_resources() -> None:
    run_id = "target-run-stored-empty"
    save_run(
        {
            "run_id": run_id,
            "created_at": "2026-09-26T00:00:00+00:00",
            "source_resources": [],
            "status": MigrationStatus.APPROVED,
            "config": {},
        }
    )

    try:
        migration_runs.execute_target_for_run(run_id)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "no source resources" in str(exc.detail).lower()
