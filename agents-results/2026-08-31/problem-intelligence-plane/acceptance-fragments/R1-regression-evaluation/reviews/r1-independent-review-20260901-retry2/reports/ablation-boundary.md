## Reviewer identity

- Assigned lane: `r1-ablation-boundary-l3-luna-retry2`.
- Scope: R1 contract v4 ablation boundary only; zero-write review except this report. This lane has no acceptance authority.

## Frozen identity

- Frozen input manifest: `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901-retry2/frozen-inputs.json`.
- Frozen input manifest SHA-256: `4878c7b30f5e289e733a513afd8e17aee336e46b9752a4a5a574fa5d30216420`.
- HEAD: `0a58bf984ef2764bafe0c2b26d1d6cefdec43783`.
- All 12 declared frozen files are present and their observed SHA-256 values match the manifest.

## P0/P1 findings

None. No P0 or P1 finding was identified in the assigned R1 boundary.

## Commands and results

- `git rev-parse HEAD`: PASS; exact frozen HEAD matched.
- Manifest/hash verification: PASS; manifest digest matched and all 12 input hashes matched.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_regression_evaluation`: PASS; 5 tests ran, all passed, process exit 0.
- Read-only `RegressionSuite.from_dict(...).evaluate()` probe: PASS; 3 cases and 4 routes per case produced deterministic full-hit sets, incremental hits, and leave-one-route-out losses. Result digest was `e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d`.
- Source/import boundary scan: PASS; `regression_evaluation.py` only imports local digest support plus standard-library modules and contains no `ResearchTrace`, `ClaimStatus`, authorization, or network behavior.

## R1 criterion disposition

- AC-01: PASS. The frozen fixture has the three accepted case IDs, exact ordered four-route records per case, unique normalized route scopes and queries, and globally unique route source IDs.
- AC-02: PASS. Full coverage is the union of route hit sets; incremental hits remove hits found by other routes; leave-one-route-out loss is recomputed from the full union. Results are sorted and deterministic.
- AC-03: PASS. Strict fields, fixed content digest, A4/T2/topic/case identities, route independence, and finite non-negative manual minutes bounded at 240 reject tampering or drift. Hit/miss/gap labels are closed and bounded.
- AC-04: PASS. The evaluator is passive and does not import or write `ResearchTrace`, `ClaimStatus`, authorization, or network state.
- AC-05: PASS for this ablation-boundary lane after persistence of this report. Overall R1 remains blocked until both required distinct durable PASS reports exist.
- AC-06: Not assessed by this lane; it remains the separate identity-contract review requirement.
- Active R1 evidence is `EV-R1-REOPENED-2` with a blocked acceptance self-check and `BLOCKED_PENDING_TWO_DURABLE_PASS_REPORTS` disposition. Implementation readiness does not override that acceptance blocker. Q1 and A5 are checked only as downstream blocked lifecycle records; this lane cannot accept R1, Q1, or A5.

## Protected-test integrity

- Protected path: `tests/test_v02_regression_evaluation.py`.
- Expected SHA-256: `a8320b5af5c000515b0cd0bb5bc177fa4acc87ee9da63439f80f25edf26022cf`.
- Observed SHA-256: `a8320b5af5c000515b0cd0bb5bc177fa4acc87ee9da63439f80f25edf26022cf`.
- Disposition: PASS. The protected test exists, is frozen, has no observed weakening or broad skip, and the focused run passed.

## Residual risk

- Evidence covers only the fixed three-case A4 fixture. It does not establish mathematical proof, external literature status, statistical performance, generalization, production behavior, or public-release authorization.
- This report supplies only the ablation lane result. The independent identity-contract report is still required before R1 can leave its blocked state; Q1 and A5 must not be promoted by this lane.
- Human acceptance H-01 and final R1 acceptance are outside this lane.

## Verdict

Verdict: PASS
proposed_state: REVIEWED

This is an independent review-lane result only. This lane cannot accept R1, Q1, or A5.
