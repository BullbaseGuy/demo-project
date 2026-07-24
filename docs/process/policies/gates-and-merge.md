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

The normal ChatGPT Web path uses a reviewed feature PR and required checks. The
optional Agent Product Gate is stricter: it checks out the exact default-branch
control plane, exact task descriptor SHA and exact candidate SHA in separate
directories. Scope and Gate commands come only from the trusted control plane.

Candidate code executes only in a read-only Gate job. A separate write-capable
job may merge an already verified exact SHA, but must not run candidate code. If
the default branch or candidate branch moves after verification, the merge fails
closed and requires a new review; the write job does not silently rebase.

Automatic merge is disabled by default. It may be enabled only when both
repository policy and an immutable low-risk descriptor explicitly approve it.
Merge conflict, branch movement, protection or permission blocks require a human.

A pre-merge PASS is not completion. G5 verifies the exact merged commit. The
Finalizer preserves domain acceptance and security results, requires them to be
PASS, updates canonical state, writes `FINAL_REPORT.md` and records the verified
run. It never manufactures acceptance or security PASS values.
