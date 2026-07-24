# Engineering issues and reusable lessons

Record repeatable framework issues here rather than in chat history.

## GHA-001 Workflow file permission

- Symptom: ordinary files can be written but `.github/workflows/*.yml` is rejected.
- Cause: the acting identity lacks Workflow write permission.
- Prevention: check Workflow permission before implementation and separate
  workflow changes from ordinary content changes.

## GHA-002 Long job observability

- Symptom: Actions appears stuck with no output.
- Cause: child output is buffered and no heartbeat exists.
- Prevention: jobs over five minutes stream output or print a 15–30 second heartbeat.

## GHA-003 Blind retry repeats successful work

- Symptom: a transient failure reruns the entire pipeline.
- Cause: infrastructure, implementation and permission failures are not classified.
- Prevention: retry only failed ordinary infrastructure jobs and retain checkpoints.

## GIT-001 Parallel pull request overlap

- Symptom: a candidate passes but conflicts with later default-branch changes.
- Cause: no path-overlap audit or refreshed merge-base gate.
- Prevention: audit overlap at branch creation and immediately before merge.

## CODE-001 Mechanical lint fixes

- Symptom: repeated manual edits fail the same formatter or import rule.
- Cause: visual guessing differs from tool behavior.
- Prevention: use the repository-pinned tool for mechanical fixes.
