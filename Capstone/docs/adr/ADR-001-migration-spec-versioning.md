# ADR-001: Migration Spec Versioning Strategy

## Status
Accepted

## Decision
- `specVersion` follows semantic versioning `MAJOR.MINOR.PATCH`.
- Consumer rejects unsupported major versions.
- Minor and patch updates must preserve backwards compatibility.
- Producer and consumer are contract-tested against canonical fixtures.

## Consequences
- Breaking schema changes require a new major version and coordinated rollout.
- Teams can evolve non-breaking fields safely while keeping CI contract gates green.
