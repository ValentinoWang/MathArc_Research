# A4 Formal Acceptance Release Run

- Run ID: A4-formal-20260901-0808
- Task ID: A4
- Lane: release
- Status: PASS / ACCEPTED
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A4-topic-observation-dogfood/acceptance-contract.md
- Contract version/hash: 1 / 20b8a9d31279d98d7cfce69f234d35396f310a0e811efa550fc10d2d03256afa
- Approved baseline: user-approved `main` HEAD `b4c6d36`
- Formal source identity: `main@5af1d9ff6fde02d86633cca50cf815ef04661d4a`
- Runtime identity: local offline release review; fixed checked-in bytes; no external network retrieval
- Reviewer/acceptance owner: release-review owner plus user (研究负责人/仓库所有者)
- Boundary: offline, source-fixed, non-mathematical-proof, non-public-release

## Findings

None at P0/P1. Three independent AI lanes returned `proposed_state: VERIFIED`; none claimed authority to accept A4. The only residual diagnostics are pre-existing `ResourceWarning` messages and ten environment-dependent skipped tests; neither changes the A4 source-level scope.

## Protected-test integrity

| Path | Expected SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| tests/test_v02_topic_observation.py | 1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56 | 1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56 | PASS |
| tests/test_v02_dogfood_archives.py | e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873 | e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873 | PASS |

## Requirements-test traceability

| Requirement | Evidence | Result |
| --- | --- | --- |
| AC-01 fixed three archives and non-promotion | T2 evidence `42e5e599...`; archive-boundary return `e361f320...` | PASS |
| AC-02 replay/recovery/dedup/budget/fail-closed | focused 41/41; state-integrity return `a3c9348c...` | PASS |
| AC-03 immutable contract metadata | negative test `test_contract_boundary_and_fixture_directory_are_immutable`; archive-boundary return | PASS |
| AC-04 full regression, browser, technical preflight | 510 passed/10 skipped; browser 52x2x6; `make publication-gate` PASS | PASS |
| AC-05 frozen identity and independent review hashes | node/edge/T2/contract hashes and three lane returns below | PASS |
| H-01 bounded human acceptance | human run `20260901T081500Z-local-a4f001`, result `7a65f16a...` | ACCEPTED |

## Independent AI review lanes

| Lane | Return | SHA-256 | Verdict |
| --- | --- | --- | --- |
| state-integrity | acceptance/release/runs/A4-formal-20260901-0808/returns/state-integrity.md | a3c9348c7fcdfcdea2a77234109b8b7c7ae99fd8247f4849285ea48391c0a6ed | VERIFIED |
| archive-boundary | acceptance/release/runs/A4-formal-20260901-0808/returns/archive-boundary.md | e361f32031394d985e310b6fc97dd93b9568b76b7769958be87501dc244d8a01 | VERIFIED |
| regression-ssot | acceptance/release/runs/A4-formal-20260901-0808/returns/regression-ssot.md | 4cc66651501e8085349e0690f4950f512e51afc652a9983523f8dd5a51b5e946 | VERIFIED |

All lanes used independent `run-l2.sh` processes with writable sandbox capability but zero-write task authority. Their logs and prompts are retained under this run; completed worker processes were terminated after returns were recorded.

## Machine verification

- Focused A4 suites: `41 passed`.
- Full suite: `510 passed, 10 skipped`.
- Browser gate: `52 cases x 2 campaigns x 6 widths`; M1 SSE event 4 refresh/reconnect and M2 queue/bundle/rejection/token/approval workflow passed.
- Publication technical preflight: PASS; fixture-only, no paper or publication authorization.
- `git diff --check`: PASS.
- Remote readback: `git ls-remote origin refs/heads/main` returned `5af1d9ff6fde02d86633cca50cf815ef04661d4a`; local `HEAD` equals remote.

## Explicit exclusions

This acceptance is not a mathematical proof, independent proof review, live external-literature confirmation, production/device evidence, statistical performance claim, or public-release authorization. The fixed sources are observations and audit fixtures only. R1 remains downstream and must be re-bound separately after this accepted A4 result.

## Decision

- State: `ACCEPTED`
- Proven scope: A4 one-shot topic observation plus the three checked-in source-pinned dogfood archives, their replay/recovery/deduplication/budget/manual-queue integrity, and fail-closed boundaries.
- Conditions: none within this bounded scope; downstream R1/Q1/A5 require fresh independent acceptance and retain their own non-public/non-mathematical boundaries.
- Residual risk: skipped environment-specific tests and all excluded external/research claims remain unresolved by design.
