# Developer Guide

This guide is for contributors working on implementation details, tests, and
integration behavior.

This is the canonical contributor workflow document. The root README is
intentionally brief and points here for implementation details.

## Scope And Reality Check

Current repository status is mixed:

- The graph structure and state schema are implemented.
- Several agents are deterministic and usable in tests.
- API routers and Streamlit dashboard pages are integrated for discovery,
  approval, deployment execution, and report retrieval.
- Some LLM-enabled paths remain optional and config-gated.

Before large changes, review:

- `src/migration_assistant/graph/workflow.py`
- `src/migration_assistant/graph/state.py`
- `docs/agent_responsibilities.md`

## Environment Setup

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -e .
pip install -r requirements-dev.txt
```

Optional local Postgres for vector workflows:

```bash
docker compose up -d postgres
```

Full local stack:

```bash
docker compose up --build
```

## Common Dev Loops

Graph smoke run:

```bash
python -m migration_assistant.graph.workflow
```

Pipeline CLI with local fixture inputs:

```bash
python scripts/run_migration_pipeline.py --run-id dev-run --bicep-dir ./tests/fixtures/sample_bicep
```

Reports API quick checks (after a run is saved via `/runs/execute` or
`/runs/execute-target`):

```bash
curl http://localhost:8000/reports/runs/<run_id>
curl http://localhost:8000/reports/runs/<run_id>/migration-plan
curl http://localhost:8000/reports/runs/<run_id>/risk
curl http://localhost:8000/reports/runs/<run_id>/execution
curl http://localhost:8000/reports/runs/<run_id>/validation
```

Notes:

- Aggregate endpoint returns all report payloads plus `report_summary`.
- Individual endpoints return one report each.
- If a report payload is not present in run config, it is generated on demand
  from run state.
- Unknown run IDs return `404`.

Discovery and target-stage API quick checks:

```bash
curl -X POST http://localhost:8000/discovery/runs -H "Content-Type: application/json" -d '{"run_id":"dev-discovery-1","bicep_paths":[],"bicep_directories":["tests/fixtures/sample_bicep"],"config":{"approval":{"auto_approve":false}}}'
curl http://localhost:8000/discovery/runs
curl -X POST http://localhost:8000/runs/<run_id>/execute-target
```

Targeted test runs:

```bash
pytest -v tests/unit/test_mapping_agent.py
pytest -v tests/unit/test_llm_required_agents.py
pytest -v tests/integration/test_end_to_end_pipeline.py
```

Full test run:

```bash
pytest -v
```

## Code Quality And Static Checks

Configured tooling in `pyproject.toml`:

- Ruff (`[tool.ruff]`, `[tool.ruff.lint]`)
- Mypy (`[tool.mypy]`)
- Pytest (`[tool.pytest.ini_options]`)

Suggested pre-PR checks:

```bash
ruff check src tests scripts knowledge_base
mypy src
pytest -v
```

## Working With GraphState Safely

`GraphState` is the runtime contract for all nodes.

Guidelines:

- Keep list-valued node updates intentional because list fields merge by
  append semantics.
- Avoid silent schema drift in `MigrationSpec` models.
- Treat state contract changes as isolated PRs with explicit reviewer attention.

Reference:

- `docs/migration_spec_schema.md`

## LLM/Bedrock Integration Notes

Current behavior in code:

- Mapping and planning paths call `require_bedrock_settings(...)` in their
  current implementations.
- Missing required Bedrock settings will raise a configuration error for those
  paths.
- Reporting currently returns early in stub mode before Bedrock summary logic.

Related modules:

- `src/migration_assistant/llm/bedrock_runtime.py`
- `src/migration_assistant/agents/mapping_agent.py`
- `src/migration_assistant/agents/planning_risk_agent.py`
- `src/migration_assistant/agents/reporting_agent.py`

## Known In-Progress Areas

These are useful to know before debugging pipeline outputs:

- Live deployment to AWS is disabled by default (`deployment.enable_live_deploy=false`).
- Some Azure/AWS edge-case mappings still route to review/modify flows.
- Vector retrieval behavior depends on optional Postgres/pgvector availability.

## PR Checklist For Contributors

1. Confirm state contract compatibility (`MigrationSpec` / `GraphState`).
2. Add or update unit tests with any behavior changes.
3. Run at least targeted tests for touched modules.
4. Update relevant docs in `docs/` when behavior or constraints change.
5. Keep changes small when touching shared merge points (`workflow.py`,
   `state.py`).
