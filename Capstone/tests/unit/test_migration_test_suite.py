from migration_assistant.graph.state import (
    GraphState,
    MappingRecord,
    MigrationStatus,
    ResourceType,
    SourceResource,
)
from migration_assistant.planning.migration_test_suite import run_migration_test_suite


def test_migration_test_suite_passes_for_valid_state() -> None:
    source_resources = [
        SourceResource(
            resource_id="/r/vnet1",
            resource_type=ResourceType.VNET,
            name="vnet1",
            bicep_symbolic_name="vnet1",
            api_version="2023-05-01",
            location="eastus",
            depends_on=[],
        ),
        SourceResource(
            resource_id="/r/subnet1",
            resource_type=ResourceType.SUBNET,
            name="subnet1",
            bicep_symbolic_name="subnet1",
            api_version="2023-05-01",
            location="eastus",
            depends_on=["vnet1"],
        ),
    ]

    state: GraphState = {
        "run_id": "phase3-suite-pass",
        "created_at": "2026-09-26T00:00:00+00:00",
        "source_resources": source_resources,
        "mappings": [
            MappingRecord(
                source_resource_id="/r/vnet1",
                target_logical_id="CoreVpc",
                mapping_rule_id="rule-vnet",
                confidence=0.95,
                notes=[],
                unmapped_properties=[],
            ),
            MappingRecord(
                source_resource_id="/r/subnet1",
                target_logical_id="CoreSubnet",
                mapping_rule_id="rule-subnet",
                confidence=0.9,
                notes=[],
                unmapped_properties=[],
            ),
        ],
        "status": MigrationStatus.MAPPED,
        "config": {},
    }

    result = run_migration_test_suite(state)
    assert result["summary"]["failed"] == 0
    assert result["summary"]["passed"] == 3


def test_migration_test_suite_fails_for_invalid_dependencies_and_missing_objects() -> None:
    source_resources = [
        SourceResource(
            resource_id="/r/vnet1",
            resource_type=ResourceType.VNET,
            name="vnet1",
            bicep_symbolic_name="vnet1",
            api_version="2023-05-01",
            location="eastus",
            depends_on=["missing_symbol"],
        )
    ]

    state: GraphState = {
        "run_id": "phase3-suite-fail",
        "created_at": "2026-09-26T00:00:00+00:00",
        "source_resources": source_resources,
        "mappings": [
            MappingRecord(
                source_resource_id="/r/unknown",
                target_logical_id="Ghost",
                mapping_rule_id="rule-ghost",
                confidence=0.2,
                notes=[],
                unmapped_properties=[],
            )
        ],
        "status": MigrationStatus.MAPPED,
        "config": {},
    }

    result = run_migration_test_suite(state)
    by_name = {check["name"]: check for check in result["checks"]}

    assert by_name["schema_compatibility"]["status"] == "pass"
    assert by_name["dependency_integrity"]["status"] == "fail"
    assert by_name["missing_object_detection"]["status"] == "fail"
    assert result["summary"]["failed"] == 2
