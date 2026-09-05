# Runtime demo readback evidence

This evidence was produced from commit `5a373a007893633f6b581e33b2c2bbdb2d63414c`.
It covers the local, credential-free demo server only. The server persisted a successful
run and a blocked run under deterministic run IDs, then served the successful run back
through `GET /api/demo/runs/<run_id>` after the POST completed.

## Results

- `VERIFIED_CERTIFICATE` returned for the supported odd-sum question.
- `promotion_allowed=false`; the result remains evidence and does not promote a theorem.
- `BLOCKED` returned for an unsupported question, with no evidence object.
- Readback returned the same run ID and accepted evidence.
- HTTP payloads redact internal host paths.
- `make test-full` passed separately: 799 tests, 0 failures, 0 errors, 20/20 SMT tests executed,
  with only the two contract-whitelisted legacy skips.

The browser gate was attempted with Playwright and recorded as blocked because this environment
has no installed Chromium executable. This is an environment limitation, not a browser-pass claim.

