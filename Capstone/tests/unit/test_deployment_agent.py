from migration_assistant.agents import deployment_agent
from migration_assistant.deployment.cloudformation_deployer import (
    build_stack_name,
    order_resources_for_deployment,
)
from migration_assistant.graph.state import GraphState, MigrationStatus, TargetResource


def test_order_resources_for_deployment_respects_dependencies() -> None:
    resources = [
        TargetResource(
            logical_id="AppSubnet",
            aws_resource_type="AWS::EC2::Subnet",
            properties={"CidrBlock": "10.0.1.0/24"},
            depends_on=["CoreVpc"],
        ),
        TargetResource(
            logical_id="CoreVpc",
            aws_resource_type="AWS::EC2::VPC",
            properties={"CidrBlock": "10.0.0.0/16"},
            depends_on=[],
        ),
    ]

    ordered = order_resources_for_deployment(resources)

    assert [resource.logical_id for resource in ordered] == ["CoreVpc", "AppSubnet"]


def test_deployment_agent_generates_dry_run_preview_only() -> None:
    state: GraphState = {
        "run_id": "Run_01",
        "created_at": "2026-09-25T00:00:00+00:00",
        "target_resources": [
            TargetResource(
                logical_id="CoreVpc",
                aws_resource_type="AWS::EC2::VPC",
                properties={"CidrBlock": "10.0.0.0/16"},
                depends_on=[],
            ),
            TargetResource(
                logical_id="AppSubnet",
                aws_resource_type="AWS::EC2::Subnet",
                properties={"CidrBlock": "10.0.1.0/24", "VpcId": {"Ref": "CoreVpc"}},
                depends_on=["CoreVpc"],
            ),
        ],
        "status": MigrationStatus.APPROVED,
        "config": {
            "aws": {"region_name": "us-east-1"},
            "deployment": {"live_deploy": True},
        },
    }

    update = deployment_agent.run(state)

    assert update["status"] == MigrationStatus.DEPLOYED
    preview = update["config"]["deployment_preview"]
    assert preview["mode"] == "dry_run"
    assert preview["resource_count"] == 2
    assert preview["ordered_logical_ids"] == ["CoreVpc", "AppSubnet"]
    assert preview["live_deploy_requested"] is True
    assert preview["live_deploy_supported"] is False
    assert preview["region_name"] == "us-east-1"


def test_build_stack_name_normalizes_run_id() -> None:
    stack_name = build_stack_name("Run 01/Prod")

    assert stack_name.startswith("migration-run-01-prod")
    assert len(stack_name) <= 128


def test_deployment_agent_uses_live_mode_when_enabled(monkeypatch) -> None:
    state: GraphState = {
        "run_id": "RunLive01",
        "created_at": "2026-09-25T00:00:00+00:00",
        "target_resources": [
            TargetResource(
                logical_id="CoreVpc",
                aws_resource_type="AWS::EC2::VPC",
                properties={"CidrBlock": "10.0.0.0/16"},
                depends_on=[],
            ),
        ],
        "status": MigrationStatus.APPROVED,
        "config": {
            "aws": {"region_name": "us-east-1"},
            "deployment": {
                "live_deploy": True,
                "enable_live_deploy": True,
                "stack_name": "mig-live-test",
                "execute_change_set": False,
            },
        },
    }

    monkeypatch.setattr(
        "migration_assistant.deployment.cloudformation_deployer.CloudFormationDeployer.deploy_stack",
        lambda self, **kwargs: {
            "mode": "live",
            "stack_name": kwargs["stack_name"],
            "change_set_name": "mig-live-test-exec",
            "executed": False,
        },
    )

    update = deployment_agent.run(state)

    assert update["status"] == MigrationStatus.DEPLOYED
    assert update["config"]["deployment_result"]["mode"] == "live"
    assert update["config"]["deployment_result"]["stack_name"] == "mig-live-test"
