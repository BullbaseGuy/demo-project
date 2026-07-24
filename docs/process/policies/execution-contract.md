# Execution contract

A complex task begins with a versioned contract defining objective, scope,
inputs, outputs, constraints, acceptance criteria, human gates, rollback and
notification behavior.

Roles:

- **ChatGPT Web Supervisor**: requirements, repository audit, planning,
  implementation, diagnosis, pull request review and decisions.
- **GitHub Actions Executor**: deterministic commands, state checks, gates,
  artifacts, bounded recovery and Post-Merge.
- **Optional Agent Thin Worker**: one explicitly authorized, narrow task only.
- **User**: permissions, secrets, irreversible actions and business decisions.

Normal success continues automatically. Pause only when continuing would require
guessing, bypassing protection or changing business meaning.
