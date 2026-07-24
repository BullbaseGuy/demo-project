# ChatGPT Web + GitHub Actions execution standard

This directory is the versioned, machine-validated process contract for the
repository.

For new-repository creation, first-time configuration and the complete workflow
diagrams, read [`../USAGE.md`](../USAGE.md).

## Architecture

```text
ChatGPT Web Supervisor
-> contract / plan / implementation / diagnosis / decisions
GitHub Actions Executor
-> context / state / scope / secret / gate
Bounded zero-model recovery
-> retry only verified ordinary infrastructure failures
Product Gate
-> trusted-control scope / targeted gate / full gate / isolated optional merge
Post-Merge
-> exact merged commit verification / canonical finalization
```

Codex is not part of the default execution chain. The repository policy remains
disabled and the permanent Codex workflow performs zero-model candidate review only.

## Layers

| Layer | Location | Purpose |
|---|---|---|
| L0 | ChatGPT Project Instructions | startup and role boundaries |
| L1 | `/AGENTS.md` | repository-wide agent contract |
| L2 | scoped `AGENTS.md` | directory rules |
| L3 | `policies/` | durable policy |
| L4 | `runbooks/` | executable procedures |
| L5 | `templates/` | state and evidence templates |
| L6 | `docs/implementation/<task-id>/` | canonical dynamic task evidence |
| L7 | workflows + `scripts/devflow/` | deterministic execution |

## Policies

- [Execution contract](policies/execution-contract.md)
- [State and documentation](policies/state-and-documentation.md)
- [Monitoring and recovery](policies/monitoring-and-recovery.md)
- [Gates and merge](policies/gates-and-merge.md)
- [Impact-aware gates and cache](policies/cache-and-impact-gates.md)
- [Security and optional agent boundary](policies/security-and-agent.md)
- [Notification policy](policies/notification-policy.md)
- [Domain adapter contract](policies/domain-adapter-contract.md)

## Runbooks

- [Start a new task](runbooks/start-new-task.md)
- [Resume a task](runbooks/resume-task.md)
- [Automatic recovery](runbooks/automatic-recovery.md)
- [Handle an incident](runbooks/handle-incident.md)
- [Post-Merge validation](runbooks/post-merge-validation.md)
- [Branch garbage collection](runbooks/branch-garbage-collection.md)
- [Upgrade compatibility](runbooks/upgrade-compatibility.md)
- [One-time agent activation boundary](runbooks/run-agent-thin-worker.md)
