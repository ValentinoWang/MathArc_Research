# Acceptance Run: 20260902T061500Z-local-a4a004

- Run ID: 20260902T061500Z-local-a4a004
- Task ID: A4-topic-observation-dogfood
- Lane: machine/integration-contract
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A4-topic-observation-dogfood/acceptance-contract.md
- Contract version: 3
- Contract SHA-256: 5b68d4370e287d3d84d9b97bee597e0966ccd2ad61bc91b99bad3e31184bbe1b
- Source identity: main@f8fa63961a28ec92d4bf90309e824025062ef279
- Runtime identity: local-ci-frozen-a4v3
- Executor or reviewer: acceptance-coordinator
- Started at: 2026-09-02T04:43:43.377108Z
- Completed at: 2026-09-02T04:48:00Z
- Evidence directory: evidence/

## Scope

This machine candidate covers AC-01 through AC-05 for the offline, fixed-source,
non-mathematical-proof, non-public-release A4 slice at `main@f8fa63961a28ec92d4bf90309e824025062ef279`.
It uses the committed A4 v3 contract, T2 evidence, the `reviews-a4v3r2`
closure campaign, and the focused local test suite. It does not exercise H-01,
change `.ssot/nodes/A4.json`, or authorize downstream R1/Q1/A5 work.

## Procedure

1. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_artifact_store_durability tests.test_v02_literature_base tests.test_v02_literature_base_integrity tests.test_v02_topic_observation tests.test_v02_topic_observation_integrity tests.test_v02_dogfood_archives` -> 108 passed, 0 failures, 0 errors, 0 skips.
2. Recomputed protected-test SHA-256 values and compared them with the v3 frozen manifest.
3. Verified the frozen v2-to-v3 patch contains no removed/renamed tests, removed/weakened assertions, or added skip/bypass markers.
4. Verified both independent zero-write closure returns are `PASS` and the campaign records no acceptance authority exercised.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | `agents-results/2026-08-31/problem-intelligence-plane/evidence/T2.json` | T2 three-archive evidence is fixed-source and bounded. |
| AC-02 | PASS | `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/returns/A4-review-luna.json`; `A4-review-sol.json` | Both independent closure lanes pass F1-F4 and the focused suite is green. |
| AC-03 | PASS | `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/frozen-inputs/protected-test-diff-v2-to-v3.patch` | Protected negative tests and contract boundary remain intact. |
| AC-04 | PASS | `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/dispatch.json` | Closure dispatch records two independent zero-write PASS lanes. |
| AC-05 | PASS | `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/frozen-inputs.json` | Contract, protected-test, source and review identities are hash-bound to the frozen campaign. |

## Findings

None within AC-01 through AC-05. The project R1-specific frozen-input validator is
not applicable to this A4 manifest (`input_profile` is A4 closure, not R1 v11);
that version mismatch is recorded as a tooling-scope observation, not promoted
to an A4 acceptance finding.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/T2.json` | 42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3 | Fixed three-archive upstream evidence |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/dispatch.json` | c4c6e960199d3fa0a0e87af4f63121a2a60851e3b4c69e3a9000f22e44b17922 | Closure dispatch and convergence ledger |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/returns/A4-review-luna.json` | 667372d3c69a59d850ca8a86ee37dea159aa066a8cdbe6a2cf6cba81edb98ece | Independent Luna zero-write PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/returns/A4-review-sol.json` | c54d1b31b904b70273834bc0134b657693c481e6be74e5867625154ac47cbd55 | Independent Sol zero-write PASS |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/frozen-inputs.json` | c0d9db825e6319dfccedb2ecf87a3a98a583b0a52bdf94ce1c181aa59d78054f | Frozen A4 closure inputs |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/reviews-a4v3r2/frozen-inputs/protected-test-diff-v2-to-v3.patch` | 2ca89d8e0dcfbbe991e46010c69f1372819497778a68b0679486ae07fd24017e | Protected-test v2-to-v3 integrity diff |

## Unverified items

This run does not prove H-01, formal A4 acceptance, mathematical truth,
external literature confirmation, production/device behavior, statistical
performance, or public-release authorization.

## Conclusion

Machine conclusion: AC-01 through AC-05 are `PASS` for the frozen A4 v3
candidate. This is `EV-A4-ACCEPTED-4` as a machine acceptance candidate only;
it is not formal A4 acceptance. H-01 remains pending explicit user execution.
