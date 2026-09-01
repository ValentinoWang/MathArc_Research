# Acceptance Run: 20260901T112000Z-local-q1c003

- Run ID: 20260901T112000Z-local-q1c003
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 7
- Source identity: bd4ecbecd699d0ea8177ff944d62b4cbcfee6170+q1-r1-accepted-3
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T11:20:00Z
- Completed at: 2026-09-01T11:20:15Z

## Scope

AC-01 through AC-04 for the accepted Q1 v7 local disclosure policy boundary.

## Procedure

Executed `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`, which passed 15/15; compiled the Q1 implementation and protected test and ran `git diff --check`, all with exit 0.

## Requirement disposition

| Requirement | Result | Notes |
| --- | --- | --- |
| AC-01 | PASS | Q1 is bound to `EV-R1-ACCEPTED-3` and current R1 fixture identity. |
| AC-02 | PASS | Every record remains `UNCALIBRATED` and `NOT_READY`. |
| AC-03 | PASS | Identity, field, byte, and digest tampering remain fail-closed. |
| AC-04 | PASS | No proof, novelty, network, performance, or public-release authority. |

## Unverified items

Independent mathematical proof, external literature, reported-open status,
novelty, calibration/statistical performance, production/device behavior, and
public-release authorization remain out of scope.

## Conclusion

PASS for the accepted local Q1 policy boundary only; this run does not authorize public release.
