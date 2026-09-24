# Phase 0 Foundations Checklist
### Agentic AI-Powered Azure-to-AWS Migration Assistant

Purpose: finish all shared decisions and baseline setup before splitting into `feature/source-pipeline` and `feature/target-pipeline`.

Date baseline: 2026-09-24

---

## 1) Ownership and Timeline

| ID | Work Item | Owner | Target Date | Status |
|---|---|---|---|---|
| P0-01 | Migration Spec schema v1.0.0 finalized | Joint (A+B) | 2026-09-26 | Not Started |
| P0-02 | Migration Spec fixtures (happy path, edge, unsupported) | Joint (A+B) | 2026-09-27 | Not Started |
| P0-03 | RAG rule schema finalized | Joint (A+B) | 2026-09-27 | Not Started |
| P0-04 | Seed mapping rules authored (minimum 10) | Person A | 2026-09-28 | Not Started |
| P0-05 | Contract tests for producer/consumer integration | Joint (A+B) | 2026-09-29 | Not Started |
| P0-06 | LangGraph typed interfaces and node I/O contracts | Joint (A+B) | 2026-09-29 | Not Started |
| P0-07 | CI baseline with schema + contract gates | Person B | 2026-09-30 | Not Started |
| P0-08 | Security baseline: secret-handling and logging policy | Joint (A+B) | 2026-09-30 | Not Started |
| P0-09 | Sandbox cloud access + least-privilege roles validated | Joint (A+B) | 2026-10-01 | Not Started |
| P0-10 | Local dev bootstrap and pinned tool versions | Person B | 2026-10-01 | Not Started |
| P0-11 | Risk taxonomy + scoring rubric approved | Person A | 2026-10-01 | Not Started |
| P0-12 | Phase 0 dry run on fixture data + sign-off | Joint (A+B) | 2026-10-02 | Not Started |

---

## 2) Detailed Checklist with Acceptance Tests

## P0-01 Migration Spec schema v1.0.0
- Tasks
  - Define JSON Schema with required top-level fields:
    - `specVersion`, `source`, `target`, `resources`, `dependencies`, `risk`, `validationHints`, `traceability`
  - Define strict enums for migration decisions:
    - `auto-migratable`, `needs-review`, `high-risk`
  - Define versioning rule:
    - reject unknown major version, warn on unknown minor fields
- Deliverables
  - `schemas/migration-spec/v1.0.0.schema.json`
- Acceptance tests
  - 3 valid spec files pass schema validation.
  - 3 intentionally invalid spec files fail with clear error messages.
  - Consumer side fails fast for unsupported major version.

## P0-02 Migration Spec fixtures
- Tasks
  - Create canonical fixtures:
    - happy path
    - security edge case (broad access/public endpoint)
    - unsupported construct case
- Deliverables
  - `fixtures/specs/happy-path.json`
  - `fixtures/specs/security-edge.json`
  - `fixtures/specs/unsupported-construct.json`
- Acceptance tests
  - All fixtures validate against `v1.0.0` schema.
  - Target pipeline can parse all 3 fixtures without runtime exceptions.

## P0-03 RAG rule schema
- Tasks
  - Define structured rule format fields:
    - `azureResourceType`, `awsResourceType`, `propertyMappings`, `preconditions`, `securityConstraints`, `knownIncompatibilities`, `fallbackStrategy`, `confidenceScore`, `citations`, `mappingQuality`
  - Restrict `mappingQuality` to:
    - `exact`, `approximate`, `manual-required`
- Deliverables
  - `schemas/rag-rules/v1.0.0.schema.json`
- Acceptance tests
  - Rule linter rejects missing required fields.
  - Rule linter rejects invalid `mappingQuality` values.

## P0-04 Seed mapping rules (minimum 10)
- Tasks
  - Add seed rules across Key Vault, Functions, and VNet coverage.
  - Add at least one known incompatibility and fallback strategy per service area.
- Deliverables
  - `knowledgebase/rules/*.yaml`
- Acceptance tests
  - At least 10 rules pass schema lint.
  - At least 2 rules per service area (Key Vault, Functions, VNet).

## P0-05 Producer/consumer contract tests
- Tasks
  - Build tests that validate:
    - source pipeline output is schema-compliant
    - target pipeline consumes spec and produces deterministic intermediate output
  - Add compatibility tests for optional/new fields.
- Deliverables
  - `tests/contract/test_migration_spec_contract.*`
- Acceptance tests
  - CI fails when source output breaks contract.
  - CI fails when target parser behavior regresses on baseline fixtures.

## P0-06 LangGraph interface contracts
- Tasks
  - Define typed node input/output models (Pydantic or equivalent):
    - `DiscoveryOutput`, `AnalysisOutput`, `MappingOutput`, `GenerationOutput`
  - Freeze these interfaces for Phase 1 (change only through ADR).
- Deliverables
  - `src/shared/contracts/*.py` (or equivalent language path)
- Acceptance tests
  - Static type checks pass.
  - Serialization/deserialization round-trip tests pass.

## P0-07 CI baseline and quality gates
- Tasks
  - Add pipeline stages:
    - lint
    - unit tests
    - schema validation (spec + rules)
    - contract tests
  - Protect `develop` with required status checks.
- Deliverables
  - `.github/workflows/ci.yml`
- Acceptance tests
  - Pull request to `develop` is blocked if any gate fails.
  - CI reports include explicit pass/fail for each gate category.

## P0-08 Security baseline
- Tasks
  - Document and enforce policy:
    - no secret values in prompts, logs, traces, or fixtures
  - Add scanning for leaked secrets in repository and CI logs.
- Deliverables
  - `docs/security-baseline.md`
  - CI secret scan step in workflow
- Acceptance tests
  - Seeded test secret in test branch is detected and fails CI.
  - Runtime logs redact secret-like fields.

## P0-09 Sandbox access validation
- Tasks
  - Validate both team members can access required Azure and AWS sandboxes.
  - Create minimum IAM/RBAC roles for discovery and deployment testing.
- Deliverables
  - `docs/sandbox-access.md`
- Acceptance tests
  - Documented smoke commands run successfully for both team members.
  - Access denied events are reviewed and least-privilege policy is updated.

## P0-10 Dev bootstrap and tool version pinning
- Tasks
  - Provide one-command setup script for local environment.
  - Pin versions for `az`, Bicep, Python, `cfn-lint`, `checkov`.
- Deliverables
  - `scripts/bootstrap.ps1` (or equivalent)
  - `docs/dev-setup.md`
- Acceptance tests
  - Clean machine setup completes using documented steps.
  - `--version` checks match pinned versions.

## P0-11 Risk taxonomy and scoring rubric
- Tasks
  - Define weighted scoring dimensions:
    - identity exposure
    - network exposure
    - unsupported mapping risk
    - blast radius
  - Set score thresholds for:
    - auto-migratable, needs-review, high-risk
- Deliverables
  - `config/risk-rubric.yaml`
  - `docs/risk-model.md`
- Acceptance tests
  - 5 sample scenarios are scored consistently by both team members.
  - Threshold boundaries are validated by unit tests.

## P0-12 Phase 0 dry run and sign-off
- Tasks
  - Run end-to-end dry workflow on fixture specs:
    - parse -> map -> generate -> lint/policy scan -> risk classify
  - Record open issues and assign owners before branch split.
- Deliverables
  - `reports/phase-0-dry-run.md`
  - Signed Phase 0 completion checklist
- Acceptance tests
  - All P0 acceptance tests are green.
  - No blocker-severity open issue remains.

---

## 3) Mandatory Exit Criteria (Go/No-Go)

Phase 1 branch split is allowed only if all conditions below are met:
- Migration Spec schema v1 is approved and enforced in CI.
- At least 3 canonical fixtures exist and pass validation.
- RAG rule schema is finalized and at least 10 rules are valid.
- Producer/consumer contract tests are passing.
- CI gates protect `develop`.
- Security baseline is documented and tested.
- Sandbox access is verified for both team members.
- Risk rubric is finalized and unit-tested.
- Phase 0 dry run report is completed with no blocker issues.

---

## 4) Suggested Daily Cadence (Phase 0)

- 15-minute stand-up:
  - schema/rules changes
  - integration blockers
  - security concerns
- End-of-day checkpoint:
  - fixture updates
  - CI gate status
  - unresolved decisions requiring ADR

---

## 5) ADRs to Create in Phase 0

- ADR-001: Migration Spec versioning strategy
- ADR-002: RAG rule schema and mapping quality taxonomy
- ADR-003: Risk scoring model and thresholds
- ADR-004: Secret-handling and redaction policy
- ADR-005: CI gate policy for `develop`

Recommended ADR location:
- `docs/adr/`
