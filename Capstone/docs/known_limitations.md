# Known Limitations And Open Risks

Updated: 2026-09-26

## Current Limitations

- Live CloudFormation deployment is disabled by default and requires explicit runtime configuration.
- Some resource/property mappings are intentionally conservative and may route to review/modify paths.
- In-memory API run storage is suitable for capstone/demo usage but not durable production persistence.
- Full cloud-side functional validation depends on accessible sandbox credentials and network reachability.

## Operational Risks

- Release branch merge and version tagging are still manual maintainer actions.
- CI validates code and packaging, but environment-specific AWS/Azure credentials are external dependencies.

## Recommended Next Hardening Steps

1. Persist run state in a durable datastore (e.g., Postgres) for multi-session review.
2. Add authenticated API access for approval and run execution endpoints.
3. Add gated live-deploy integration tests against dedicated sandbox stacks.
