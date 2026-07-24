# Runbook: automatic recovery

1. Collect source workflow, run attempt, failed job and step metadata.
2. Download only bounded safe artifacts.
3. Generate a stable root-cause fingerprint.
4. Classify.
5. Retry only verified ordinary infrastructure failures.
6. Dispatch a valuable notification only for terminal decisions.
7. Never dispatch or rerun a model job or paid probe.
