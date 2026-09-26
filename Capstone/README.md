# Azure-AWS Migration Assistant

Agentic migration assistant for translating Azure infrastructure definitions
into AWS CloudFormation with workflow orchestration, validation, approval,
and reporting stages.

## Project Status

- Current state: active capstone implementation with Phase 1-4 deliverables completed.
- Workflow graph and state contract are in place.
- Phase 1 baseline sign-off (2026-09-25): source-side and target-side Phase 1 deliverables are wired for deterministic execution with Bedrock-enabled paths where required, validated by `python -m pytest -q` (37 passed).
- Phase 3 completion sign-off (2026-09-26): migration test suite, report generation, smoke/security post-deploy checks, and observability assets are implemented and validated by `python -m pytest -q` (58 passed).
- Phase 4 completion sign-off (2026-09-26): API + dashboard flows for discovery/approval/deployment/reporting are integrated, Docker packaging is finalized for API and dashboard services, and full test suite validation reached `63 passed`.

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

To run the full local stack (Postgres + API + Streamlit dashboard):

```bash
docker compose up --build
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

## API Usage (Phase 2)

Start the API server:

```bash
uvicorn api.main:app --reload
```

### Discovery Run Execution

Create a run from local Bicep paths/directories and execute through the
approval gate:

```bash
curl -X POST http://localhost:8000/discovery/runs \
	-H "Content-Type: application/json" \
	-d '{
		"run_id": "phase4-discovery-001",
		"bicep_paths": [],
		"bicep_directories": ["tests/fixtures/sample_bicep"],
		"config": {
			"approval": {
				"auto_approve": false
			}
		}
	}'
```

Inspect discovery run summaries/details:

```bash
curl http://localhost:8000/discovery/runs
curl http://localhost:8000/discovery/runs/<run_id>
```

### Execute Target Pipeline From Migration Spec

Use `POST /runs/execute-target` when Person A has already produced a
`MigrationSpec` and you want to run only Person B stages:

- CFN generation
- static validation
- deployment (dry-run by default, optional live mode)
- post-deploy validation
- reporting

Example request:

```bash
curl -X POST http://localhost:8000/runs/execute-target \
	-H "Content-Type: application/json" \
	-d '{
		"migration_spec": {
			"run_id": "target-demo-001",
			"created_at": "2026-09-26T00:00:00+00:00",
			"source_resources": [
				{
					"resource_id": "/subscriptions/demo/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet-main",
					"resource_type": "Microsoft.Network/virtualNetworks",
					"name": "vnet-main",
					"api_version": "2023-05-01",
					"location": "eastus",
					"properties": {
						"addressSpace": "10.0.0.0/16"
					},
					"depends_on": []
				}
			],
			"mappings": [
				{
					"source_resource_id": "/subscriptions/demo/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet-main",
					"target_logical_id": "CoreVpc",
					"mapping_rule_id": "rule-vnet-vpc",
					"confidence": 0.95,
					"notes": [],
					"unmapped_properties": []
				}
			],
			"status": "approved",
			"config": {
				"llm": {
					"enabled": true,
					"provider": "aws_bedrock",
					"bedrock": {
						"model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
						"region_name": "us-east-1",
						"temperature": 0.7,
						"max_tokens": 512
					}
				},
				"deployment": {
					"live_deploy": false,
					"enable_live_deploy": false
				}
			}
		}
	}'
```

Expected response includes:

- `run_id`, `status`
- `target_resources`
- `validation_results` (both `static` and `post_deploy`)
- `config.deployment_preview` (or `config.deployment_result` in live mode)
- `config.report_summary`

If `migration_spec` is invalid, API returns `400`.
If target pipeline LLM/deployment configuration is invalid, API returns `400` with a config error detail.

To execute target stages for an already saved run without re-posting the full
spec payload:

```bash
curl -X POST http://localhost:8000/runs/<run_id>/execute-target
```

### Fetch Generated Reports

After a run is saved, report payloads can be fetched from dedicated endpoints.
If a specific report payload is not already present in run config, the API
builds it on demand from run state.

Get all reports for a run:

```bash
curl http://localhost:8000/reports/runs/<run_id>
```

Response shape includes:

- `run_id`, `status`, `report_summary`
- `reports.migration_plan_report`
- `reports.risk_report`
- `reports.execution_report`
- `reports.validation_report`

Get individual reports:

```bash
curl http://localhost:8000/reports/runs/<run_id>/migration-plan
curl http://localhost:8000/reports/runs/<run_id>/risk
curl http://localhost:8000/reports/runs/<run_id>/execution
curl http://localhost:8000/reports/runs/<run_id>/validation
```

If `run_id` does not exist, reports endpoints return `404`.

## Documentation Index

- Architecture summary: [ARCHITECTURE.md](ARCHITECTURE.md)
- Detailed architecture notes and diagram references: [docs/high_level_architecture.md](docs/high_level_architecture.md)
- Developer workflow and contributor notes: [docs/developer_guide.md](docs/developer_guide.md)
- Known limitations and open risks: [docs/known_limitations.md](docs/known_limitations.md)
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

