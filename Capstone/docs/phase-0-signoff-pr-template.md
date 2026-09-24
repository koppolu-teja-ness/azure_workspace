# Phase 0 Sign-off PR Template

## Title
Phase 0 Foundations Sign-off: schema, contracts, CI gates, and security baseline

## Summary
This PR requests Phase 0 sign-off for the Agentic AI-powered Azure-to-AWS Migration Assistant.

Scope covered:
- Migration Spec schema and canonical fixtures
- RAG rule schema and seed mappings
- Producer/consumer contracts and typed interfaces
- CI baseline and secret scan gate
- Security baseline, risk rubric, and ADR set
- Dry run report and operational follow-ups

## Owners
- Person A: koppolu-teja-ness
- Person B: saurav-das-ness

## Required checks
- [ ] lint
- [ ] schema_validation
- [ ] contract_tests
- [ ] secret_scan

## Phase 0 deliverables checklist
- [ ] Migration Spec schema v1 approved and enforced in CI
- [ ] At least 3 canonical fixtures exist and pass validation
- [ ] RAG rule schema finalized and at least 10 rules valid
- [ ] Producer/consumer contract tests passing
- [ ] CI gates defined for develop
- [ ] Security baseline documented and tested
- [ ] Sandbox access verified for both team members
- [ ] Risk rubric finalized and unit-tested
- [ ] Dry run report completed with no blocker issues

## Evidence links
- Checklist baseline: [phase-0-foundations-checklist.md](phase-0-foundations-checklist.md)
- Migration spec schema: [schemas/migration-spec/v1.0.0.schema.json](schemas/migration-spec/v1.0.0.schema.json)
- RAG rule schema: [schemas/rag-rules/v1.0.0.schema.json](schemas/rag-rules/v1.0.0.schema.json)
- Canonical fixtures folder: [fixtures/specs](fixtures/specs)
- Rules folder: [knowledgebase/rules](knowledgebase/rules)
- Shared contracts: [src/shared/contracts](src/shared/contracts)
- CI workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- Security baseline: [docs/security-baseline.md](docs/security-baseline.md)
- Sandbox access: [docs/sandbox-access.md](docs/sandbox-access.md)
- Risk model: [docs/risk-model.md](docs/risk-model.md)
- Branch protection checklist: [docs/branch-protection-checklist.md](docs/branch-protection-checklist.md)
- Dry run report: [reports/phase-0-dry-run.md](reports/phase-0-dry-run.md)

## Live identity validation
Person A values captured:
- Azure subscriptionId: REDACTED_AZURE_SUBSCRIPTION_ID
- Azure tenantId: REDACTED_AZURE_TENANT_ID
- AWS accountId: REDACTED_AWS_ACCOUNT_ID
- AWS ARN: REDACTED_AWS_CALLER_ARN

Person B pending values to add:
- Azure subscriptionId
- Azure tenantId
- AWS accountId
- AWS ARN

If Person B has no Azure account yet:
- Use temporary fallback documented in `docs/sandbox-access.md`.
- Person A runs Azure discovery/export steps and commits non-secret artifacts.
- Person B continues AWS-side work and CI using those artifacts.

## Open operational items before final merge
- [ ] Person B runs sandbox identity commands and updates sandbox record (or fallback is documented with target end date)
- [ ] Branch protection enabled on develop with required checks

## Risk and blocker declaration
- [ ] No blocker-severity open issue remains
- [ ] Known limitations are documented and accepted for Phase 1

## Reviewer sign-off
- [ ] Person A approves
- [ ] Person B approves
- [ ] Joint sign-off complete
