# Team Work Split Plan

## Ownership Map (Source of Truth)

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

## Working Rules

- Joint items should be proposed via PR with at least one review from the other owner.
- Shared contracts (`graph/state.py`, KB schema, API interfaces) should not be changed without notifying both owners.
- Use merge points at the end of each phase to reduce integration drift.
