from migration_assistant.agents import post_deploy_validation_agent
from migration_assistant.graph.state import (
    GraphState,
    MappingRecord,
    MigrationStatus,
    ResourceType,
    SourceResource,
    TargetResource,
    ValidationStatus,
)


def _base_state() -> GraphState:
    return {
        "run_id": "post-deploy-run",
        "created_at": "2026-09-25T00:00:00+00:00",
        "source_resources": [],
        "target_resources": [],
        "mappings": [],
        "validation_results": [],
        "status": MigrationStatus.DEPLOYED,
        "config": {},
    }


def test_post_deploy_validation_warns_when_no_mappings() -> None:
    state = _base_state()

    update = post_deploy_validation_agent.run(state)

    assert update["status"] == MigrationStatus.VERIFIED
    assert len(update["validation_results"]) == 1
    assert update["validation_results"][0].status == ValidationStatus.WARNING


def test_post_deploy_validation_fails_on_resource_count_mismatch() -> None:
    state = _base_state()
    state["source_resources"] = [
        SourceResource(
            resource_id="/subscriptions/demo/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1",
            resource_type=ResourceType.VNET,
            name="vnet1",
            api_version="2023-05-01",
            location="eastus",
            properties={"addressSpace": "10.0.0.0/16"},
        )
    ]
    state["mappings"] = [
        MappingRecord(
            source_resource_id=state["source_resources"][0].resource_id,
            target_logical_id="CoreVpc",
            confidence=0.9,
        )
    ]

    update = post_deploy_validation_agent.run(state)

    assert update["status"] == MigrationStatus.FAILED
    count_result = next(
        item
        for item in update["validation_results"]
        if item.check_name == "resource-count-equivalence"
    )
    assert count_result.status == ValidationStatus.FAIL


def test_post_deploy_validation_verifies_when_counts_match() -> None:
    state = _base_state()
    source = SourceResource(
        resource_id="/subscriptions/demo/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1",
        resource_type=ResourceType.VNET,
        name="vnet1",
        api_version="2023-05-01",
        location="eastus",
        properties={"addressSpace": "10.0.0.0/16"},
    )
    state["source_resources"] = [source]
    state["mappings"] = [
        MappingRecord(
            source_resource_id=source.resource_id,
            target_logical_id="CoreVpc",
            confidence=0.9,
        )
    ]
    state["target_resources"] = [
        TargetResource(
            logical_id="CoreVpc",
            aws_resource_type="AWS::EC2::VPC",
            properties={"CidrBlock": "10.0.0.0/16"},
            depends_on=[],
        )
    ]

    update = post_deploy_validation_agent.run(state)

    assert update["status"] == MigrationStatus.VERIFIED
    count_result = next(
        item
        for item in update["validation_results"]
        if item.check_name == "resource-count-equivalence"
    )
    assert count_result.status == ValidationStatus.PASS

    smoke_result = next(
        item
        for item in update["validation_results"]
        if item.check_name == "smoke-network-reachability"
    )
    assert smoke_result.status == ValidationStatus.PASS


def test_post_deploy_validation_fails_for_public_exposure() -> None:
    state = _base_state()
    source = SourceResource(
        resource_id="/subscriptions/demo/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1",
        resource_type=ResourceType.VNET,
        name="vnet1",
        api_version="2023-05-01",
        location="eastus",
        properties={"addressSpace": "10.0.0.0/16"},
    )
    state["source_resources"] = [source]
    state["mappings"] = [
        MappingRecord(
            source_resource_id=source.resource_id,
            target_logical_id="PublicSubnetSg",
            confidence=0.95,
        )
    ]
    state["target_resources"] = [
        TargetResource(
            logical_id="PublicSubnetSg",
            aws_resource_type="AWS::EC2::SecurityGroup",
            properties={
                "GroupDescription": "test",
                "SecurityGroupIngress": [
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 443,
                        "ToPort": 443,
                        "CidrIp": "0.0.0.0/0",
                    }
                ],
            },
            depends_on=[],
        )
    ]

    update = post_deploy_validation_agent.run(state)

    assert update["status"] == MigrationStatus.FAILED
    security_result = next(
        item
        for item in update["validation_results"]
        if item.check_name == "security-public-exposure-diff"
    )
    assert security_result.status == ValidationStatus.FAIL


def test_post_deploy_validation_fails_for_overbroad_iam() -> None:
    state = _base_state()
    source = SourceResource(
        resource_id="/subscriptions/demo/resourceGroups/rg/providers/Microsoft.Web/sites/fn1",
        resource_type=ResourceType.FUNCTION_APP,
        name="fn1",
        api_version="2023-12-01",
        location="eastus",
        properties={},
    )
    state["source_resources"] = [source]
    state["mappings"] = [
        MappingRecord(
            source_resource_id=source.resource_id,
            target_logical_id="FnExecutionRole",
            confidence=0.95,
        )
    ]
    state["target_resources"] = [
        TargetResource(
            logical_id="FnExecutionRole",
            aws_resource_type="AWS::IAM::Policy",
            properties={
                "PolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "*",
                            "Resource": "*",
                        }
                    ],
                }
            },
            depends_on=[],
        )
    ]

    update = post_deploy_validation_agent.run(state)

    assert update["status"] == MigrationStatus.FAILED
    iam_result = next(
        item
        for item in update["validation_results"]
        if item.check_name == "security-iam-overbroadening-diff"
    )
    assert iam_result.status == ValidationStatus.FAIL
