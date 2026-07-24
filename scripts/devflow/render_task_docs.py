from __future__ import annotations

import argparse
from pathlib import Path

from state_model import TaskState, load_json_yaml


def render_status(
    data: dict[str, object],
    state: TaskState,
) -> str:
    post_merge = data["post_merge"]
    return f"""# STATUS: {state.task_id}

```yaml
status: {state.status}
execution_status: {state.execution_status}
acceptance_domain: {state.acceptance_domain}
acceptance_status: {state.acceptance_status}
security_status: {state.security_status}
current_stage: {state.current_stage}
last_completed_stage: {state.last_completed_stage or 'null'}
branch: {state.working_branch}
pull_request: {data.get('pull_request') or 'pending'}
next_action: {data['next_action']}
post_merge: {post_merge['status']}
human_intervention_required: {str(state.human_required).lower()}
```

Generated from `task_state.yaml`; canonical state wins on conflict.
"""


def render_handoff(
    data: dict[str, object],
    state: TaskState,
) -> str:
    human = data["human_gate"]
    return f"""# HANDOFF: {state.task_id}

## Current facts

- Status: {state.status}
- Execution: {state.execution_status}
- Acceptance: {state.acceptance_domain}/{state.acceptance_status}
- Security: {state.security_status}
- Stage: {state.current_stage}
- Branch: `{state.working_branch}`
- Pull request: {data.get('pull_request') or 'pending'}
- Last successful step: `{data['last_successful_step']}`
- Next action: `{data['next_action']}`

## Current block

{human.get('reason') or 'None'}

## Minimum human action

{human.get('minimum_action') or 'None'}

## Resume order

1. `task_state.yaml`
2. current GitHub Checks and bounded artifacts
3. current `Wxx_plan.md` / `Wxx_result.md`
4. this file
5. `docs/process/README.md`

## Retry budget

`{data['retry_budget']}`
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_dir", type=Path)
    args = parser.parse_args()
    data = load_json_yaml(
        args.task_dir / "task_state.yaml"
    )
    state = TaskState.from_mapping(data)
    (args.task_dir / "STATUS.md").write_text(
        render_status(data, state),
        encoding="utf-8",
    )
    (args.task_dir / "HANDOFF.md").write_text(
        render_handoff(data, state),
        encoding="utf-8",
    )
    print("TASK_DOCS_RENDERED=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
