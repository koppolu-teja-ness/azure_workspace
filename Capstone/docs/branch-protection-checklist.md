# Develop Branch Protection Checklist

Repository scope: Azure-to-AWS migration capstone
Target branch: `develop`
Owner: `saurav-das-ness`

## Required status checks
- `lint`
- `schema_validation`
- `contract_tests`
- `secret_scan`

## GitHub settings steps
1. Open repository Settings.
2. Go to Branches.
3. Under Branch protection rules, choose Add rule.
4. Branch name pattern: `develop`.
5. Enable Require a pull request before merging.
6. Enable Require status checks to pass before merging.
7. Select checks:
   - `lint`
   - `schema_validation`
   - `contract_tests`
   - `secret_scan`
8. Enable Require branches to be up to date before merging.
9. Enable Restrict who can push to matching branches (optional but recommended).
10. Save changes.

## Verification
- Open a test PR to `develop`.
- Confirm the four checks appear and must pass.
- Confirm merge button is disabled when any required check fails.

## Evidence to capture
- Screenshot of branch protection rule
- Screenshot of blocked PR when a check fails
- Link to successful PR with all required checks green
