# Q1 Machine Verification Summary

- Source identity: `c0dcc523ba00de9f660a8e1f1badd887f21de1f7`
- Runtime: `/opt/homebrew/bin/python3.13`
- Executor: Codex
- Completed at: 2026-08-31T16:43:04Z

## Commands

1. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`
   - PASS: 10 tests.
2. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest discover -s tests -p 'test_v02*.py'`
   - PASS: 233 tests, 8 skipped.
3. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest discover -s tests`
   - PASS: 400 tests, 10 skipped.
4. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile matharc/v02/calibration_disclosure.py tests/test_v02_calibration_disclosure.py`
   - PASS.

## Requirement Coverage

- AC-01: direct source-byte and content-digest checks bind the accepted R1 evidence, R1 fixture, topic, case order and Q1 records.
- AC-02: the high-priority first case still has `NOT_READY` communication readiness.
- AC-03: identity, status, priority, disclosure limits, public flag, cardinality, unknown-field and policy-digest changes fail closed.
- AC-04: static checks prevent claim, novelty-audit and network dependencies, while the policy always returns `public_release_allowed: false`.

## Boundary

This run proves only deterministic local policy behavior over the fixed R1 fixture. It does not prove mathematical results, open status, novelty, external retrieval, statistical calibration/performance, production behavior or public-release approval.
