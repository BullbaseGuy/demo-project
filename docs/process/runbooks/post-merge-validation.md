# Runbook: Post-Merge validation

1. Bind the run to the merge SHA supplied by Product Gate.
2. Check out that exact commit.
3. Prove the commit is contained in the configured default branch.
4. Run the declared Post-Merge profile independently of the pre-merge run.
5. On failure, route bounded evidence to ChatGPT Web.
6. On success, finalize canonical state and send one completion notification.
