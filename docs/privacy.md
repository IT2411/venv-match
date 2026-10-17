# Privacy and Security Policy

Venv Match is designed with privacy and data minimization by default:

1. **No Arbitrary Environment Variable Collection:** Environment variables are never collected unless explicitly allowlisted by name via `CaptureConfig(env_vars=...)` or `--env NAME`. Wildcard patterns (`*`, `?`) are rejected.
2. **Presence-Only Default:** Even when an environment variable is allowlisted, only its presence (`"present": true/false`) is recorded unless `include_env_values=True` or `--env-values` is explicitly provided.
3. **Secret Variable Exclusion:** Variable names containing secret-like keywords (`TOKEN`, `SECRET`, `PASSWORD`, `PASSWD`, `API_KEY`, `APIKEY`, `PRIVATE_KEY`, `PRIVATEKEY`, `CREDENTIAL`, `AUTH`) are excluded from value collection and automatically redacted (`"<redacted>"`) across all terminal and JSON reports.
4. **No Identifying Machine Telemetry:** Hostnames, IP addresses, usernames, running processes, and source code are never collected.
5. **Safe Deserialization:** Snapshots are parsed strictly as UTF-8 JSON and validated against the schema. Venv Match never uses `pickle` or executes code from a snapshot.
