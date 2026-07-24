# Runbook: branch garbage collection

The planner considers only configured managed prefixes. It blocks active task
branches and open pull request heads.

The default is Dry Run. Deletion requires both repository configuration and the
individual dispatch to allow execution. Never delete an unmanaged branch.
