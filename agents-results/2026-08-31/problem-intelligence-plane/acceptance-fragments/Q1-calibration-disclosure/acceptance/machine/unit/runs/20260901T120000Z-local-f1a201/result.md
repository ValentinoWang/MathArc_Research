# Acceptance Run: 20260901T120000Z-local-f1a201

- Run ID: 20260901T120000Z-local-f1a201
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 4
- Contract SHA-256: 1cd610edf1dba0d8dfecf827ce0680c57b8ce7496b2d81ccae70a01879e29225
- Source identity: 757feb11c6d6c05bb43332bcf3c1a523a7833a7d+q1-v4-final
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T12:00:00Z
- Completed at: 2026-09-01T12:01:00Z
- Evidence directory: evidence/

## Scope

AC-01 through AC-04 for the current Q1 contract-v4 policy boundary: current R1 identity, three fixed uncalibrated records, fail-closed parsing, and the passive non-public restriction.

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
| evidence/execution.md | bedca3bce6960d5e7f5b15c2ead4e00ff27763633ce416e832d0013ed51f2969 | Commands and bounded result summary. |

## Unverified items

Mathematical proof, live literature/open-status verification, novelty, calibration quality, statistical performance, production/device behavior, and public release authorization.

## Conclusion

PASS for the locked Q1 contract-v4 machine boundary only. It is not an A5 source-delivery decision and does not make a research-publication claim.
