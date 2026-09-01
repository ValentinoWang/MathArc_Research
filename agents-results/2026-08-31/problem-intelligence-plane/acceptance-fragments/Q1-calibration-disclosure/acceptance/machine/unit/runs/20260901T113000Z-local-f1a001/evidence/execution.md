# Q1 Machine Execution Evidence

- Candidate source identity: `8a6d908541b770461a081b43d8ced627befd0912+q1-v4-integrity-final`
- Runtime: `/opt/homebrew/bin/python3.13`
- Executed at: `2026-09-01T00:41:00Z`

```text
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile matharc/v02/calibration_disclosure.py tests/test_v02_calibration_disclosure.py
git diff --check
```

The selected suite passed 15 tests. The red proof includes a recomputed policy digest after a field mutation and an altered fixture byte stream; both are rejected. This run has no mathematical, external-literature, novelty, calibration-performance, production, or public-release authority.
