# Risk Scoring Model

## Dimensions
- identityExposure
- networkExposure
- unsupportedMappingRisk
- blastRadius

Each dimension is scored from 0 to 100.

## Weights
Defined in `config/risk-rubric.yaml`:
- identityExposure: 0.30
- networkExposure: 0.30
- unsupportedMappingRisk: 0.25
- blastRadius: 0.15

The weighted score is:

score = identityExposure*0.30 + networkExposure*0.30 + unsupportedMappingRisk*0.25 + blastRadius*0.15

## Classification thresholds
- auto-migratable: score <= 30.0
- needs-review: score <= 65.0
- high-risk: score > 65.0

## Test coverage
- Boundary behavior validated in `tests/contract/test_risk_rubric.py`.
- Five sample scenarios are evaluated for deterministic scoring consistency.
