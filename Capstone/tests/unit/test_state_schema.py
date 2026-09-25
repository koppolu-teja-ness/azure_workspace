"""Sanity tests for the Migration Spec contract — the one thing both
branches depend on. Keep this passing at every merge point."""
from migration_assistant.graph.state import (
    ApprovalDecision,
    MigrationSpec,
    MigrationStatus,
    ResourceType,
    SourceResource,
    graph_state_to_spec,
    spec_to_graph_state,
)


def test_migration_spec_round_trips_through_graph_state():
    spec = MigrationSpec(
        source_resources=[
            SourceResource(
                resource_id=(
                    "/subscriptions/x/resourceGroups/y/providers/"
                    "Microsoft.KeyVault/vaults/kv1"
                ),
                resource_type=ResourceType.KEY_VAULT,
                name="kv1",
                api_version="2023-07-01",
                location="eastus",
            )
        ],
        status=MigrationStatus.DISCOVERED,
    )

    state = spec_to_graph_state(spec)
    assert isinstance(state, dict)
    assert state["run_id"] == spec.run_id

    rehydrated = graph_state_to_spec(state)
    assert rehydrated.run_id == spec.run_id
    assert len(rehydrated.source_resources) == 1
    assert rehydrated.source_resources[0].name == "kv1"


def test_migration_spec_has_stable_defaults():
    assert MigrationSpec().status == MigrationStatus.DISCOVERED
    assert MigrationSpec().approval == ApprovalDecision()


def test_migration_spec_json_schema_is_exportable():
    schema = MigrationSpec().to_json_schema()
    assert "properties" in schema
    assert "source_resources" in schema["properties"]
