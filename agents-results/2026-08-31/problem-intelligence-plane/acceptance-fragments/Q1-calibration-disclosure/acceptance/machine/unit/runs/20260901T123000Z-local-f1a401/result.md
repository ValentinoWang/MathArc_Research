# Acceptance Run: 20260901T123000Z-local-f1a401

- Run ID: 20260901T123000Z-local-f1a401
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 4
- Contract SHA-256: 2c4acb235a042800c14b5af2e6d2ae47f6b87e5e284cad9e5c114ce728806b5e
- Source identity: b35e02c2f12d1180ffca1c6af3d29b543c5929da+q1-v4-final
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T12:30:00Z
- Completed at: 2026-09-01T12:31:00Z
- Evidence directory: evidence/

## Scope

AC-01 through AC-04 for current R1 evidence, three fixed uncalibrated records, fail-closed parsing, and the passive non-public restriction.

## Procedure

Ran `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`, Python compilation of the implementation and protected test, and `git diff --check`.

## Requirement disposition

| Requirement | Result | Notes |
| --- | --- | --- |
| AC-01 | PASS | Current R1 evidence, fixture, topic, and case identity are closed. |
| AC-02 | PASS | Every record remains `UNCALIBRATED` and `NOT_READY`. |
| AC-03 | PASS | Identity, status, fields, fixture bytes, and recomputed-digest tampering fail closed. |
| AC-04 | PASS | No claim, novelty, network, mathematical, performance, or public-release authority is introduced. |

## Conclusion

PASS for Q1's local policy boundary only; it does not establish mathematics, literature, calibration performance, production, or public release.
