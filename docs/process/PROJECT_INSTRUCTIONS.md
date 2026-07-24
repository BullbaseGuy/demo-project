# ChatGPT Project Instructions

Repository development uses versioned GitHub state as the source of truth.

For every complex task, read in order:

1. root `AGENTS.md`;
2. `docs/process/README.md`;
3. `docs/implementation/ACTIVE_TASKS.yaml`;
4. the current task's `task_state.yaml`, `HANDOFF.md` and `Wxx_plan.md`;
5. current pull request, branch HEAD and GitHub Checks.

`task_state.yaml` is the sole task state. Save a plan before each work package
and a result only after deterministic validation. Pause only for a real
permission, security, irreversible, conflict or business boundary. Never expose
private runtime values in chat, repository files, logs, Issues or artifacts.
