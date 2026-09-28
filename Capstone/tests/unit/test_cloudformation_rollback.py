from migration_assistant.deployment.boto3_client import Boto3ClientFactory
from migration_assistant.deployment.cloudformation_deployer import CloudFormationDeployer


class _FakeWaiter:
    def wait(self, **kwargs):
        _ = kwargs


class _FakeCloudFormationClient:
    def __init__(self) -> None:
        self.deleted_change_set = False
        self.deleted_stack = False

    def describe_stacks(self, **kwargs):
        _ = kwargs
        raise RuntimeError("stack does not exist")

    def create_change_set(self, **kwargs):
        _ = kwargs
        return {"Id": "cs-123"}

    def get_waiter(self, name: str):
        _ = name
        return _FakeWaiter()

    def execute_change_set(self, **kwargs):
        _ = kwargs
        raise RuntimeError("execute failed")

    def delete_change_set(self, **kwargs):
        _ = kwargs
        self.deleted_change_set = True

    def delete_stack(self, **kwargs):
        _ = kwargs
        self.deleted_stack = True


def test_live_deploy_failure_triggers_cleanup(monkeypatch) -> None:
    fake_client = _FakeCloudFormationClient()

    factory = Boto3ClientFactory(region_name="us-east-1")
    monkeypatch.setattr(
        Boto3ClientFactory,
        "cloudformation_client",
        lambda self: fake_client,
    )

    deployer = CloudFormationDeployer(
        client_factory=factory,
        live_deploy_enabled=True,
        cleanup_on_failure=True,
    )

    try:
        deployer.deploy_stack(
            run_id="run-rollback-1",
            template_body="AWSTemplateFormatVersion: '2010-09-09'\nResources: {}",
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "cleanup=" in str(exc)

    assert fake_client.deleted_change_set is True
    assert fake_client.deleted_stack is True
