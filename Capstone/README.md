# Azure → AWS Migration Assistant — Phase 0 Scaffold

Agentic AI–powered migration assistant that turns Azure Bicep (Key Vault,
Functions, Virtual Network) into validated, deployable AWS CloudFormation.

This is the **Phase 0** scaffold: repo structure, the Migration Spec
contract, the RAG knowledge base schema, CI, and a LangGraph skeleton with
every agent stubbed out so the two branches (`charan` = source pipeline,
`saurav` = target pipeline) can build in parallel starting Phase 1.

## Branch model

| Branch | Owner | Focus |
|---|---|---|
| `charan` | Person A | Discovery, Bicep parsing, RAG mapping, planning/risk, approval UI |
| `saurav` | Person B | CFN generation, static validation, deployment, post-deploy validation |
| `develop` / `main` | Joint | Integration merge points |

See `CODEOWNERS` for the file-level ownership map, and
`team-work-split-plan.md` for the phase-by-phase plan.

## What's in this scaffold

- **`src/migration_assistant/graph/state.py`** — the **Migration Spec**: the
  one shared contract both branches build against. Pydantic models
  (`MigrationSpec`, `SourceResource`, `TargetResource`, `MappingRecord`,
  `RiskAssessment`, `ApprovalDecision`, `ValidationResult`) plus the
  `GraphState` TypedDict LangGraph actually threads through the graph.
  **Treat this file as frozen after Phase 0** — changes need review from
  both of you (see `docs/migration_spec_schema.md`).
- **`src/migration_assistant/graph/workflow.py`** — the LangGraph skeleton.
  Compiles and runs end-to-end today with every agent stubbed out.
- **`src/migration_assistant/agents/`** — one module per agent from the
  design doc, each exposing `run(state) -> dict`. Currently stubs; ownership
  is marked in each file's docstring and in `CODEOWNERS`.
- **`knowledge_base/schema/pgvector_schema.sql`** — the RAG knowledge base
  schema (mapping rules, RBAC↔IAM mappings, trigger mappings,
  incompatibilities, region mappings, issue log).
- **`.github/workflows/ci.yml`** — lint (ruff) + type check (mypy) + tests,
  running on `main`, `develop`, `charan`, and `saurav`.
- **`config/`** — naming/tagging conventions and Azure↔AWS region mapping,
  agreed jointly.
- **`scripts/provision_sandbox.md`** + **`scripts/bootstrap_sandbox.sh`** —
  checklist and starter CLI commands for setting up sandbox Azure/AWS
  accounts. Run these locally, not in CI — they need your own credentials.

## Setup

```bash
git clone <your-repo-url> && cd azure-aws-migration-assistant
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
cp .env.example .env   # fill in once sandbox accounts exist — see scripts/provision_sandbox.md
docker compose up -d postgres   # local pgvector instance; schema auto-loads
```

## Verify the Phase 0 scaffold works

```bash
pytest -v                                      # schema + graph skeleton tests
python -m migration_assistant.graph.workflow   # smoke-test the full stub pipeline
ruff check src tests knowledge_base
mypy src
```

You should see the smoke test print `Final status: MigrationStatus.VERIFIED`
— that's the whole graph running end-to-end on stubs, all the way through
deploy and post-deploy validation. That's the Phase 0 exit criterion:
**the skeleton runs, the contract is agreed, now go build Phase 1 on your
own branch.**

## Phase 0 exit checklist

See `docs/phase0_checklist.md`.
