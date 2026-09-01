# Acceptance Run: 20260901T022009Z-local-a5g001

- Run ID: 20260901T022009Z-local-a5g001
- Task ID: A5-problem-intelligence-v0-release
- Lane: machine/static
- Status: CANDIDATE
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A5-problem-intelligence-v0-release/acceptance-contract.md
- Contract version: 5
- Contract SHA-256: c2b72b10c53e7ed1589de2fd378b4da6e4c44c1b3a6193119c593a9271d7a9a0
- Source identity: 20d41af66b03d037b7e390ce31800fcc9d573a3e+a5-v5-q1-v5
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T02:20:09Z
- Completed at: 2026-09-01T02:20:09Z
- Evidence directory: evidence/

## Scope

Candidate static verification for AC-01 through AC-03 only: fixed Q1 v5 identity closure, source-only scope, and required post-push remote-ref readback. It cannot make the existing A5 handoff ready before its monotonic `ready_at`.

## Procedure

Ran `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_release_decision tests.test_v02_calibration_disclosure`, Python compilation of both protected tests, and `git diff --check`.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | `tests/test_v02_release_decision.py` | Fixed Q1 v5 evidence, code, protected test, node, execution contract, frozen inputs, ledger, and distinct review bytes are bound. |
| AC-02 | PASS | `tests/test_v02_release_decision.py` | The exact source scope and all six prohibitions remain enforced. |
| AC-03 | PASS | `tests/test_v02_release_decision.py` | Pre-push delivery remains false; an exact remote-main readback is mandatory. |

## Findings

None.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| A5 v5 contract | c2b72b10c53e7ed1589de2fd378b4da6e4c44c1b3a6193119c593a9271d7a9a0 | Locked contract used for this run |
| Q1 v5 ledger | 53bd3643f9dafe03aa821a8fc61678f71e804b371b09b86a3435b09430e739b4 | Detached current Q1 reconciliation closure |

## Unverified items

Mathematical proof, literature or reported-open-status truth, novelty, calibration/statistical performance, production/device behavior, public research communication, or completed GitHub delivery.

## Conclusion

Candidate verification passed for the bounded A5 source-scope contract only. This record neither supersedes the existing handoff nor performs GitHub delivery or authorizes a research conclusion.
