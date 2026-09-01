Lane: `ablation-boundary`
Reviewer identity: `r1-ablation-boundary-luna-low-retry11`
Wrapper: `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901-retry11/workers/run-luna-low.sh`
Review mode: zero-write

Frozen head: `eaf433c168dd30417968fbf4a32cd4bbc050d2ae` (verified against git HEAD).
Frozen input manifest SHA-256: 75fa2c6194433f84eddfa861942a38eb740120db17aa3b5eeb5f8bbc86fb92f6

Zero-write compliance: PASS. No files were written before this assigned report; no skills, agents, network, release workflow, or remote action was used. This report is the only write.

Exact results: all 14 manifest entries matched their recorded SHA-256 values. The R1 contract contains the protected test hash `4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6`. `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q tests.test_v02_regression_evaluation` completed with 7 tests and `OK`.

P0/P1 findings: none. `regression_evaluation.py` fail-closes fixture identity, route order, case order, route/query/source independence, bounded minutes, and fixed content digest; evaluation recomputes full coverage, route increments, and leave-one-out loss. `four-route-regression.json` contains the fixed three cases and four ordered routes with hit/miss/gap labels and unresolved boundaries. No P0/P1 issue or ablation-boundary overclaim was found.

AC-01: PASS. Three fixed cases and exactly four ordered independent routes per case are enforced and present.
AC-02: PASS. Full-route hits, route-exclusive increments, leave-one-out losses, and hit/miss/gap labels are deterministically recomputed.
AC-03: PASS. Identity, scope, query, source, content digest, hit data, and manual-minute tampering are fail-closed by the implementation and protected tests.
AC-04: PASS. The evaluated result is passive and contains no authorization, declaration, ResearchTrace, or ClaimStatus dependency.
AC-05: PASS for this lane’s local checks and report production on the frozen inputs.
AC-06: Not assessed by this ablation-boundary lane; this report does not establish the independent identity-contract review.

Residual limits: this is a small fixed three-case route comparison only. It does not establish mathematical proof, external literature confirmation, statistical performance, accuracy, recall, generalization, production/device behavior, or public release. This review does not accept R1 and does not transition Q1/A5.

Verdict: PASS
