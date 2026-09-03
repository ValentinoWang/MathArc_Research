# Acceptance Run: 20260903T045853Z-local-a11ce0

- Run ID: 20260903T045853Z-local-a11ce0
- Task ID: FEAT-20260903-01
- Lane: machine/e2e
- Status: PASS
- Acceptance contract: agents-results/2026-09-03/research-preview-access/acceptance-contract.md
- Contract version: 1
- Contract SHA-256: e9013cd21bcfd9d13a183a50807ec45cd173927b7c22415c3dbf6bf4e45dee45
- Source identity: access-surface@4de13b752e6aac834362c65510bf493951507a64730305cf32f6aacfecc2f841
- Runtime identity: local-playwright-fixture
- Executor or reviewer: codex-browser-gate
- Started at: 2026-09-03T04:58:00Z
- Completed at: 2026-09-03T04:58:53.013Z
- Evidence directory: evidence/

## Scope

Covered AC-01 through AC-03 on the local Chromium fixture: application pending,
invalid invitation, successful redemption, hardened session cookie, refresh
restoration, invitation replay rejection, logout, guest isolation, authenticated
M1 SSE, and M2 review behavior. This run excludes human judgment, production,
external sandbox, and physical-device claims.

## Procedure

Ran `node scripts/console_browser_gate.mjs` twice against fresh temporary access
stores. Both executions exited zero. The second execution produced the reviewed
10-image desktop/mobile capture set registered below; an independent SHA-256
recalculation matched all manifest entries.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | evidence/screenshot-manifest.json | Application pending and email-bound redemption journeys passed. |
| AC-02 | PASS | evidence/screenshot-manifest.json | Anonymous access, session restoration, replay, logout, SSE, and review boundaries passed. |
| AC-03 | PASS | evidence/screenshot-manifest.json | Ten reviewed desktop/mobile captures are hash-bound to this run. |

## Findings

None.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| evidence/screenshot-manifest.json | d8f1aa4f446bd758d69eccf9c90f133070c4497c93bfd7fe7c48193c5bbeff96 | Reviewed capture identities, viewports, timestamps, and content hashes. |

## Unverified items

Human comprehension and approval; production deployment, TLS, email delivery,
real institutional identity, external service behavior, and physical-device
rendering.

## Conclusion

PASS for the bounded local browser access workflow. This is machine evidence
only and does not satisfy H-01 or establish production readiness.
