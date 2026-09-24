# ADR-005: CI Gate Policy for develop

## Status
Accepted

## Decision
Required checks on `develop`:
- lint
- schema_validation
- contract_tests
- secret_scan

## Consequences
- Producer/consumer compatibility regressions are blocked before merge.
- Security and quality controls are enforced consistently across both feature branches.

## Implementation note
Branch protection must be enabled in GitHub repository settings to enforce these required checks.
Detailed setup steps are documented in `docs/branch-protection-checklist.md`.
