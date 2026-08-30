# MathArc G0-c authoritative local baseline — 2026-08-29

- commit: `5efbfba366cf640a59ee0de93e8b2be4c4d59e40`
- authority: `make ci-full` + `make clean-ci`
- clean-check source: committed `HEAD:.` tree + registry/workflow authorities
- clean-check bootstrap: fresh venv + `.[research,dev,formal]`
- Python: `3.11.15`
- z3: `5.1.0`
- sympy: `1.14.0`
- mypy source-file count (`matharc/v02/**/*.py`): **49**
- unittest discovered/run: **283 / 283**
- unittest skipped: **2**
- SMT discovered/executed/skipped: **20 / 20 / 0**
- published Claude smoke artifacts: **0**
- `make ci-full` exit: **0**
- `make clean-ci` exit: **0**

## Content-addressed milestone artifacts

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `artifacts/v0.1-acceptance.json` | `bda60ac24cd7943587f28a4e500cc8046d1abaf0be397c1451a5628546b59a02` | 11810 |
| `artifacts/v0.2-acceptance.json` | `ab50fc48ee14e00b83a4c85ab44a3424539ac1c847354ecbc929f784f04f6e11` | 5264 |
| `artifacts/frankl-q6-two-small-python.json` | `445c4743f45e71624a1c6e9b8b6484a77fa80b63c69f7aa771bdb3e38d6aadb4` | 5744 |
| `artifacts/ci/unittest-summary.json` | `9cdacfbdf18b9314a879e987dfe3c7dd147fc8e1944f6cf7e6d26fe9de8b2d37` | 1182 |
| `artifacts/ci/capabilities.json` | `6bcaebcb91cb2ca191e72b95dd379a08198e5894f0c6f153dcd01338908ad3c5` | 247 |

## Logs

The full local logs are generated under `artifacts/ci/` and are intentionally not treated as a substitute for the committed summary/digests above.

## Claim boundary

This baseline proves the committed engineering gate reproduced on this machine and in a clean archived checkout. A published Claude smoke row, when present, proves only a sanitized synthetic proposal-only model turn. Neither is evidence that any open mathematical conjecture is solved.
