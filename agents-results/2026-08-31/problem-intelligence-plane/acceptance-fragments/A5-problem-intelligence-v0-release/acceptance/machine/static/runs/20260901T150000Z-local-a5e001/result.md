# Acceptance Run: 20260901T150000Z-local-a5e001

- Run ID: 20260901T150000Z-local-a5e001
- Task ID: A5-problem-intelligence-v0-release
- Lane: machine/static
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A5-problem-intelligence-v0-release/acceptance-contract.md
- Contract version: 4
- Contract SHA-256: 381844e59b716836204bc1d29ee888f1b289196e0da00cea9006adccd88b6aae
- Source identity: 20d41af66b03d037b7e390ce31800fcc9d573a3e+a5-v4-current-q1
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T01:38:32.808700Z
- Completed at: 2026-09-01T15:01:00Z
- Evidence directory: evidence/

## Scope

AC-01 through AC-03 only: byte-bind the current accepted Q1 evidence and all protected Q1 inputs, verify that the release scope is repository-source delivery only, and require a post-push remote `main` ref readback before a GitHub-delivery claim.

## Procedure

Ran `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_release_decision tests.test_v02_calibration_disclosure`, `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile tests/test_v02_release_decision.py tests/test_v02_calibration_disclosure.py`, and `git diff --check`.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | `tests/test_v02_release_decision.py` | Current Q1 evidence, fixture/digest, implementation, and protected-test bytes are bound. |
| AC-02 | PASS | `tests/test_v02_release_decision.py` | The exact source scope and all six prohibitions are enforced. |
| AC-03 | PASS | `tests/test_v02_release_decision.py` | Pre-push delivery is false and an exact remote-ref readback is mandatory. |

## Findings

None.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| `evidence/acceptance-contract.md` | 381844e59b716836204bc1d29ee888f1b289196e0da00cea9006adccd88b6aae | Locked A5 v4 contract snapshot |

## Unverified items

Mathematical proof, literature or reported-open-status truth, novelty, calibration/statistical performance, production/device behavior, public research communication, or a completed GitHub delivery.

## Conclusion

PASS for the bounded A5 source-scope contract only. This run does not perform a GitHub delivery and authorizes no research conclusion.
