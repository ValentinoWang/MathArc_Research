# A4 Regression Review

- Review lane: regression-scope, read-only
- Source SHA: `3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
- Remote SHA: `3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
- Worktree: clean before and after review

## Commands

- `.venv/bin/python -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives`: `41` passed, exit `0`.
- `.venv/bin/python -m unittest -v tests.test_v02_console_export tests.test_v02_console_topic`: `14` passed, exit `0`.
- `.venv/bin/python -m unittest discover -s tests -p 'test_v02*.py'`: `315` passed, `8` skipped, exit `0`.
- `.venv/bin/python -m unittest discover -s tests`: `513` passed, `2` skipped, exit `0`.
- `node scripts/console_browser_gate.mjs`: exit `0`; `52 cases x 2 campaigns x 6 widths`, mobile viewport checks, keyboard checks, M1 SSE and M2 review workflow passed.
- `git diff HEAD^ HEAD --check`: exit `0`.

## Protected hashes

| Path | SHA-256 | Result |
| --- | --- | --- |
| `matharc/v02/topic_observation.py` | `16743b6097480044253c50fc8188b65a23062e5f57435361863311b1483a80e1` | PASS |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` | PASS |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` | PASS |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | PASS |

The four hashes match the protected hashes recorded by the prior A4 formal run.

## Scope review

The current commit adds read-only R1 route-regression and T2 dogfood-archive projections in `matharc/v02/console_export.py`, corresponding prototype rendering, browser assertions, and focused export tests. Existing A4 state/replay/manual-queue behavior is unchanged and the protected A4 suites remain non-vacuous with no removed assertions or skips. New console tests verify fixed route order, three-case projections, non-promotion flags, read-only behavior, and workspace provenance. Browser coverage verifies live projections, responsive widths, keyboard activation, SSE reconnect, and review workflows.

No P0, P1, or P2 regression was found in this lane. The projections remain fixture-only/read-only and do not authorize mathematical conclusions, public release, or external literature claims. Existing environment-dependent skips are residual harness conditions, not introduced by this commit.

## Verdict

`PASS` for the regression-scope lane. This report is independent verification evidence and does not itself change A4 SSOT state or grant acceptance authority.
