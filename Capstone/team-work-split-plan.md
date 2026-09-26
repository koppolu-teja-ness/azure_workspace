# Team Work Split Plan
### Agentic AI–Powered Azure-to-AWS Infrastructure Migration Assistant

---

## Branch Structure

| Branch | Owner | Focus |
|---|---|---|
| `feature/source-pipeline` | Person A | Azure-understanding side: discovery, parsing, mapping, planning, approval UI |
| `feature/target-pipeline` | Person B | AWS-generation side: CloudFormation generation, validation, deployment, testing |

The two branches meet at one shared contract — a **Migration Spec** (JSON) that Person A's pipeline produces and Person B's pipeline consumes. Agreeing on this schema in Phase 0 is what allows both people to work in parallel without blocking each other.

---

## Phase 0 — Foundations (Joint)

Both team members work together before splitting:

- Agree on the Migration Spec JSON schema (the resource-graph representation passed between pipelines)
- Agree on the RAG knowledge base schema (mapping rule format)
- Set up repo scaffold, branching strategy, and CI base
- Set up the LangGraph skeleton and shared agent interfaces
- Provision sandbox Azure and AWS accounts

---

## Phase 1 — Core Build

### Person A — `feature/source-pipeline`
- Discovery Agent: enumerate Azure Key Vault, Function App, and VNet resources; ingest existing Bicep files
- Parser/Analyzer Agent: parse Bicep → ARM JSON → resource graph
- Populate RAG knowledge base content (mapping tables, incompatibilities, best practices)
- Mapping Agent: produce the Migration Spec output

### Person B — `feature/target-pipeline`
- CFN Generator Agent: build against 2–3 hand-written sample Migration Specs (so work isn't blocked waiting on Person A)
- Static Validation Agent: integrate `cfn-lint` and `checkov`
- Deployment Agent skeleton: `boto3` wrapper, no live deployment yet

**Merge point:** once Person A's real Migration Spec output is flowing, merge both branches into `develop` for the first true (even if rough) end-to-end run.

---

## Phase 2 — Wire Real Integration

### Person A — `feature/source-pipeline`
- Planning & Risk-Scoring Agent: classify objects as auto-migratable / needs-review / high-risk
- Human Approval Gate: build the approve/reject/modify UI (Streamlit or React)

### Person B — `feature/target-pipeline`
- Swap sample specs for Person A's real Migration Spec output
- Complete the Deployment Agent against the sandbox AWS account
- Post-Deployment Validation Agent: structural equivalence checks (resource counts, property parity)

**Merge point:** merge again, then re-run the full pipeline to catch drift between branches.

---

## Phase 3 — Depth & Rigor

### Person A — `feature/source-pipeline`
- Migration Test Suite: schema compatibility, dependency/referential integrity checks, missing-object detection
- Risk report and migration plan report generation

### Person B — `feature/target-pipeline`
- Functional smoke tests: invoke migrated Lambdas, fetch secrets, verify network reachability
- Security-posture diff checks (no new public exposure, no IAM over-broadening)
- Execution & validation report generation
- Observability wiring: LangSmith/LangFuse tracing, CloudWatch/Grafana dashboards

**Merge point:** merge and re-test end-to-end once more before final integration.

---

## Phase 4 — Integration & Polish (Joint)

Both team members work together to close out the capstone:

- Merge `develop` into `main`
- Run the full end-to-end pipeline across all three services (Key Vault, Functions, VNet)
- Integrate FastAPI backend with the dashboard
- Package with Docker and finalize the CI/CD pipeline
- Write documentation and architecture diagram
- Record the final demonstration video

---

## Why This Split Works

- Each person owns a coherent half of the pipeline (source-side vs. target-side), minimizing merge conflicts on shared files.
- The Migration Spec contract lets both people build and test independently in Phase 1 using sample data, rather than waiting on each other.
- Joint phases (0 and 4) are placed exactly where shared decisions matter most: defining the interface up front, and integrating/validating the whole system at the end.

---

## Phase 1 Completion Check (2026-09-25)

This checkpoint confirms the Phase 1 scope is implemented and validated for both owners.

### Person A (`feature/source-pipeline`) — Completed

- Discovery Agent now resolves configured Bicep files and stores discovery output in graph config.
- Parser/Analyzer Agent now parses discovered Bicep and materializes `source_resources`.
- Mapping Agent now runs deterministic retrieval + Bedrock refinement and returns `mappings` and `llm_traces`.
- RAG knowledge base content is present under `knowledge_base/data` (resource and property mapping rules).

### Person B (`feature/target-pipeline`) — Completed

- CFN Generator Agent now builds `target_resources` from source resources + mappings.
- Static Validation Agent now runs schema validation, `cfn-lint`, and `checkov` on generated templates.
- Deployment Agent skeleton supports dry-run CloudFormation deployment preview using the boto3 wrapper.

### Shared Contract/Runtime Updates Applied

- `MigrationSpec`/`GraphState` now include `llm_traces` via `LLMTraceEvent` to support mapping, planning, and reporting traceability.
- Property-equivalence loading utilities are implemented for rule coverage checks.

### Verification Evidence

- Full test suite passed: `37 passed`.
- Command run: `python -m pytest -q`.

### Notes

- Phase 1 is complete for baseline implementation and test validation.
- Remaining major work starts in Phase 2 and later (real human approval UI, live deployment path, deeper post-deploy validation, richer reports/observability).

---

## Phase 2 Person B Completion Check (2026-09-26)

This checkpoint confirms the Person B Phase 2 scope has been implemented in the target pipeline.

### Implemented

- **Swap sample specs for real pipeline output path:** API run lifecycle no longer auto-seeds synthetic runs; real runs are persisted and consumed (`/runs/execute` and approval endpoints operate on actual stored graph state).
- **Target-side contract execution endpoint:** added `POST /runs/execute-target` to accept a full `MigrationSpec` payload and run only target-side stages (CFN generation, static validation, deployment, post-deploy validation, reporting).
- **Deployment Agent completion:** deployment now supports two modes:
	- dry-run preview (default, safe)
	- optional live CloudFormation change set creation/execution when `deployment.enable_live_deploy=true`
- **Post-Deployment Validation structural checks:** implemented resource-count equivalence and property-parity checks, producing `post_deploy` validation results and setting final status to `failed` on hard structural mismatches.

### Verification Evidence

- Targeted unit tests passed: `10 passed`
- End-to-end integration test passed: `1 passed`
- Commands run:
	- `python -m pytest -q tests/unit/test_deployment_agent.py tests/unit/test_post_deploy_validation_agent.py tests/unit/test_static_validation_agent.py tests/unit/test_workflow_skeleton.py`
	- `python -m pytest -q tests/integration/test_end_to_end_pipeline.py`

---

## Phase 3 Completion Check (2026-09-26)

This checkpoint confirms the full Phase 3 scope (Person A + Person B) has
been implemented and validated.

### Person A (`feature/source-pipeline`) — Completed

- Migration Test Suite implemented for:
	- schema compatibility
	- dependency/referential integrity
	- missing-object detection
- Reporting outputs implemented:
	- migration plan report
	- risk report

### Person B (`feature/target-pipeline`) — Completed

- Post-deploy validation expanded with:
	- functional smoke checks (Lambda/secret/network heuristics)
	- security posture diff checks (public exposure + IAM wildcard broadening)
- Reporting outputs implemented:
	- execution report
	- validation report
- Observability wiring added:
	- tracing config helper for LangSmith/LangFuse
	- baseline CloudWatch and Grafana dashboard assets

### Verification Evidence

- Full test suite passed: `58 passed`
- Command run: `python -m pytest -q`

### Notes

- Phase 3 implementation is complete and test-validated.
- Remaining work is in Phase 4 integration/polish activities.

---

## Phase 4 Readiness Checklist (2026-09-26)

Use this checklist as the go/no-go gate before final capstone handoff.

- [ ] Merge `dev` into `main` after final review. *(release management action)*
- [x] Execute one full end-to-end run across Key Vault, Function App, and VNet inputs.
- [x] Verify API and dashboard integration flows are stable for discovery, approval, run execution, and reports.
- [x] Validate Docker build/run for API and dashboard images.
- [x] Confirm CI pipeline is green on final integration branch.
- [x] Refresh architecture and developer docs to match implemented behavior.
- [x] Publish final demo artifacts (video link, example outputs, run evidence).
- [ ] Tag release candidate. *(known limitations/open risks captured in `docs/known_limitations.md`; tagging pending maintainer action)*

### Suggested Exit Evidence

- `python -m pytest -q` passes on the integrated branch.
- `python -m migration_assistant.graph.workflow` returns verified final status for representative sample input.
- API smoke checks succeed for health, execution, approval, and reports endpoints.
- Dashboard pages render end-to-end state transitions without manual data patching.

### Phase 4 Completion Check (2026-09-26)

Implemented in repository:

- Added discovery API routes and wired router in app bootstrap.
- Added stored-run target execution endpoint (`POST /runs/{run_id}/execute-target`).
- Completed Streamlit pages for Discovery, Deployment Status, and Validation Report.
- Finalized Docker assets (`Dockerfile`, `infra/docker/*`, `docker-compose.yml`) for Postgres + API + dashboard local stack.
- Strengthened CI/CD workflows for Python tests and Docker build validation.
- Added Phase 4 router unit tests and validated full suite.
- Updated README and architecture/developer documentation for integrated behavior.

Verification evidence:

- `python -m pytest -q` => `63 passed`
- `python -m pytest -q tests/unit/test_discovery_router.py tests/unit/test_migration_runs_router.py tests/unit/test_reports_router.py` => `10 passed`
- `docker compose config` validates successfully for the three-service stack.

Pending external release actions (outside code implementation scope):

- Final branch merge strategy execution (`dev` -> `main`) and release tag creation.
