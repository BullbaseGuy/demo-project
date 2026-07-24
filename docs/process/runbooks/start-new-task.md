# Runbook: start a new task

The normal path is a ChatGPT Web supervised feature branch and pull request. The
optional Agent Product Gate is a separate, default-disabled path and must not be
confused with ordinary development.

## Standard ChatGPT Web path

1. Read `/AGENTS.md`, `docs/process/README.md`, the active-task index and current
   GitHub Checks.
2. Choose a stable task ID using letters, numbers, dot, underscore or hyphen.
3. Refresh the default branch and create one branch using the configured
   `.devflow/project.json` `work_prefix`, for example `feature/example`.
4. Copy the task templates into `docs/implementation/<task-id>/` and replace all
   placeholders.
5. Add one entry to `docs/implementation/ACTIVE_TASKS.yaml`. Set:
   - `branch` to the feature branch;
   - `task_branch` and `publish_branch` to `null` for the standard path;
   - `post_merge_profile` to `post-merge` unless the project defines another
     trusted profile;
   - `notify_completion` to `true` when a final Issue notification is wanted.
6. Create exactly one `[TASK CONTROL] <task-id>` Issue. Put its number in
   `task_state.yaml.notification.control_issue_number`.
7. Commit `00_contract.md`, `01_master_plan.md`, `task_state.yaml`, `HANDOFF.md`,
   `DECISIONS.md` and `W00_plan.md` before implementation.
8. Open a Draft PR and write its number into both the task index and canonical
   state.
9. Execute one work package at a time. A verified work package receives a
   matching `Wxx_result.md` before the next package begins.
10. Before merge, set the canonical state to a verifiable pre-final state:
    - `status: VERIFYING`;
    - `execution_status: COMPLETED`;
    - `acceptance.status: PASS`;
    - `security_status: PASS`;
    - `human_gate.required: false`;
    - current `Wxx_plan.md` and `Wxx_result.md` both exist.
11. Merge only after required PR checks pass. The `pull_request: closed` trigger
    in `Devflow Post Merge` resolves the task by PR number, verifies the exact
    merged commit, updates canonical state to `DONE`, writes `FINAL_REPORT.md`,
    commits the closeout and closes the Task Control Issue.

## Optional immutable Agent Product Gate

This path remains unavailable while `.devflow/codex-policy.yaml` and
`.devflow/project.json` keep agent execution disabled. A future separately
reviewed activation uses two additional branches:

- `task/agent-<task-id>`: data-only branch containing
  `.agent/current_task.yaml`;
- `agent/<task-id>`: immutable candidate code branch.

Dispatch `Devflow Product Gate` with the exact task and candidate commit SHAs.
The read-only Gate job checks the trusted default-branch control plane, candidate
scope, targeted profile and full profile. A separate write-capable job may merge
only when repository policy and the immutable descriptor both explicitly allow
low-risk auto-merge. Candidate code never runs in the write-capable job.

## Pause conditions

Pause only for a real permission or security boundary, an irreversible action,
a business decision, an unclassifiable failure, a merge conflict or exhausted
bounded recovery. Record the minimum action and resume point in canonical state.
