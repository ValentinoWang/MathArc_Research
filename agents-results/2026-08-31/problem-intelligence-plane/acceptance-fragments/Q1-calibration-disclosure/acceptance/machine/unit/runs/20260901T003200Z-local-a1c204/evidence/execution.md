# Q1 Machine Execution Evidence

- Candidate source identity: `8a6d908541b770461a081b43d8ced627befd0912+q1-v4-final`
- Runtime: `/opt/homebrew/bin/python3.13`
- Executed at: `2026-09-01T00:33:00Z`

## Commands

```text
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile matharc/v02/calibration_disclosure.py tests/test_v02_calibration_disclosure.py
git diff --check
```

## Result

All 14 selected unit tests passed. Compilation and whitespace validation passed.
This run validates only Q1 AC-01 through AC-04; it does not accept mathematics, external literature, novelty, calibration performance, production behavior, or public release.
