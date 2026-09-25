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
