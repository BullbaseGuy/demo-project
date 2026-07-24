# Monitoring and bounded recovery

Jobs expected to exceed five minutes must stream output or print a heartbeat.
The ChatGPT UI animation is not execution state.

Failures are classified as infrastructure, mechanical, implementation, context,
security, permission, business, merge conflict or unclassified.

Only verified ordinary infrastructure failures may rerun failed jobs, and only
within the configured limit. Model-bearing jobs, paid probes, security failures,
scope violations and permission boundaries never retry automatically.

Failure bundles contain a stable reason code, fingerprint, failed steps, bounded
log tail and minimum action. Full logs remain in short-lived GitHub artifacts.
