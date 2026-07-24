# Generic Devflow Scaffold

A repository-neutral execution scaffold for **ChatGPT Web supervision** and
**deterministic GitHub Actions execution**.

The scaffold separates:

- planning and decisions in ChatGPT Web;
- canonical task state stored in the repository;
- deterministic validation, recovery, notifications, merge gates and post-merge verification in GitHub Actions;
- an optional Codex/agent surface that is **hard-disabled by default**.

It intentionally contains no product implementation. Add product code under
`src/` and define repository-owned commands in `.devflow/gate-profiles.json`.

## Safety defaults

| Capability | Default |
|---|---|
| Model invocation | disabled |
| Automatic merge | disabled |
| Paid relay probe | disabled |
| Branch deletion | dry-run |
| Infrastructure retry | bounded |
| Secret-bearing automation | absent |
| Third-party Actions | pinned to immutable SHAs |

## Start a task

1. Read `AGENTS.md` and `docs/process/README.md`.
2. Create a stable task ID and one work branch.
3. Copy the templates in `docs/process/templates/` to
   `docs/implementation/<task-id>/`.
4. Add the task to `docs/implementation/ACTIVE_TASKS.yaml`.
5. Create one `[TASK CONTROL] <task-id>` Issue and place its number in
   `task_state.yaml`.
6. Commit `W00_plan.md` before implementation.
7. Open a Draft PR and let the deterministic checks run.

Detailed instructions are in
[`docs/process/runbooks/start-new-task.md`](docs/process/runbooks/start-new-task.md).

## Configure a product repository

Edit only the central configuration surfaces:

- `.devflow/project.json`: actors, branch prefixes, feature switches, path classes and recovery limits;
- `.devflow/gate-profiles.json`: trusted command argument arrays;
- `.devflow/codex-policy.yaml`: remains disabled unless a separately reviewed one-time activation is approved.

A gate command is an argument array, not a shell expression:

```json
["python", "-m", "pytest", "-q"]
```

Shell command strings and `bash -c` style execution are rejected.

## Local validation

```bash
python -m pip install -e ".[dev]"
python scripts/devflow/validate_docs.py
python scripts/devflow/validate_workflows.py
python scripts/devflow/validate_state.py --all-active --no-git
python scripts/devflow/upgrade_compatibility.py
ruff check scripts tests
pytest -q
```

## Architecture

```text
ChatGPT Web Supervisor
  -> contract / plan / diagnosis / PR review / decisions
GitHub Actions Executor
  -> state / scope / gate / bounded recovery / notification
Product Gate
  -> merge-base scope / full gate / optional reviewed merge
Post-Merge
  -> independent verification of the exact merged commit
Optional Agent Surface
  -> disabled by policy; zero-model candidate review only
```

See [`docs/process/README.md`](docs/process/README.md) for the complete index.
