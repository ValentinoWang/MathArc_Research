# R1 Ablation-Boundary Independent Review

- Review date: 2026-09-01
- Reviewer identity: `r1-ablation-boundary-l3-luna-retry4`
- Wrapper: `/Users/vsiyo/.codex/workers/run-l3.sh`
- Review mode: independent, zero-write review; the only write made by this lane is this report
- Scope: R1 contract-v7 AC-01 through AC-05 only

Frozen input manifest SHA-256: d7fcfb268f97dc0a9d013356b90faa8fb07f542b09e6649ad0dfb63fe19b1534

## Frozen identity

Frozen HEAD expected and observed:

`d4b3396d786c1fed0a8405dc419ad483fa2acf41` -> `d4b3396d786c1fed0a8405dc419ad483fa2acf41` - PASS

The manifest SHA-256 matched the required value. Every manifest-listed input existed and its observed SHA-256 matched the frozen value:

| Input | Expected SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| `matharc/v02/regression_evaluation.py` | `a733a72c0d79012bf94fef04af783c2210f23a7e3f8dd8abc3aba179e20bf86d` | `a733a72c0d79012bf94fef04af783c2210f23a7e3f8dd8abc3aba179e20bf86d` | PASS |
| `tests/test_v02_regression_evaluation.py` | `91a588052e9d32e688bb677503628c304ac5ff2420cbd756d4769e513651b6ff` | `91a588052e9d32e688bb677503628c304ac5ff2420cbd756d4769e513651b6ff` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json` | `04839d8177b10b4b7749ee953b6bae0771db3ede63a79708ed9da64e6ce1b75c` | `04839d8177b10b4b7749ee953b6bae0771db3ede63a79708ed9da64e6ce1b75c` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/R1.json` | `42a24a7479694a2f5898f4b91d2535582d6d07afe477432950331c4be16e3cb8` | `42a24a7479694a2f5898f4b91d2535582d6d07afe477432950331c4be16e3cb8` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/A4.json` | `85a3e6335bf8e5c886bef328e87f853c8eadc132a793b55ff39a962caae618dd` | `85a3e6335bf8e5c886bef328e87f853c8eadc132a793b55ff39a962caae618dd` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json` | `6c5f40b705979caa72d1c7dda05d9dc9a3bca1afd7d6ab982b3297fe48c7610c` | `6c5f40b705979caa72d1c7dda05d9dc9a3bca1afd7d6ab982b3297fe48c7610c` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/A5.json` | `58f053e614dded059d62e9cb7984be48d70af5ee1b026621d2bcdbc3de3400b6` | `58f053e614dded059d62e9cb7984be48d70af5ee1b026621d2bcdbc3de3400b6` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/acceptance-contract.md` | `bdb31169e0d401e7a4ed804a16f958a2126a921787b2c294d61b74f6fbbd8e63` | `bdb31169e0d401e7a4ed804a16f958a2126a921787b2c294d61b74f6fbbd8e63` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/R1.json` | `d035f8776821e2b1410b68ebf975d5919b56fd76f0e6ad4aa0c2cbcb148ecbd5` | `d035f8776821e2b1410b68ebf975d5919b56fd76f0e6ad4aa0c2cbcb148ecbd5` | PASS |
| `acceptance/human/R1-regression-evaluation/binding.md` | `007feca22546861c941a3daf4f1e55c776c0594d938b8f05803ddb05ddb7acce` | `007feca22546861c941a3daf4f1e55c776c0594d938b8f05803ddb05ddb7acce` | PASS |
| `acceptance/human/R1-regression-evaluation/checklist.md` | `7e6a2b8efba2926e2ceda5878938c51e494bf91622ddfcaee73ba9271126db08` | `7e6a2b8efba2926e2ceda5878938c51e494bf91622ddfcaee73ba9271126db08` | PASS |
| `tests/test_v02_calibration_disclosure.py` | `b9188cdbf0aa2a556c55a7341c9e461a7f54dc864d938212e2bffb0eed2b8a94` | `b9188cdbf0aa2a556c55a7341c9e461a7f54dc864d938212e2bffb0eed2b8a94` | PASS |
| `tests/test_v02_release_decision.py` | `202cc472dcfb959a94f89b4701f0f54c72682d9cacce13f5f09263a6376695fc` | `202cc472dcfb959a94f89b4701f0f54c72682d9cacce13f5f09263a6376695fc` | PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901/ledger.json` | `047cd4334e37604d81d095487a4193d6ad2a41ccbb4d872b1c3cfb7b286a66fe` | `047cd4334e37604d81d095487a4193d6ad2a41ccbb4d872b1c3cfb7b286a66fe` | PASS |

## Findings

P0 findings: None.

P1 findings: None.

No frozen identity mismatch, implementation defect, ablation calculation defect, tamper-boundary bypass, passive-boundary violation, or protected-test integrity failure was found in this assigned lane.

## Current lifecycle boundary

The current R1 evidence is `EV-R1-REOPENED-3` with `acceptance_self_check: blocked` and independent-review disposition `BLOCKED_PENDING_TWO_DURABLE_PASS_REPORTS`. I read this only to confirm that R1 remains blocked pending the review campaign; this lane does not change or accept that lifecycle.

Q1 is recorded as `EV-Q1-REOPENED-2`, `proposed_state: BLOCKED`, and requires R1 reacceptance before Q1 is revalidated. A5 is recorded as `EV-A5-REOPENED-2`, `proposed_state: BLOCKED`, with release status `BLOCKED_UPSTREAM_R1_REVIEW` and no current delivery/publication authorization. These were inspected only for the required blocked lifecycle.

This lane cannot accept R1, Q1, or A5. The terminal PASS below is only the result of this ablation-boundary review lane; it is not an R1, Q1, or A5 acceptance or release decision.

## Independent engineering check

The R1 contract-v7 binds a fixed three-case fixture and exactly four ordered routes per case. `RegressionSuite.from_dict` verifies the fixture kind/version, topic, A4 evidence identity, A4 source HEAD, T2 fixture digest, route order, case order, canonical fixture content digest, case status, bounded finite manual minutes, sorted closed outcome labels, route shape, normalized query-scope/query independence, source identity uniqueness, and exact route source identity. `RegressionSuite.evaluate` computes the full hit union, each route's exclusive increment, and each leave-one-route-out loss from sets; it does not consume an asserted ablation result.

The fixed fixture loaded as three cases with four routes each. An independent calculation from the raw JSON hit sets matched every full union, route increment, and leave-one-out loss returned by the implementation. The returned evaluation digest was:

`e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d`

The independent result was:

| Case | Full hits | Non-zero route increments and leave-one-out losses |
| --- | --- | --- |
| `P-FRANKL-Q6` | `frankl-boundary`, `frankl-structure` | `FORWARD_CITATION: frankl-boundary`; `STRUCTURAL_SEMANTIC: frankl-structure` |
| `P-ARXIV-2601-22401-COLLISION` | `erdos-397-alias`, `erdos-397-resolution`, `erdos-397-review` | `FORWARD_CITATION: erdos-397-resolution`; `ALIAS_AND_EQUIVALENCE: erdos-397-alias`; `REVIEW_AND_EXPERT_LEAD: erdos-397-review` |
| `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS` | `q6-residual-boundary` | `STRUCTURAL_SEMANTIC: q6-residual-boundary` |

Zero-increment routes were retained as empty results. Manual minutes were `12`, `28`, and `7`, all within the contract bound.

## Commands and results

| Command | Result |
| --- | --- |
| `shasum -a 256 agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901-retry4/frozen-inputs.json` | PASS; observed `d7fcfb268f97dc0a9d013356b90faa8fb07f542b09e6649ad0dfb63fe19b1534` |
| `git rev-parse --verify HEAD` | PASS; observed `d4b3396d786c1fed0a8405dc419ad483fa2acf41` |
| Manifest-driven SHA-256 verification for all listed inputs | PASS; all expected and observed hashes match |
| `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_regression_evaluation` | PASS; 5 tests ran, 5 passed, 0 failed |
| `git diff --check` | PASS; exit code 0 |
| Independent raw-JSON set recomputation | PASS; full/increment/leave-one-out results matched; evaluation digest `e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d` |
| Independent tamper checks for unknown fields, route/case count/order, normalized duplicate query, duplicate source, NaN/boolean manual minutes, unknown outcome, and empty query | PASS; all 9 candidates rejected by `RegressionValidationError` |
| Passive source check for `ResearchTrace`, `ClaimStatus`, `authorize`, and HTTP dependency | PASS; no forbidden dependency or network reference in the evaluator source |
| Wrapper inspection: `/Users/vsiyo/.codex/workers/run-l3.sh` | PASS for required wrapper identity; executable and terminates through `exec codex exec` |

The pre-report repository check showed `## main...origin/main`, no tracked diff, and only the pre-existing untracked retry4 manifest/log/prompt files. No source, test, contract, evidence, SSOT, human acceptance, peer report, staging, branch, remote, or commit path was changed by this review.

## AC disposition

| AC | Disposition | Basis |
| --- | --- | --- |
| AC-01 | PASS | Frozen fixture and loader preserve exactly three accepted case IDs and four ordered independent route records per case; focused test and independent count check passed. |
| AC-02 | PASS | Full route union, route-exclusive increments, and leave-one-route-out losses were independently recomputed from raw hit sets and matched the implementation; deterministic focused test passed. |
| AC-03 | PASS | Frozen identity/content digest and strict deserialization rejected identity, structure, route, query, source, outcome, manual-minute, and ablation-related tamper candidates; focused negative tests and independent negative checks passed. |
| AC-04 | PASS | Evaluator is a passive in-memory calculation boundary. The focused source guard passed and the source contains no `ResearchTrace`, `ClaimStatus`, `authorize`, or HTTP dependency. |
| AC-05 | PASS | This independent zero-write lane is bound to the verified frozen manifest and HEAD, uses the declared reviewer identity and wrapper, and writes this persistent terminal PASS report. |

AC-06 and H-01 were not reviewed or disposed by this lane because they are outside the requested AC-01 through AC-05 ablation-boundary scope.

## Protected-test integrity

The contract-declared protected test is `tests/test_v02_regression_evaluation.py`. Contract hash, frozen-manifest hash, and observed file hash all equal:

`91a588052e9d32e688bb677503628c304ac5ff2420cbd756d4769e513651b6ff`

The protected test exists, ran without skips or failures in the required focused command, and has no tracked working-tree modification. The ancillary calibration and release test inputs listed by the frozen manifest also matched their frozen hashes; they were not evaluated for Q1/A5 acceptance.

## Residual risk

- The evidence covers only the fixed three-case, four-route fixture. It does not establish mathematical truth, external literature completeness, statistical accuracy/recall, generalization, production behavior, or device behavior.
- R1 remains lifecycle-blocked until the separate required independent review lane(s) and all other applicable acceptance conditions are completed by their authorized owners. This report does not alter that state.
- Q1 and A5 remain blocked and require their own authorized revalidation/reacceptance after upstream lifecycle conditions; this lane supplies no Q1 or A5 evidence.

Verdict: PASS
