# Known Limitations And Open Risks

Updated: 2026-09-27

## Current Limitations

- Live CloudFormation deployment is disabled by default and requires explicit runtime configuration.
- Some resource/property mappings are intentionally conservative and may route to review/modify paths.
- Workflow execution requires valid Bedrock configuration (`llm.enabled=true`, `llm.provider=aws_bedrock`, `llm.bedrock.model_id` set).
- Full cloud-side functional validation depends on accessible sandbox credentials and network reachability.

## Operational Risks

- Release branch merge and version tagging are still manual maintainer actions.
- CI validates code and packaging, but environment-specific AWS/Azure credentials are external dependencies.

## Recommended Next Hardening Steps

1. Add authenticated API access for approval and run execution endpoints.
2. Add gated live-deploy integration tests against dedicated sandbox stacks.
3. Expand functional post-deploy checks from surrogate local checks to cloud API-backed assertions.
