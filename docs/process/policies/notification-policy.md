# Notification policy

Raw workflow failure is not a user notification. Classification and bounded
recovery run first.

Only these decisions enter the canonical Task Control Issue:

```text
COMPLETED
INTERRUPTED
HUMAN_REQUIRED
SECURITY_BLOCKED
```

Each task uses one `[TASK CONTROL] <task-id>` Issue. Notifications are deduplicated
by `task_id + fingerprint + notification_type`.

`/ack` only records receipt. It does not repair, retry, resume or change state.
