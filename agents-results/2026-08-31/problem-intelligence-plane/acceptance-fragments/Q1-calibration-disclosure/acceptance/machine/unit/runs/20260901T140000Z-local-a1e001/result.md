# Acceptance Run: 20260901T140000Z-local-a1e001

- Run ID: 20260901T140000Z-local-a1e001
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 4
- Contract SHA-256: 38cacfefc654acf2b5d5cb9a54e827a5fe83e54937fe957ae4e752b941ecd1fb
- Source identity: 20d41af66b03d037b7e390ce31800fcc9d573a3e+q1-r1-run-id-repair
- Runtime identity: python-3.13
- Executor or reviewer: local-acceptance
- Started at: 2026-09-01T14:00:00Z
- Completed at: 2026-09-01T14:01:00Z
- Evidence directory: evidence/

## Scope

AC-01 through AC-04 for the current R1 evidence identity, the three fixed
uncalibrated disclosure records, fail-closed parsing, and the passive
non-public policy boundary.

## Procedure

Executed `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v
tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`,
then compiled `matharc/v02/calibration_disclosure.py` and its protected test
with Python 3.13 and ran `git diff --check`.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | unit output | Current R1 evidence, fixture, topic, and case identity are closed. |
| AC-02 | PASS | unit output | Every record remains `UNCALIBRATED` and `NOT_READY`. |
| AC-03 | PASS | unit output | Identity, status, fields, fixture bytes, and recomputed-digest tampering fail closed. |
| AC-04 | PASS | static/unit output | No claim, novelty, network, mathematical, performance, or public-release authority is introduced. |

## Findings

None.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| `tests/test_v02_calibration_disclosure.py` | `89d52c973a0d5e026da855aef85a57db8656e6cc5b593b98f09ff6d2541318db` | Protected AC-01 through AC-04 test file. |
| `evidence/R1.json` | `073fecdfae5f7ca8c8adc946959b3fd030b60d3c8960b22230d2256b7679114c` | Current accepted upstream R1 evidence. |
| `evidence/q1-fixtures/uncalibrated-disclosure-policy.json` | `566533a91201ee353ef80efd13e7e039e21692b4ef5334a8a55e940cccf58064` | Current fixed Q1 policy fixture. |
| `matharc/v02/calibration_disclosure.py` | `1a56ac0e25023e7103adc4c18e9ce50157bb6f58dee57247aba22ada5a352b50` | Local policy implementation. |

## Unverified items

Independent mathematical proof review, external literature retrieval,
reported-open verification, novelty acceptance, calibration or statistical
performance, production/device behavior, and public-release authorization.

## Conclusion

PASS for Q1's local policy boundary only. This run does not establish
mathematics, literature, calibration performance, production, or public
release.
