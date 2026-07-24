# Gates and merge

Gate layers:

| Gate | Purpose |
|---|---|
| G0 | state, documentation, workflow, context, scope and secret safety |
| G1 | targeted task validation |
| G2 | complete repository regression |
| G3 | optional real bounded integration slice |
| G4 | optional product E2E or performance matrix |
| G5 | independent exact-merge Post-Merge |

Product Gate validates expected base ancestry, calculates the merge base,
checks only candidate changes, runs the full gate and refreshes against the
latest default branch before any allowed merge.

Automatic merge is disabled by default. It may be enabled only for reviewed
low-risk tasks with explicit scope and all gates passing. Merge conflict,
protection or permission blocks require a human.
