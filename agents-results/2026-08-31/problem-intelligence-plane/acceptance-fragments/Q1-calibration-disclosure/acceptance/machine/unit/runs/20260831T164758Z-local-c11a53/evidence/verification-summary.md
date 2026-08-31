# Q1 Machine Verification Summary

- Source identity: `c0dcc523ba00de9f660a8e1f1badd887f21de1f7+q1-r1-metadata-migration`
- Runtime: `/opt/homebrew/bin/python3.13`
- Executor: Codex

## Commands

1. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`
   - PASS: 10 tests.
2. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest discover -s tests -p 'test_v02*.py'`
   - PASS: 233 tests, 8 skipped.
3. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile matharc/v02/calibration_disclosure.py tests/test_v02_calibration_disclosure.py`
   - PASS.
4. `git diff --check`
   - PASS.

## Requirement Coverage

- AC-01: direct source-byte and content-digest checks bind accepted R1 evidence, R1 fixture, topic, case order and Q1 records.
- AC-02: a high scientific priority still has `NOT_READY` communication readiness.
- AC-03: identity, status, priority, disclosure limit, field and policy-digest tampering fails closed.
- AC-04: static checks prevent claim, novelty-audit and network dependencies, while the policy always returns `public_release_allowed: false`.

## Boundary

This run proves deterministic local policy behavior over the fixed R1 fixture only. It does not prove mathematics, external literature, open status, novelty, statistical calibration/performance, production behavior or public-release approval.
