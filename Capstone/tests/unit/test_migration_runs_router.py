from fastapi import HTTPException

from api.dependencies import save_run
from api.routers import migration_runs
from migration_assistant.graph.state import MigrationSpec, MigrationStatus, spec_to_graph_state


LLM_CONFIG = {
    "llm": {
        "enabled": True,
        "provider": "aws_bedrock",
        "bedrock": {
            "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "region_name": "us-east-1",
            "temperature": 0.7,
            "max_tokens": 512,
        },
    }
}


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
            "config": {**LLM_CONFIG},
        }
    )

    saved_stages: list[str] = []
    monkeypatch.setattr(
        migration_runs,
        "save_run_checkpoint",
        lambda state, *, stage: saved_stages.append(stage),
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
    assert saved_stages == [
        "generate_cfn",
        "static_validate",
        "deploy",
        "post_deploy_validate",
        "report",
        "target_pipeline_complete",
    ]


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
            "config": {**LLM_CONFIG},
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
            "config": {**LLM_CONFIG},
        }
    )

    try:
        migration_runs.execute_target_for_run(run_id)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "no source resources" in str(exc.detail).lower()


def test_get_run_checkpoints_returns_checkpoint_list(monkeypatch) -> None:
    monkeypatch.setattr(
        migration_runs,
        "list_run_checkpoints",
        lambda run_id: [
            {"id": 1, "stage": "generate_cfn", "created_at": "2026-09-28T00:00:00+00:00"},
            {"id": 2, "stage": "static_validate", "created_at": "2026-09-28T00:01:00+00:00"},
        ],
    )

    payload = migration_runs.get_run_checkpoints("resume-run-1")

    assert payload["run_id"] == "resume-run-1"
    assert len(payload["checkpoints"]) == 2
    assert payload["checkpoints"][0]["stage"] == "generate_cfn"


def test_resume_target_for_run_continues_from_next_stage(monkeypatch) -> None:
    state = spec_to_graph_state(
        MigrationSpec.model_validate(
            {
                "run_id": "resume-run-2",
                "created_at": "2026-09-28T00:00:00+00:00",
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
                "target_resources": [
                    {
                        "logical_id": "CoreVpc",
                        "aws_resource_type": "AWS::EC2::VPC",
                        "properties": {"CidrBlock": "10.1.0.0/16"},
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
                "status": MigrationStatus.STATIC_VALIDATED,
                "config": {**LLM_CONFIG},
            }
        )
    )

    monkeypatch.setattr(
        migration_runs,
        "get_latest_run_checkpoint",
        lambda run_id: ("static_validate", state),
    )

    called_stages: list[str] = []
    monkeypatch.setattr(
        migration_runs,
        "save_run_checkpoint",
        lambda s, *, stage: called_stages.append(stage),
    )

    monkeypatch.setattr(
        migration_runs.cfn_generator_agent,
        "run",
        lambda s: (_ for _ in ()).throw(RuntimeError("should not rerun generate_cfn")),
    )
    monkeypatch.setattr(
        migration_runs.static_validation_agent,
        "run",
        lambda s: (_ for _ in ()).throw(RuntimeError("should not rerun static_validate")),
    )
    monkeypatch.setattr(
        migration_runs.deployment_agent,
        "run",
        lambda s: {
            "config": {**s.get("config", {}), "deployment_preview": {"mode": "dry_run"}},
            "status": MigrationStatus.DEPLOYED,
        },
    )
    monkeypatch.setattr(
        migration_runs.post_deploy_validation_agent,
        "run",
        lambda s: {"validation_results": [], "status": MigrationStatus.VERIFIED},
    )
    monkeypatch.setattr(
        migration_runs.reporting_agent,
        "run",
        lambda s: {"config": {**s.get("config", {}), "report_summary": "resumed"}},
    )

    payload = migration_runs.resume_target_for_run("resume-run-2")

    assert payload["run_id"] == "resume-run-2"
    assert payload["status"] == MigrationStatus.VERIFIED.value
    assert payload["config"]["report_summary"] == "resumed"
    assert called_stages == ["deploy", "post_deploy_validate", "report", "target_pipeline_complete"]
