# Runbook: start a new task

1. Read the repository contract, process index and active task index.
2. Audit the default branch, open pull requests and shared paths.
3. Create a stable task ID and one work branch from current default branch.
4. Create contract, master plan, canonical state, HANDOFF and DECISIONS files.
5. Add the task to `ACTIVE_TASKS.yaml`.
6. Create one `[TASK CONTROL] <task-id>` Issue and record its number in state.
7. Commit `W00_plan.md` before implementation.
8. Open a Draft PR referencing the canonical task directory.
9. Define allowed paths, gate profiles, failure classes and human boundaries.
10. Continue through ordinary success states without pausing.
