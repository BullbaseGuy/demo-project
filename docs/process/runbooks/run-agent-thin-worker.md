# Runbook: one-time agent activation boundary

The default scaffold cannot invoke a model.

A future activation requires:

1. a concrete failed task and trusted reproduction;
2. explicit user approval;
3. one immutable task descriptor and allowed file list;
4. an approved context budget;
5. a one-time grant with a short TTL;
6. a separate reviewed activation pull request;
7. one non-rerunnable model session;
8. deterministic scope, secret and gate checks before publication.

A blocked or failed session consumes the grant and cannot be rerun.
