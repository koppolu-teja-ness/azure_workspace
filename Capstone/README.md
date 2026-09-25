# Azure-AWS Migration Assistant

Agentic migration assistant for translating Azure infrastructure definitions
into AWS CloudFormation with workflow orchestration, validation, approval,
and reporting stages.

## Project Status

- Current state: active capstone scaffold with partial Phase 0/1 implementations.
- Workflow graph and state contract are in place.
- Several agents are implemented as stubs or partial logic and are still under active development.
- Phase 1 baseline sign-off (2026-09-25): source-side and target-side Phase 1 deliverables are wired for deterministic execution with Bedrock-enabled paths where required, validated by `python -m pytest -q` (37 passed).

## What This Repo Contains

- LangGraph workflow orchestration for migration stages.
- Agent modules for discovery, mapping, planning, deployment, and reporting.
- Knowledge base assets for mapping rules and incompatibility guidance.
- API surface (`api/`) and dashboard surfaces (`dashboard/`, `streamlit_app/`).
- Tests, fixtures, and sample outputs under `tests/` and `examples/`.

## Quickstart

### 1) Set up Python environment

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -e .
pip install -r requirements-dev.txt
```

### 2) Optional local services

```bash
docker compose up -d postgres
```

### 3) Run tests

```bash
pytest -v
```

### 4) Run workflow smoke test

```bash
python -m migration_assistant.graph.workflow
```

Expected output includes `Final status: MigrationStatus.VERIFIED`.

## Documentation Index

- Architecture summary: [ARCHITECTURE.md](ARCHITECTURE.md)
- Detailed architecture notes and diagram references: [docs/high_level_architecture.md](docs/high_level_architecture.md)
- Developer workflow and contributor notes: [docs/developer_guide.md](docs/developer_guide.md)
- Agent responsibilities: [docs/agent_responsibilities.md](docs/agent_responsibilities.md)
- Migration spec contract: [docs/migration_spec_schema.md](docs/migration_spec_schema.md)
- Mapping rules references: [docs/mapping_rules_reference.md](docs/mapping_rules_reference.md)
- Phase 0 checklist: [docs/phase0_checklist.md](docs/phase0_checklist.md)

## Developer Quick Commands

Use these as quick checks from a fresh clone:

```bash
python -m migration_assistant.graph.workflow
pytest -v
```

For full contributor workflows (targeted test loops, static checks,
integration caveats), use:

[docs/developer_guide.md](docs/developer_guide.md)

## Team Ownership Map

This section mirrors the working ownership split used for implementation.

```text
azure-aws-migration-assistant/
│
├── README.md                                         [joint]
├── ARCHITECTURE.md                                    [joint]
├── docker-compose.yml / Dockerfile                    [joint — Phase 4]
│
├── .github/workflows/                                 [joint — CI base in Phase 0]
│
├── config/
│   ├── settings.yaml                                  [joint — Phase 0]
│   └── region_mapping.yaml                             [joint — Phase 0]
│
├── src/migration_assistant/
│   │
│   ├── agents/
│   │   ├── discovery_agent.py                         [charan]
│   │   ├── parser_analyzer_agent.py                   [charan]
│   │   ├── mapping_agent.py                            [charan]
│   │   ├── cfn_generator_agent.py                      [saurav]
│   │   ├── static_validation_agent.py                  [saurav]
│   │   ├── planning_risk_agent.py                       [charan]
│   │   ├── approval_gate.py                             [charan]
│   │   ├── deployment_agent.py                          [saurav]
│   │   ├── post_deploy_validation_agent.py              [saurav]
│   │   └── reporting_agent.py                           [split — see reporting/ below]
│   │
│   ├── graph/
│   │   ├── workflow.py                                 [joint — Phase 0 skeleton, both wire in nodes]
│   │   ├── state.py                                     [joint — Phase 0, this IS the Migration Spec contract]
│   │   └── checkpoints.py                              [saurav]
│   │
│   ├── azure_discovery/                                [charan]
│   ├── bicep_parser/                                   [charan]
│   │
│   ├── mapping/
│   │   ├── rag_retriever.py                             [charan]
│   │   ├── embeddings.py                                [charan]
│   │   └── mapping_rules/                                [charan]
│   │
│   ├── cfn_generation/                                 [saurav]
│   │
│   ├── validation/
│   │   ├── static/                                      [saurav — Phase 1]
│   │   └── post_deploy/                                 [saurav — Phase 2/3]
│   │
│   ├── planning/                                        [charan — Phase 2]
│   ├── deployment/                                      [saurav — Phase 2]
│   │
│   ├── reporting/
│   │   ├── migration_plan_report.py                    [charan — Phase 3]
│   │   ├── execution_report.py                          [saurav — Phase 3]
│   │   └── validation_report.py                         [saurav — Phase 3]
│   │
│   └── secrets/secure_copy.py                           [saurav, design agreed jointly in Phase 0]
│
├── knowledge_base/
│   ├── ingestion/                                       [joint schema (Phase 0), charan fills content (Phase 1)]
│   ├── data/                                            [charan — Phase 1]
│   └── schema/pgvector_schema.sql                       [joint — Phase 0]
│
├── api/
│   ├── main.py                                          [joint — Phase 4]
│   ├── routers/discovery.py                             [charan]
│   ├── routers/approval.py                              [charan]
│   ├── routers/migration_runs.py                        [joint — Phase 4]
│   └── routers/reports.py                               [joint — Phase 4]
│
├── dashboard/
│   ├── pages/1_Discovery.py                             [charan]
│   ├── pages/2_Migration_Plan.py                        [charan]
│   ├── pages/3_Approval_Gate.py                         [charan — Phase 2]
│   ├── pages/4_Deployment_Status.py                     [saurav]
│   └── pages/5_Validation_Report.py                     [saurav]
│
├── observability/                                       [saurav — Phase 3]
│
├── tests/
│   ├── unit/test_bicep_parser.py, test_mapping_agent.py  [charan]
│   ├── unit/test_cfn_generation.py                        [saurav]
│   ├── integration/                                       [joint — merge points]
│   └── fixtures/
│       ├── sample_bicep/                                   [charan]
│       └── expected_cfn/                                   [saurav]
│
├── scripts/
│   ├── run_discovery.sh                                  [charan]
│   ├── run_migration_pipeline.py                          [joint entrypoint]
│   └── seed_knowledge_base.py                             [charan]
│
├── docs/                                                  [joint — Phase 4]
└── examples/sample_migration_run/                          [joint — Phase 4]
```

For collaboration rules and merge checkpoints, see [team-work-split-plan.md](team-work-split-plan.md).

