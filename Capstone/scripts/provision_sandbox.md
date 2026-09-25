# Phase 0 — Sandbox Account Provisioning Checklist

This step needs to happen outside this repo/chat, since it requires each of
your own cloud credentials. Do this once, jointly, before Phase 1 starts.

## Azure sandbox

- [ ] Create (or get access to) a dedicated Azure subscription/resource
      group for this project — do not point discovery/deployment at a
      production subscription.
- [ ] Create a read-only service principal for the Discovery Agent:
      `az ad sp create-for-rbac --name migration-assistant-discovery --role Reader --scopes /subscriptions/<SUBSCRIPTION_ID>`
- [ ] Record `appId`, `password`, `tenant` into `.env` as `AZURE_CLIENT_ID`,
      `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`.
- [ ] Confirm `az bicep version` works locally (needed by the Bicep parser
      in Phase 1).

## AWS sandbox

- [ ] Create (or get access to) a dedicated AWS account or isolated OU for
      this project.
- [ ] Create an IAM role/user for the Deployment Agent scoped to only the
      services in scope: CloudFormation, Secrets Manager, KMS, ACM, Lambda,
      API Gateway, EventBridge, S3 (event notifications only), SQS, VPC,
      IAM (role creation, scoped).
- [ ] Do **not** grant `AdministratorAccess`, even in a sandbox — the whole
      point of the capstone's risk scoring is undermined if the deploying
      identity itself is over-permissioned.
- [ ] Record credentials as an AWS CLI profile (`AWS_PROFILE` in `.env`),
      not raw access keys committed anywhere in the repo.

## Shared

- [ ] Agree on the Azure region <-> AWS region mapping for your sandbox
      accounts and fill in `config/region_mapping.yaml`.
- [ ] Confirm both of you can run `docker compose up -d postgres` locally
      and connect to it (this is the knowledge base sandbox).
- [ ] Confirm both of you can run the LangGraph smoke test:
      `python -m migration_assistant.graph.workflow`

See `scripts/bootstrap_sandbox.sh` for starter CLI commands for the steps
above — run it locally after `az login` / `aws configure`, not in CI, and
review the generated IAM policy before attaching it to anything.
