# Security and optional agent boundary

Codex/model execution is disabled by default. The permanent workflow is
zero-secret and performs candidate review only.

A future one-time activation requires a separate reviewed pull request, explicit
user approval, one immutable task commit, bounded allowed files, a context
budget, one short-lived grant and at most one call.

Task branches are data-only. Control code, policy, scope, gate and secret logic
must come from an exact trusted default-branch commit.

Secret-bearing jobs are repository read-only and separate from publication,
merge and Post-Merge. Model jobs and paid probes never rerun automatically.
