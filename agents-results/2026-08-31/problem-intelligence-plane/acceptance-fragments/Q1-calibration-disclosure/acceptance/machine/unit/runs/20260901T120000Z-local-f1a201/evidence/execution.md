# Q1 Machine Execution Evidence

- Candidate source identity: `757feb11c6d6c05bb43332bcf3c1a523a7833a7d+q1-v4-final`
- Runtime: `/opt/homebrew/bin/python3.13`
- Executed at: `2026-09-01T12:00:00Z`

```text
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile matharc/v02/calibration_disclosure.py tests/test_v02_calibration_disclosure.py
git diff --check
```

The selected suite passed 15 tests. The protected tests reject a recomputed policy digest after a field mutation and a changed fixture byte stream. This execution creates no mathematical, external-literature, novelty, calibration-performance, production, or public-release authority.
