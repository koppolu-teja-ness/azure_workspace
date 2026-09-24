# Team Work Split Plan
### Agentic AI–Powered Azure-to-AWS Infrastructure Migration Assistant

---

## Branch Structure

| Branch | Owner | Focus |
|---|---|---|
| `feature/source-pipeline` | Person A (`koppolu-teja-ness`) | Azure-understanding side: discovery, parsing, mapping, planning, approval UI |
| `feature/target-pipeline` | Person B (`saurav-das-ness`) | AWS-generation side: CloudFormation generation, validation, deployment, testing |

The two branches meet at one shared contract — a **Migration Spec** (JSON) that Person A's pipeline produces and Person B's pipeline consumes. Agreeing on this schema in Phase 0 is what allows both people to work in parallel without blocking each other.

---

## Phase 0 — Foundations (Ownership Split)

### Person A (`koppolu-teja-ness`) (Azure-only focus)
- Define Azure-side source representation in the Migration Spec JSON schema.
- Define Azure-side mapping requirements and edge cases in the RAG rule schema.
- Provision and validate Azure sandbox access and discovery permissions.
- Validate Azure-related fixture realism for Key Vault, Functions, and VNet inputs.

### Person B (`saurav-das-ness`) (AWS-only focus)
- Define AWS-side target representation and consumer expectations in the Migration Spec JSON schema.
- Define AWS-side mapping quality and generation constraints in the RAG rule schema.
- Set up CI baseline, schema/contract gates, and AWS-oriented validation tooling.
- Provision and validate AWS sandbox access and deployment permissions.

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

## Phase 4 — Integration & Polish (Ownership Split)

### Person A (`koppolu-teja-ness`) (Azure-only focus)
- Validate Azure discovery completeness and Azure-to-spec traceability before final merge.
- Finalize source-side documentation for Azure assumptions and unsupported constructs.
- Support end-to-end validation only for Azure source correctness and parity inputs.

### Person B (`saurav-das-ness`) (AWS-only focus)
- Merge `develop` into `main` after required CI checks pass.
- Run AWS-side generation, deployment, and validation for all in-scope services.
- Finalize Docker/CI-CD packaging and target-side runtime checks.
- Finalize deployment, validation, and operations documentation for AWS outputs.

---

## Why This Split Works

- Each person owns a coherent half of the pipeline (source-side vs. target-side), minimizing merge conflicts on shared files.
- The Migration Spec contract lets both people build and test independently in Phase 1 using sample data, rather than waiting on each other.
- Phase ownership remains stable from start to finish: Person A handles Azure concerns, Person B handles AWS concerns.
