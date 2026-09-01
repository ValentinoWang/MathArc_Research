# R1 Independent Review: Identity and Contract

- Lane: `identity-contract`
- Reviewer identity: `01a05c23-00d1-7280-b6b8-6d5283f450c9`
- Wrapper: `/Users/vsiyo/.codex/workers/run-l2.sh`
- Runtime: `gpt-5.6-sol`, writable sandbox capability, zero-write review authority
- Zero-write boundary: no source, test, contract, evidence, SSOT, acceptance, or human files were edited; this report is the sole authorized lane write
- Frozen source: `329b270460abf146561499fd5aa7ec4e62737eb1`
- Frozen input manifest SHA-256: `5bc1d1d6a02b2018e4956271dc20497e44a0ef779c0fbcafaf57d4f710add000`
- Authority boundary: this lane cannot accept R1 or change R1, Q1, or A5 state

## Findings

### P0

None.

### P1

1. **The locked R1 protected-test baseline does not match the frozen/current protected test.** Contract v9 declares `tests/test_v02_regression_evaluation.py` SHA-256 `4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6`, but the frozen manifest, current R1 evidence, and `HEAD` contain `cfe0b0451b1a96a07eeb2d7e64fe6b80cff2498948373a740025e83978a6060f`. Git history identifies the contract hash at `8a6d908541b770461a081b43d8ced627befd0912`; commit `0cf567af98f8e32d4ddead6435ea2c49bbb272de` later widened the blocked-evidence and blocked-disposition assertions without updating the approved locked baseline. The frozen manifest proves current-byte integrity, not approval of this protected-test change. AC-01 through AC-06 therefore lack an intact protected-test baseline.

2. **The required focused Q1 suite is red on the frozen R1 fixture identity.** `test_policy_pins_historical_r1_fixture_identity_and_content` expects the Q1 policy's historical R1 fixture digest `04839d8177b10b4b7749ee953b6bae0771db3ede63a79708ed9da64e6ce1b75c`, while `R1_FIXTURE` now resolves to the frozen accepted-A4 fixture digest `9b7fb5c0e63cecde14ee658b4eac7e5b26196ee511ea8a6bbddcfa3dceec0429`. The Q1 suite result is 7 passed, 1 failed. Q1 remains fail closed, but a required focused test failure prevents a PASS identity/contract review.

3. **This two-lane campaign cannot satisfy the contract's distinct-wrapper rule.** Process provenance shows both `ablation-boundary` and `identity-contract` were launched through `/Users/vsiyo/.codex/workers/run-l2.sh`. Contract v9 and the current R1 evidence failure rule reject duplicate wrappers; the human checklist also requires two reports with different wrappers. Distinct sessions alone do not satisfy AC-05/AC-06 convergence.

## Frozen Identity

- `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` both returned `329b270460abf146561499fd5aa7ec4e62737eb1`.
- All 10 `frozen-inputs.json` entries match their declared SHA-256 values. The three frozen test files match the manifest; only the R1 test conflicts with the approved contract's locked baseline.
- A4 evidence is exactly `EV-A4-ACCEPTED-2`, SHA-256 `13a67ddb425c1329d020ac3d757760b860a24481ac9d298f3c56fd69968f9bf7`. Its task-local formal acceptance result resolves to `agents-results/2026-08-31/problem-intelligence-plane/acceptance/release/runs/A4-formal-20260901-0808/result.md`, SHA-256 `03111d4a059a08363f98515b75f797fb79415939e2153c83df4aa5849860177c`; its human result is SHA-256 `7a65f16a9fdcfde2840bbb3ea270e1ac66608fb2788890ba21b398fad0a955d9` and records `PASS`.
- The exact case order is `P-FRANKL-Q6`, `P-ARXIV-2601-22401-COLLISION`, `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS`.
- The exact route order in the fixture, implementation constants, and every case is `FORWARD_CITATION`, `ALIAS_AND_EQUIVALENCE`, `STRUCTURAL_SEMANTIC`, `REVIEW_AND_EXPERT_LEAD`.

## Fail-Closed Boundaries

- R1 rejects unknown or missing fields; A4 evidence ID/digest/head drift; T2, topic, fixture-content, case-order, route-order, status, query-scope, query, source, outcome, manual-minute, and ablation drift.
- Manual minutes must be finite and within `[0, 240]`; outcomes are limited to `hit`, `miss`, and `gap`; route scopes, queries, and sources must remain independent.
- The evaluator has no `ResearchTrace`, `ClaimStatus`, authorization, HTTP, production, or device dependency. R1 remains a passive local fixed-fixture artifact.
- The review gate rejects missing/non-PASS reports, identity or wrapper mismatch, duplicate paths/wrappers/reviewers, symlinks, replayed reports, byte-identical reports, hard links, and frozen-input drift.
- Current R1 evidence and node remain `BLOCKED`; Q1 and A5 remain blocked/non-public. This lane does not convert technical test success into acceptance.

## Exact Commands and Results

```text
$ git rev-parse HEAD
329b270460abf146561499fd5aa7ec4e62737eb1

$ git ls-remote origin refs/heads/main
329b270460abf146561499fd5aa7ec4e62737eb1 refs/heads/main

$ shasum -a 256 agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260902-a4/frozen-inputs.json
5bc1d1d6a02b2018e4956271dc20497e44a0ef779c0fbcafaf57d4f710add000

$ jq -r '.inputs[] | [.sha256,.path] | @tsv' frozen-inputs.json | while read expected/path; do shasum -a 256 "$path"; done
PASS: 10/10 declared inputs matched; 0 mismatches.

$ git show HEAD:tests/test_v02_regression_evaluation.py | shasum -a 256
cfe0b0451b1a96a07eeb2d7e64fe6b80cff2498948373a740025e83978a6060f

$ git show 0cf567a^:tests/test_v02_regression_evaluation.py | shasum -a 256
4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6

$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_regression_evaluation
Ran 7 tests in 0.037s; OK; exit 0.

$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_calibration_disclosure
Ran 8 tests in 0.009s; FAILED (failures=1); exit 1.
Failure: test_policy_pins_historical_r1_fixture_identity_and_content: observed fixture SHA-256 `9b7fb5c0e63cecde14ee658b4eac7e5b26196ee511ea8a6bbddcfa3dceec0429` does not equal policy-pinned `04839d8177b10b4b7749ee953b6bae0771db3ede63a79708ed9da64e6ce1b75c`.

$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_release_decision
Ran 6 tests in 0.006s; OK; exit 0.

$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_regression_evaluation tests.test_v02_calibration_disclosure tests.test_v02_release_decision
Ran 21 tests in 0.039s; FAILED (failures=1); exit 1.
```

## AC Disposition

| Item | Disposition | Basis |
| --- | --- | --- |
| AC-01 | Technical behavior PASS; acceptance BLOCKED | Exact three-case/four-route order passed, but protected-test integrity failed. |
| AC-02 | Technical behavior PASS; acceptance BLOCKED | Deterministic full-route, increment, and leave-one-out tests passed, but protected-test integrity failed. |
| AC-03 | Technical behavior PASS; acceptance BLOCKED | Tamper and identity negative tests passed, but protected-test integrity failed. |
| AC-04 | Technical behavior PASS; acceptance BLOCKED | Passive/no-authority boundary passed, but protected-test integrity failed. |
| AC-05 | NOT SATISFIED | Sibling ablation report is non-PASS and uses the same wrapper as this lane. |
| AC-06 | NOT SATISFIED | This identity/contract lane has P1 findings and cannot issue a PASS report; distinct-wrapper convergence is absent. |
| H-01 | NOT EVALUATED | Its machine-green and two-independent-PASS prerequisites are not met; AI cannot impersonate the required human role. |

## Acceptance Disposition

`NOT READY`. This review supplies findings only and does not accept R1. The acceptance owner must resolve the protected-test baseline through an approved contract/test identity, repair the Q1 historical-fixture reference while preserving Q1's blocked boundary, and rerun the two review lanes with distinct approved wrappers on a newly frozen campaign. Q1 and A5 must not be promoted by this result.

## Residual Risk

The fixed three-case fixture does not establish live literature retrieval, independent mathematical proof, novelty, accuracy, recall, statistical performance, generalization, production/device behavior, monitoring, or public-release authorization. Even after the P1 findings are repaired, those exclusions remain outside R1.

Verdict: FAIL
