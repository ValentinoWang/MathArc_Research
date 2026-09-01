# Acceptance Run: 20260901T003200Z-local-a1c204

- Run ID: 20260901T003200Z-local-a1c204
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 4
- Contract SHA-256: e2db06e4a9d863bc1963e19d5aac1c17bc070adb84df45d95c41ac1df39efc73
- Source identity: 8a6d908541b770461a081b43d8ced627befd0912+q1-v4-final
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T00:32:56.958717Z
- Completed at: 2026-09-01T00:33:00Z
- Evidence directory: evidence/

## Scope

AC-01 through AC-04 for Q1 contract v4: current R1 identity, the three fixed uncalibrated records, fail-closed policy parsing, and the passive non-public boundary.

## Procedure

Executed the focused Q1/R1 unit suite, bytecode-free compilation, and whitespace validation recorded in `evidence/execution.md`.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | protected tests | Current R1 evidence, fixture, topic, and case identity are closed. |
| AC-02 | PASS | protected tests | Every record remains `UNCALIBRATED` and `NOT_READY`. |
| AC-03 | PASS | protected tests | Identity, status, limits, fields, and digest tampering fail closed. |
| AC-04 | PASS | protected tests | No claim, novelty, network, mathematical, performance, or public-release authority is introduced. |

## Findings

None.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| evidence/execution.md | 8f300574ac8f2cf499b9865e9e57fd4509ef62ceb2035db8348fe01744065c3c | Commands and bounded result summary |

## Unverified items

Mathematical proof, live literature/open-status verification, novelty, calibration quality or statistical performance, production/device behavior, and public release authorization.

## Conclusion

PASS for the Q1 contract-v4 machine boundary. This is not an A5 source-delivery decision and does not make a research-publication claim.
