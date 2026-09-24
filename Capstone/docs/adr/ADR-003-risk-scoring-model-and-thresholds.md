# ADR-003: Risk Scoring Model and Thresholds

## Status
Accepted

## Decision
- Use weighted dimensions: identity exposure, network exposure, unsupported mapping risk, blast radius.
- Weights and thresholds are source-controlled in `config/risk-rubric.yaml`.
- Classifications are mapped to `auto-migratable`, `needs-review`, and `high-risk`.

## Consequences
- Risk classification is deterministic and testable.
- Threshold tuning can be reviewed through pull requests and test updates.
