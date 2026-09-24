# ADR-002: RAG Rule Schema and Mapping Quality Taxonomy

## Status
Accepted

## Decision
- RAG rules must conform to `schemas/rag-rules/v1.0.0.schema.json`.
- `mappingQuality` allowed values are `exact`, `approximate`, and `manual-required`.
- Each rule must include incompatibilities, fallback strategy, and citations.

## Consequences
- Mapping quality is explicit and auditable.
- Unsupported or risky mappings are surfaced early in planning.
