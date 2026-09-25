# Mapping Rules Reference

This document describes where Azure-to-AWS mapping knowledge is stored and
how it is used by the mapping stage.

## Rule Sources

Primary knowledge assets live under `knowledge_base/data/`:

- `resource_type_mappings.json`: Azure resource type -> AWS resource type
	mappings.
- `property_mappings/`: per-resource property translation rules.
- `rbac_to_iam_rules.json`: permission model mappings.
- `trigger_mappings.json`: event/trigger mapping references.
- `known_incompatibilities.md`: migration caveats and unsupported patterns.
- `issue_log.jsonl`: observed migration issues and notes.

## Retriever Behavior

The mapping workflow uses `RuleBasedMappingRetriever` in
`src/migration_assistant/mapping/rag_retriever.py`.

Selection strategy is designed as:

1. Deterministic rule lookup by Azure resource type.
2. Optional vector similarity retrieval when embeddings and pgvector are
	 configured.
3. Fallback to deterministic selection when vector retrieval is unavailable.

## Confidence and Notes

`MappingRecord` includes:

- `mapping_rule_id` for traceability.
- `confidence` to support risk scoring and approval decisions.
- `notes` and `unmapped_properties` to flag manual follow-up.

## Updating Rules Safely

- Keep mapping data changes in small PRs with fixture updates.
- Add or update unit tests under `tests/unit/test_mapping_agent.py` and
	related parser/generation tests when rule behavior changes.
- Validate with sample inputs in `tests/fixtures/sample_bicep/` and inspect
	generated outputs in `examples/sample_migration_run/`.

