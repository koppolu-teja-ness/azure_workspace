# ADR-004: Secret-Handling and Redaction Policy

## Status
Accepted

## Decision
- Secret values must never enter prompts, logs, traces, fixtures, or reports.
- A recursive redaction utility is mandatory for structured logging.
- CI enforces repository secret scanning via `gitleaks`.

## Consequences
- Migration diagnostics remain useful without exposing sensitive data.
- Any accidental secret commit is blocked by CI and must be removed before merge.
