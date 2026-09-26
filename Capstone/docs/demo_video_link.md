# Demo Video Link

## Current Status

Phase 4 implementation artifacts are now committed, including API/dashboard
integration, Docker stack assets, and run/report examples.

Video recording link is pending publication by the project maintainers.

## Phase 4 Evidence Artifacts

- Example outputs: `examples/sample_migration_run/`
- Run evidence summary: `examples/sample_migration_run/phase4_run_evidence.md`
- Known limitations/open risks: `docs/known_limitations.md`

## How To Record a Fresh Demo

Suggested walkthrough order:

1. Start local dependencies (`docker compose up -d postgres`).
2. Run the workflow smoke test (`python -m migration_assistant.graph.workflow`).
3. Show generated sample artifacts in `examples/sample_migration_run/`.
4. Optionally show API/dashboard surfaces if available in your branch.

## Team Update Convention

When a new recording is available, update this file with:

- Video URL
- Recording date
- Commit SHA or branch used in the demo
- Short changelog of what the demo validates

