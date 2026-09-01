# R1 v8 Ablation-Boundary Independent Review

Review date: 2026-09-01

Lane: `ablation-boundary`

Reviewer identity: `r1-ablation-boundary-l3-luna-retry5`

Wrapper: `/Users/vsiyo/.codex/workers/run-l3.sh`

Review mode: independent zero-write review. The sole permitted write is this report.

Scope: R1 contract version 8, AC-01 through AC-05, and the fixed three-case/four-route calculation. This lane cannot accept R1, Q1, or A5.

Frozen input manifest SHA-256: a006cef2287c4dd09415ba1bb1d74763a41c7b99d568d908e24e929f3988df83

## Findings

P0 findings: None.

P1 findings: None.

No P0/P1 issue was found in the assigned ablation-boundary scope.

## Frozen identity

The frozen manifest is:

`agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901-retry5/frozen-inputs.json`

The expected and observed local HEAD are both:

`d0989e55a26b635f8cb97502d6edbbf44a430d20`

The frozen manifest SHA-256 matches the required value above. All 14 declared inputs were present and their observed SHA-256 matched the manifest:

| Input | SHA-256 | Result |
| --- | --- | --- |
| `matharc/v02/regression_evaluation.py` | `a733a72c0d79012bf94fef04af783c2210f23a7e3f8dd8abc3aba179e20bf86d` | MATCH |
| `tests/test_v02_regression_evaluation.py` | `018b6311383a8f495b9f1a916bc027806f724782a03a3f88c9370a7979579350` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json` | `04839d8177b10b4b7749ee953b6bae0771db3ede63a79708ed9da64e6ce1b75c` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/R1.json` | `4369df2e53a6eb4fcc17d9e7b4fc0a5d5c849e2843a9bac699ff5cdcadd4f2fe` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/A4.json` | `85a3e6335bf8e5c886bef328e87f853c8eadc132a793b55ff39a962caae618dd` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json` | `6c5f40b705979caa72d1c7dda05d9dc9a3bca1afd7d6ab982b3297fe48c7610c` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/A5.json` | `58f053e614dded059d62e9cb7984be48d70af5ee1b026621d2bcdbc3de3400b6` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/acceptance-contract.md` | `340b8323a1568c400dd3cc6ca9c9c527050ff2b95d81e15b919cab3babba3689` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/R1.json` | `d035f8776821e2b1410b68ebf975d5919b56fd76f0e6ad4aa0c2cbcb148ecbd5` | MATCH |
| `acceptance/human/R1-regression-evaluation/binding.md` | `c21eda1b84c16d662fc42ee0987d847db617a6ebf3d5e7d56347818180485000` | MATCH |
| `acceptance/human/R1-regression-evaluation/checklist.md` | `56b6658887aa4a68668b70a18fa1262fd6644aa84c9b6d44fc1cdb8c1a8819b4` | MATCH |
| `tests/test_v02_calibration_disclosure.py` | `28a201c4565c40ea5f21c22ca5d107db5b06e328f88afaa43ada3ee21091b520` | MATCH |
| `tests/test_v02_release_decision.py` | `202cc472dcfb959a94f89b4701f0f54c72682d9cacce13f5f09263a6376695fc` | MATCH |
| `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901/ledger.json` | `047cd4334e37604d81d095487a4193d6ad2a41ccbb4d872b1c3cfb7b286a66fe` | MATCH |

The manifest records remote `main` as `226442979a34b8b541b218d4c9b95e6ced0aa08c`. A read-only GitHub API read returned that exact commit with tree `56e27151ded3763bd088027ef318c53c88615411`; local `HEAD^{tree}` is the same tree. The local `origin/main` tracking ref is stale at `ecb751529073f0e9ae3b761ba28e1ccb60ef1cc9` and was not used as remote truth. No fetch, push, ref update, or other remote mutation was performed.

## Independent calculation

The fixture has exactly three cases and exactly four ordered routes per case:

`FORWARD_CITATION`, `ALIAS_AND_EQUIVALENCE`, `STRUCTURAL_SEMANTIC`, `REVIEW_AND_EXPERT_LEAD`.

The independent calculation used the raw fixture hit sets:

`full = union(all route hit sets)`

`incremental(route) = route hits - union(other route hit sets)`

`leave_one_out_loss(route) = full - union(other route hit sets)`

The implementation output matched this calculation for every case and route. The deterministic result digest was `e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d`.

| Case | Full hits | Route increment and leave-one-route-out loss |
| --- | --- | --- |
| `P-FRANKL-Q6` | `frankl-boundary`, `frankl-structure` | `FORWARD_CITATION`: `frankl-boundary`; `STRUCTURAL_SEMANTIC`: `frankl-structure`; `ALIAS_AND_EQUIVALENCE` and `REVIEW_AND_EXPERT_LEAD`: empty |
| `P-ARXIV-2601-22401-COLLISION` | `erdos-397-alias`, `erdos-397-resolution`, `erdos-397-review` | `FORWARD_CITATION`: `erdos-397-resolution`; `ALIAS_AND_EQUIVALENCE`: `erdos-397-alias`; `REVIEW_AND_EXPERT_LEAD`: `erdos-397-review`; `STRUCTURAL_SEMANTIC`: empty |
| `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS` | `q6-residual-boundary` | `STRUCTURAL_SEMANTIC`: `q6-residual-boundary`; all other routes: empty |

Zero-increment routes remain present as valid empty results. The fixed manual minutes are `12`, `28`, and `7`, all finite, non-negative, and within the contract bound. The fixture outcome labels are confined to `hit`, `miss`, and `gap`.

Field-order replay produced the same result. Twelve in-memory negative probes were all rejected by `RegressionValidationError`: unknown field, missing case, extra route, route-order drift, normalized duplicate query, duplicate source, hit tamper, negative/NaN/boolean manual minutes, unknown outcome, and identity digest tamper.

## Commands and results

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_regression_evaluation` | PASS; 6 tests ran, 6 passed, 0 failed |
| `git diff --check` | PASS; exit code 0 |
| Manifest-driven SHA-256 verification | PASS; 14/14 inputs matched |
| Read-only remote commit/tree comparison | PASS; manifest remote commit and live API commit matched, and remote/local tree identity was `56e27151ded3763bd088027ef318c53c88615411` |
| Independent raw-JSON set recomputation | PASS; full coverage, every route increment, every leave-one-route-out loss, and result digest matched |
| Passive-boundary inspection | PASS; evaluator imports only standard-library modules plus local `digest_json`, with no `ResearchTrace`, `ClaimStatus`, `authorize`, HTTP, socket, or subprocess dependency |
| Wrapper inspection | PASS; `/Users/vsiyo/.codex/workers/run-l3.sh` is executable and terminates through `exec codex exec` |

## AC disposition

| AC | Lane-local outcome | Basis |
| --- | --- | --- |
| AC-01 | PASS | Frozen fixture and loader preserve the three accepted case IDs and exactly four ordered, independent route records per case. |
| AC-02 | PASS | Independent set recomputation matched full union, route-exclusive increment, leave-one-route-out loss, sorted output, and deterministic digest for all three cases and all four routes. |
| AC-03 | PASS | Fixed fixture/content and A4/T2/topic identity checks, strict fields, route/query/source uniqueness, closed outcomes, bounded manual minutes, and tamper rejection all passed. |
| AC-04 | PASS | The evaluator is passive and in-memory; source and result-surface checks found no authorization, declaration, `ResearchTrace`, or `ClaimStatus` dependency. |
| AC-05 | PASS for this lane | This report is the persistent zero-write ablation review bound to the frozen manifest, frozen HEAD, declared lane, reviewer identity, wrapper, and terminal PASS. It is not formal R1 acceptance. |

AC-06 and H-01 are outside this requested ablation-boundary lane. This lane does not accept R1, Q1, or A5.

## Protected test and lifecycle boundary

The protected test `tests/test_v02_regression_evaluation.py` matched the frozen SHA-256 `018b6311383a8f495b9f1a916bc027806f724782a03a3f88c9370a7979579350`. The required focused test completed without skips or failures.

Before this report write, R1 evidence was `EV-R1-REOPENED-4` with `acceptance_self_check: blocked` and independent-review disposition `BLOCKED_PENDING_TWO_DURABLE_PASS_REPORTS`. Q1 was `EV-Q1-REOPENED-2` with blocked acceptance self-check. A5 was `EV-A5-REOPENED-2` with proposed state `BLOCKED`, release status `BLOCKED_UPSTREAM_R1_REVIEW`, and no current delivery/publication authorization. These records were inspected only to preserve the required downstream blocked boundary; no acceptance or release decision was made.

## Zero-write scope and residual risks

Only the report path specified by the request was writable. This lane made no source, test, contract, fixture, evidence, SSOT, human-acceptance, peer-report, staging, commit, branch, or remote changes. The retry5 manifest, prompts, and logs were treated as pre-existing lane inputs. All probes used memory or temporary process state and did not write bytecode.

Residual risks remain bounded to the contract:

- Evidence covers only this fixed three-case A4-derived fixture and local route comparison.
- It does not establish mathematical proof, external literature completeness, accuracy, recall, statistical performance, generalization, production behavior, device behavior, or public-release authorization.
- R1 still requires the separate identity-contract lane, convergence by the authorized acceptance owner, and H-01 before formal acceptance. Q1 and A5 remain blocked and require their own authorized revalidation.

Verdict: PASS
