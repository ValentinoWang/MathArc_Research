# Guard Card: research-preview-access-boundary

- Failure class: client-side invitation bypass or unauthenticated live-projection disclosure
- Scope: the research-preview entry flow, access store, workspace/review HTTP adapters, and console browser fixture
- Blocking level: release gate when `access_store_root` is configured
- Fast proof: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_access tests.test_v02_access_server tests.test_console_prototype`
- Runtime proof: `node scripts/console_browser_gate.mjs`
- Repair path: restore the server-owned invitation/session validation, keep the dashboard and guest demo public, re-gate every live API/review/SSE route, and rerun both commands.
- Retirement condition: replace only when another server-owned identity system covers the same endpoints and the negative fixtures are migrated before this guard is removed.

## Failure Contract

The guard fails when a non-empty client value can enter authenticated mode, when invitation or session secrets are persisted in plaintext, when an invitation can be replayed or used with another email, when an expired/revoked/logged-out credential remains active, or when any live workspace, event, artifact, console, or review route succeeds without a valid preview session. A preview session never grants review-write authority: `POST /api/review` continues to require the independent reviewer Bearer credential.

The public dashboard, access application/redeem/session/logout endpoints, health signal, and explicitly labeled guest demonstration remain reachable without a preview session. Topic scopes are session metadata until a separately verified server projection enforces record-level filtering; this guard does not claim that filtering exists.

## Evidence

- Red proof: tests send missing, malformed, wrong-email, replayed, expired, revoked, duplicate, and logged-out credentials; access protected routes with no Cookie; try reviewer Bearer without a preview session; and try a preview session without reviewer Bearer.
- Green proof: an email-bound invitation is redeemed once, an HttpOnly SameSite cookie restores the session, protected JSON/SSE projections become reachable, logout revokes the session, and a fresh guest context remains demo-only.

## Calibration

With `access_store_root=None`, the existing observatory remains backward compatible and this access boundary is inactive. Browser screenshots prove only the rendered states; API tests and hashed-at-rest inspection separately prove the authorization and secret-storage behavior. Neither layer is human acceptance or production deployment evidence.
