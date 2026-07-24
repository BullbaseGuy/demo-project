# Runbook: resume a task

Read in order:

1. `ACTIVE_TASKS.yaml`;
2. canonical `task_state.yaml`;
3. current Checks and bounded artifacts;
4. branch and pull request;
5. `HANDOFF.md`;
6. current plan/result;
7. chat history last.

Do not repeat a successful checkpoint. Resume from `next_action` unless current
repository facts prove it stale.
