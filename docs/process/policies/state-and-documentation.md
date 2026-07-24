# State and documentation

Each task has one canonical state file:

```text
docs/implementation/<task-id>/task_state.yaml
```

The file uses JSON syntax stored with a `.yaml` extension for deterministic
standard-library parsing.

Schema v2 separates:

```yaml
execution_status: PENDING | RUNNING | COMPLETED | FAILED | BLOCKED
acceptance:
  domain: generic | <adapter-domain>
  status: PENDING | PASS | REVIEW_REQUIRED | FAIL
security_status: PENDING | PASS | BLOCKED | FAIL
post_merge:
  status: PENDING | RUNNING | PASS | FAIL
```

`DONE` requires execution `COMPLETED`, acceptance `PASS`, security `PASS`,
Post-Merge `PASS`, no human gate and complete plan/result evidence.

Required task files include contract, master plan, canonical state, STATUS,
HANDOFF, DECISIONS, the current plan, completed stage results and a final report.
