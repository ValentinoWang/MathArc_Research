# Acceptance environment blockers

Recorded on 2026-09-05 while attempting to complete the browser and production gates.

- `apt-get install chromium` was rejected by the managed runtime because the package helper
  cannot change its sandbox user/group IDs.
- `npx playwright install chromium` reached the download step, but the Chrome archive was
  truncated and failed ZIP validation; the retry endpoint was unavailable in this environment.
- The Work Cloud Browser launched successfully, but its isolated browser cannot connect to the
  container's `127.0.0.1:4173` (`ERR_BLOCKED_BY_CLIENT`).
- The production-domain probe was not authorized by the network policy, so no claim is made about
  `research.matharc.space` availability or systemd/TLS state.

These are blockers to completing the browser/production acceptance, not application test failures.

