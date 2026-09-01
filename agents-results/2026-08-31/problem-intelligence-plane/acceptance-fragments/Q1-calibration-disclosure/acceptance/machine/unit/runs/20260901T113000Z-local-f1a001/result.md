# Acceptance Run: 20260901T113000Z-local-f1a001

- Run ID: 20260901T113000Z-local-f1a001
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 4
- Contract SHA-256: 5da7263cc7923547e88092f0b25a6beba144332b33e070c6aed4e1e453dd7612
- Source identity: 8a6d908541b770461a081b43d8ced627befd0912+q1-v4-integrity-final
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T11:30:00Z
- Completed at: 2026-09-01T11:31:00Z
- Evidence directory: evidence/

## Scope

AC-01 through AC-04 for the current Q1 contract-v4 policy boundary: current R1 identity, the fixed three uncalibrated records, fail-closed parsing, and the passive non-public restriction. This run makes no mathematical, external-literature, statistical, production, or public-release conclusion.

## Procedure

Executed the locked focused unit suite, Python compilation of the implementation and protected test, and `git diff --check`; the command transcript is retained in `evidence/execution.md`.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | protected tests | Current R1 evidence, fixture, topic, and case identity are closed. |
| AC-02 | PASS | protected tests, policy fixture | Every record remains `UNCALIBRATED` and `NOT_READY`. |
| AC-03 | PASS | protected tests | Identity, status, limits, fields, fixture bytes, and recomputed-digest tampering fail closed. |
| AC-04 | PASS | protected tests | No claim, novelty, network, mathematical, performance, or public-release authority is introduced. |

## Findings

None.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| evidence/execution.md | 7c27cd08a2170b3d1962e2c48a6bd2738352c1f80df2daa4140859cbeb6aa72f | Commands and bounded result summary. |

## Unverified items

Mathematical proof, live literature/open-status verification, novelty, calibration quality, statistical performance, production/device behavior, and public release authorization.

## Conclusion

PASS for the locked Q1 contract-v4 machine boundary only. It is not an A5 source-delivery decision and does not make a research-publication claim.
