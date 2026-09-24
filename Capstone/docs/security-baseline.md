# Security Baseline

## Policy
- No secret values in prompts, logs, traces, or fixture files.
- Redact secret-like fields before structured logging.
- Treat sample fixture values as non-sensitive metadata only.

## Enforcement
- Runtime redaction helper implemented in `src/shared/security.py`.
- Redaction behavior tested in `tests/contract/test_security_redaction.py`.
- CI includes a secret scan gate (`gitleaks`) on every push/PR.

## Logging guidance
- Log only resource identifiers and migration decision metadata.
- Never log Key Vault secret values, connection strings, private keys, API tokens, or IAM access keys.
- Apply redaction recursively to nested structures before serializing logs.

## CI secret leak test protocol
1. Create a temporary branch.
2. Add a known test secret pattern such as `AWS_SECRET_ACCESS_KEY=AKIA_TEST_SHOULD_FAIL`.
3. Push and verify CI fails at the `secret_scan` job.
4. Remove test pattern before merge.
