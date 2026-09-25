# Migration Spec — Schema Reference

`MigrationSpec` (in `src/migration_assistant/graph/state.py`) is the
contract between the source pipeline (`charan`) and target pipeline
(`saurav`). Dump the live JSON Schema any time with:

```bash
python -c "from migration_assistant.graph.state import MigrationSpec; import json; print(json.dumps(MigrationSpec().to_json_schema(), indent=2))"
```

## Top-level fields

| Field | Type | Produced by |
|---|---|---|
| `run_id` | `str` | generated at run start |
| `source_resources` | `list[SourceResource]` | Discovery + Parser/Analyzer agents |
| `target_resources` | `list[TargetResource]` | CFN Generator agent |
| `mappings` | `list[MappingRecord]` | Mapping agent |
| `risk_assessments` | `list[RiskAssessment]` | Planning & Risk-Scoring agent |
| `approval` | `ApprovalDecision` | Human Approval Gate |
| `validation_results` | `list[ValidationResult]` | Static + Post-Deploy Validation agents |
| `status` | `MigrationStatus` | updated by whichever agent runs last |
| `config` | `dict` | loaded from `config/settings.yaml` + `region_mapping.yaml` at run start |

## Changing this schema

This file is joint-owned (see `CODEOWNERS`). After Phase 0 sign-off, any
change to `SourceResource`, `TargetResource`, `MappingRecord`,
`RiskAssessment`, `ApprovalDecision`, or `ValidationResult` should be its own
small PR reviewed by both of you before either branch builds against the
new shape — a silent shape change on one branch is exactly the kind of
thing that causes a broken merge in Phase 1/2.
