from fastapi import HTTPException

from api.dependencies import save_run
from api.routers import discovery
from migration_assistant.graph.state import MigrationStatus


def test_execute_discovery_runs_pipeline_and_saves_state(monkeypatch) -> None:
    class _FakeGraph:
        def invoke(self, initial_state):
            return {
                **initial_state,
                "source_resources": [
                    {
                        "resource_id": "/subscriptions/demo/resourceGroups/rg/providers/Microsoft.KeyVault/vaults/kv-demo",
                        "resource_type": "Microsoft.KeyVault/vaults",
                        "name": "kv-demo",
                        "api_version": "2023-07-01",
                        "location": "eastus",
                        "properties": {},
                        "depends_on": [],
                    }
                ],
                "status": MigrationStatus.AWAITING_APPROVAL,
                "config": {
                    **initial_state.get("config", {}),
                    "discovered_bicep_files": ["tests/fixtures/sample_bicep/keyvault.bicep"],
                },
            }

    monkeypatch.setattr(discovery, "build_graph", lambda: _FakeGraph())

    payload = discovery.DiscoveryRunRequest(
        run_id="phase4-discovery-router-1",
        bicep_paths=["tests/fixtures/sample_bicep/keyvault.bicep"],
        bicep_directories=[],
        config={"approval": {"auto_approve": False}},
    )

    result = discovery.execute_discovery(payload)

    assert result["run_id"] == "phase4-discovery-router-1"
    assert result["status"] == MigrationStatus.AWAITING_APPROVAL.value
    assert len(result["source_resources"]) == 1
    assert result["config"]["discovered_bicep_files"] == [
        "tests/fixtures/sample_bicep/keyvault.bicep"
    ]


def test_get_discovery_runs_lists_counts() -> None:
    run_id = "phase4-discovery-router-2"
    save_run(
        {
            "run_id": run_id,
            "created_at": "2026-09-26T00:00:00+00:00",
            "source_resources": [{}],
            "mappings": [{}, {}],
            "status": MigrationStatus.PARSED,
            "config": {
                "discovered_bicep_files": [
                    "tests/fixtures/sample_bicep/keyvault.bicep",
                    "tests/fixtures/sample_bicep/vnet.bicep",
                ]
            },
        }
    )

    payload = discovery.get_discovery_runs()
    match = next(item for item in payload["runs"] if item["run_id"] == run_id)

    assert match["status"] == MigrationStatus.PARSED.value
    assert match["counts"]["discovered_files"] == 2
    assert match["counts"]["source_resources"] == 1
    assert match["counts"]["mappings"] == 2


def test_get_discovery_run_detail_returns_404_for_unknown_run() -> None:
    try:
        discovery.get_discovery_run_detail("missing-discovery-run")
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 404
        assert "not found" in str(exc.detail).lower()
