# Devflow Script Rules

These rules apply to `scripts/devflow/**`.

- Scripts must be deterministic, non-interactive and usable on GitHub-hosted Ubuntu runners.
- Machine-readable output goes to JSON files; terminal output is bounded.
- Treat artifact content as untrusted data.
- Do not execute commands read from task files.
- Resolve a trusted gate profile owned by the default branch.
- State validation fails closed for malformed state or missing evidence.
- Secret audit reports counts only and never prints a matching value.
- Unit tests are required for state transitions, path guards and workflow policy.
