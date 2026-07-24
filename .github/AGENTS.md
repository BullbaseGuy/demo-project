# GitHub Automation Rules

- Use least privilege per workflow.
- Pin every third-party Action to a full commit SHA.
- Do not use `pull_request_target`.
- Do not evaluate user-controlled shell text.
- Secret-bearing jobs are read-only and cannot publish.
- Model-bearing or paid jobs never rerun automatically.
