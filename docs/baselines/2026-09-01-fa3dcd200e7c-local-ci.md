# MathArc G0-c authoritative local baseline — 2026-09-01

- commit: `fa3dcd200e7c20ae819397d746d347640a6d150a`
- authority: `make ci-full` + `make clean-ci`
- clean-check source: committed `HEAD:.` tree + registry/workflow authorities
- clean-check bootstrap: fresh venv + `.[research,dev,formal]`
- Python: `3.13.7`
- z3: `5.1.0`
- sympy: `1.14.0`
- mypy source-file count (`matharc/v02/**/*.py`): **68**
- unittest discovered/run: **494 / 494**
- unittest skipped: **2**
- SMT discovered/executed/skipped: **20 / 20 / 0**
- published Claude smoke artifacts: **0**
- `make ci-full` exit: **0**
- `make clean-ci` exit: **0**

## Content-addressed milestone artifacts

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `artifacts/v0.1-acceptance.json` | `60f4bd1df31db81161b437a52e1253737257cc76d9ae9d3af39aa41dcc6cf7b6` | 12459 |
| `artifacts/v0.2-acceptance.json` | `d4f08bfe2efc9037ae8f744cd83f565e4d975dda432b587c0dc4720436c2c880` | 5295 |
| `artifacts/frankl-q6-two-small-python.json` | `445c4743f45e71624a1c6e9b8b6484a77fa80b63c69f7aa771bdb3e38d6aadb4` | 5744 |
| `artifacts/ci/unittest-summary.json` | `21ed200f00472c47b3703cc2fdeb4e6e7770a14806803406f620266e28fd8293` | 1204 |
| `artifacts/ci/capabilities.json` | `d1bbea3221661bec028c15e95808f8968cad5bbf161512dc5ef4127856e31a2e` | 239 |

## Logs

The full local logs are generated under `artifacts/ci/` and are intentionally not treated as a substitute for the committed summary/digests above.

## Claim boundary

This baseline proves the committed engineering gate reproduced on this machine and in a clean archived checkout. A published Claude smoke row, when present, proves only a sanitized synthetic proposal-only model turn. Neither is evidence that any open mathematical conjecture is solved.
