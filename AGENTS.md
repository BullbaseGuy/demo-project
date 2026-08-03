# Repository Agent Contract

This file is the repository-wide entry point for ChatGPT Web, Codex and other
coding agents.

## Required reading order

1. `docs/process/README.md`;
2. `.devflow/workflow-skills.lock.json` and, when installed, the locked
   `.agents/workflow-skills/skills/workflow-router/SKILL.md`;
3. `docs/implementation/ACTIVE_TASKS.yaml`;
4. the active task's `task_state.yaml`, `HANDOFF.md` and current `Wxx_plan.md`;
5. the nearest scoped `AGENTS.md` for every changed path;
6. the current branch, pull request and GitHub Checks.

## Non-negotiable rules

1. `task_state.yaml` is the canonical task state. Chat history is not a state store.
2. Every work package requires `Wxx_plan.md` before implementation and
   `Wxx_result.md` only after deterministic verification.
3. Continue through ordinary intermediate states. Pause only for a real
   permission, security, irreversible, business, conflict or exhausted-retry boundary.
4. Run all failures through deterministic classification before notifying the user.
5. Retry only verified ordinary infrastructure failures, and preserve successful checkpoints.
6. Codex/model execution is disabled by default.
7. Never place secrets, private endpoints, model identifiers or transformed secret
   values in tracked files, logs, Issues, pull requests or artifacts.
8. A changed path outside the declared scope is `SECURITY_BLOCKED`.
9. Separate execution status, domain acceptance and security status.
10. Long jobs need streaming output or a fixed heartbeat.
11. Mechanical checks belong in scripts and CI, not prose-only instructions.
12. Do not mark a task complete until exact-merge Post-Merge verification and
    canonical closeout both pass.
13. Valuable notifications are limited to `COMPLETED`, `INTERRUPTED`,
    `HUMAN_REQUIRED` and `SECURITY_BLOCKED`.
14. `/ack` only confirms receipt; it never triggers repair or resume.
15. Reusable workflow skills come only from the exact revision in
    `.devflow/workflow-skills.lock.json`; branch names and abbreviated SHAs are invalid.
16. This scaffold must not track copied `SKILL.md` bodies. Installed skills are generated
    artifacts and the source repository remains authoritative.
17. Before using or upgrading the skills, validate the lock, remote manifest, installer blob,
    zero-model setting and compatibility workflow.
