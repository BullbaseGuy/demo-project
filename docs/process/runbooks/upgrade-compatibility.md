# Runbook: upgrade compatibility

Compatibility changes use versioned fixtures. Unknown schema versions fail
closed. Migration first produces an idempotent preview and never reopens a
completed task.

Run:

```bash
python scripts/devflow/upgrade_compatibility.py
```
