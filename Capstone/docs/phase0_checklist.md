# Phase 0 — Exit Checklist

Both of you should be able to check every box before starting Phase 1.

- [ ] `MigrationSpec` schema in `src/migration_assistant/graph/state.py`
      reviewed and agreed by both of you — this is the contract your two
      branches build against.
- [ ] `knowledge_base/schema/pgvector_schema.sql` reviewed and agreed.
- [ ] Repo cloned; `pip install -e .` + `pip install -r requirements-dev.txt`
      works for both of you.
- [ ] `docker compose up -d postgres` works locally for both of you, and
      the schema loads without error.
- [ ] `pytest -v` passes for both of you.
- [ ] `python -m migration_assistant.graph.workflow` runs end-to-end and
      prints `Final status: MigrationStatus.VERIFIED` for both of you.
- [ ] CI (`.github/workflows/ci.yml`) is green on a throwaway PR.
- [ ] `charan` and `saurav` branches created off `develop`.
- [ ] `CODEOWNERS` reviewed — both agree who owns what.
- [ ] Sandbox Azure subscription + service principal created
      (`scripts/provision_sandbox.md`).
- [ ] Sandbox AWS account + scoped deployment role created
      (`scripts/provision_sandbox.md`).
- [ ] `config/region_mapping.yaml` filled in for your actual sandbox regions.
- [ ] `config/settings.yaml` naming/tagging conventions agreed.

Once every box is checked, move to Phase 1 per `team-work-split-plan.md`.
