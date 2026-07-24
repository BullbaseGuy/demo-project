# Domain adapter contract

The Devflow core understands platform execution, generic acceptance, security
and Post-Merge. A product may define domain-specific acceptance reason codes and
evidence files without changing the core state machine.

A completed program may still require domain review:

```yaml
execution_status: COMPLETED
acceptance:
  domain: example-domain
  status: REVIEW_REQUIRED
  reason_code: SOURCE_CONFLICT
```

This is not a program crash. Domain adapters must never convert missing evidence
into a fabricated zero, absence or success.
