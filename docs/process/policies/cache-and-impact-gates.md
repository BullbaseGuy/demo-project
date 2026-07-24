# Impact-aware gates and cache

Changed paths are classified conservatively:

- `docs_only`: documentation link and format checks;
- `devflow_only`: framework compile, lint, tests and compatibility;
- `product`: full repository gate and configured integration checks.

Unknown paths and mixed changes use the highest risk. An empty diff still runs
the safe framework gate.

Only regenerable dependencies may be cached. Scope, secrets, manifests, merge
base, current gates, Post-Merge and canonical state are always recomputed.
