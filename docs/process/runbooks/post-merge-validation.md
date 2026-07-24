# Runbook: Post-Merge validation

1. A merged PR, Product Gate dispatch or manual recovery dispatch starts the
   workflow.
2. For a merged PR, resolve exactly one indexed task by `pull_request` number.
   Unmanaged PRs exit successfully without modifying canonical state.
3. Bind verification to the exact merge SHA and prove it is contained in the
   configured default branch.
4. Run the declared Post-Merge profile independently in a read-only job.
5. On failure, route bounded evidence through Auto Recovery to ChatGPT Web.
6. On success, a separate write-capable job runs only protected Devflow control
   code. It requires existing acceptance and security PASS values, writes
   `DONE`, records the merge/run, generates `FINAL_REPORT.md`, updates the task
   index and pushes the canonical closeout.
7. Dispatch one deduplicated completion notification. A duplicate Post-Merge run
   for the same merge SHA is idempotent.
8. If default-branch rules block the closeout push, do not force-push. Follow the
   `HUMAN_REQUIRED` or `INTERRUPTED` recovery instruction.
