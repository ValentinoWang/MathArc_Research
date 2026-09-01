# Acceptance Run: 20260901T093000Z-local-a1c004

- Run ID: 20260901T093000Z-local-a1c004
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 4
- Contract SHA-256: e2db06e4a9d863bc1963e19d5aac1c17bc070adb84df45d95c41ac1df39efc73
- Source identity: 8a6d908541b770461a081b43d8ced627befd0912+q1-v4-reaccept
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T00:09:30.583741Z
- Completed at: 2026-09-01T08:20:00+08:00
- Evidence directory: evidence/

## Scope

AC-01 through AC-04 for Q1 contract v4 only: current R1 identity, three fixed uncalibrated records, fail-closed policy parsing, and the passive non-public boundary. This run deliberately does not make a mathematical, external-literature, statistical, production, or public-release conclusion.

## Procedure

Executed `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`, `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile matharc/v02/calibration_disclosure.py tests/test_v02_calibration_disclosure.py`, contract validation, and `git diff --check`.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | protected tests, Q1.json | Current R1 evidence, fixture, topic, and case identity are closed. |
| AC-02 | PASS | protected tests, policy fixture | Every record remains UNCALIBRATED and NOT_READY. |
| AC-03 | PASS | protected tests | Identity, status, limits, fields, and digest tampering fail closed. |
| AC-04 | PASS | protected tests, independent reports | No claim, novelty, network, mathematical, performance, or public-release authority is introduced. |

## Findings

The whole-suite red proof is the intentionally stale A5 policy-fixture hash. It is downstream of Q1 and is owned by A5 reacceptance; it does not weaken or bypass any Q1 criterion.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| evidence/Q1.json | pending final evidence hash | Current Q1 acceptance evidence is finalized after this immutable run. |
| protected test | 7a38001d211c2b8ef5b6b45e8f8fa87f7b0ce9785559cc475eb511d250af5026 | Locked Q1 test baseline. |

## Unverified items

Mathematical proof, live literature/open-status verification, novelty, calibration quality, statistical performance, production/device behavior, and public release authorization.

## Conclusion

PASS for the Q1 contract-v4 machine boundary. This is not an A5 source-delivery decision and does not make a research-publication claim.
