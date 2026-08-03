# Pinned Workflow Skills

`BullbaseGuy/chatgpt-workflow-skills` is the single source of reusable ChatGPT Web workflow skills. This scaffold contains only an immutable consumer lock, compatibility validation, and usage guidance. It does not copy or independently maintain any `SKILL.md` body.

## Lock

`.devflow/workflow-skills.lock.json` records:

- the source repository;
- a full 40-character reviewed commit;
- release manifest and installer Git blob identities;
- the install root and router entry point;
- payload file count;
- the zero-model requirement.

Changing any of these values is a framework change and must pass the compatibility workflow.

## Install on Windows

Download the installer from the exact locked revision, verify its Git blob SHA against the lock, then run it with the same revision. The workflow `.github/workflows/devflow-workflow-skills-compatibility.yml` performs this end to end on `windows-latest` and verifies that a second run returns `UNCHANGED`.

For an already checked-out skills repository, use its offline mode:

```powershell
$Lock = Get-Content .\.devflow\workflow-skills.lock.json -Raw | ConvertFrom-Json
pwsh -File D:\src\chatgpt-workflow-skills\scripts\install-workflow-skills.ps1 `
  -Revision $Lock.revision `
  -OfflineSourceRoot D:\src\chatgpt-workflow-skills `
  -Destination .\.agents\workflow-skills
```

The generated `.agents/workflow-skills` directory is a pinned installation artifact. Do not commit it; the source repository remains authoritative.

## ChatGPT Project entry instruction

```text
Read AGENTS.md, docs/process/README.md and .devflow/workflow-skills.lock.json. Resolve the active
canonical task state and HANDOFF before reading the pinned workflow-router skill. ChatGPT Web is the
Supervisor; GitHub Actions is the Executor. Continue in AUTO and stop only for a DECISION_POLICY
HUMAN_GATE. Never ask again for facts already present in the repository, Issue, PR or Actions run.
```

## Upgrade

1. Review the source-repository diff and Checks.
2. Replace the lock revision, release version, manifest blob, installer blob and payload count.
3. Run the compatibility workflow.
4. Confirm no tracked `SKILL.md` files were introduced into this scaffold.
5. Merge the lock update only after the exact pinned installer passes on Windows.

## Resume

A fresh ChatGPT session receiving only a task ID first resolves `docs/implementation/ACTIVE_TASKS.yaml`, then the task state and `HANDOFF.md`, and finally the router from the installed or source-repository revision named by the lock. Chat history is never required as a state store.
