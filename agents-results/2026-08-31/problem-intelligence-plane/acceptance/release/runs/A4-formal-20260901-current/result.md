# A4 Formal Acceptance Release Run

- Run ID: A4-formal-20260901-current
- Task ID: A4-topic-observation-dogfood
- Lane: release
- Status: PASS / ACCEPTED
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A4-topic-observation-dogfood/acceptance-contract.md
- Contract version/hash: 2 / 4b7ac7ea035d59be7c87fef9867b97529f8b00f68c207d7460963cd625095c84
- Implementation candidate identity: `main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
- Delivery readback identity: `origin/main@b70bac26f01046cba5d219395e48b8c5a8515815`
- Runtime identity: local offline release review; fixed checked-in bytes; no external network retrieval
- Reviewer/acceptance owner: release-review owner plus user（研究负责人/仓库所有者）
- Boundary: offline, source-fixed, non-mathematical-proof, non-public-release

## Findings and resolution

The identity lane initially reported a P1 because the current serial result and
node state did not yet exist. That finding was resolved in this serial synthesis
by binding the current contract, human run, three durable review returns, local
CI, remote readback, and the final A4 node/evidence update to one source identity.
No implementation P0/P1/P2 finding remains within scope.

## Protected-test integrity

| Path | SHA-256 | Result |
| --- | --- | --- |
| tests/test_v02_topic_observation.py | 1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56 | PASS |
| tests/test_v02_dogfood_archives.py | e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873 | PASS |

## Requirements-test traceability

| Requirement | Evidence | Result |
| --- | --- | --- |
| AC-01 fixed three archives and non-promotion | evidence/T2.json SHA 42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3 | PASS |
| AC-02 replay/recovery/dedup/budget/fail-closed | focused topic/archive 41/41; archive review SHA 215fc35ed55def0f6c19a2bce1702cd0a8a2fb91713a7df749360446ef206f77 | PASS |
| AC-03 immutable contract metadata | protected negative tests; archive review | PASS |
| AC-04 local CI, browser, technical preflight | local `make ci-full PYTHON=.venv/bin/python` exit 0; 513 tests, 2 skips, 20/20 SMT; browser 52x2x6 | PASS |
| AC-05 current identity and independent review binding | current contract/binding/checklist, remote readback, three review-lane reports | PASS |
| H-01 bounded human acceptance | acceptance/human/A4-topic-observation-dogfood/runs/20260901T141500Z-local-a4f002/result.md | PASS |

## Independent AI review lanes

| Lane | Return | SHA-256 | Verdict |
| --- | --- | --- | --- |
| identity/readiness | acceptance/release/runs/A4-formal-20260901-current/evidence/review-lanes/identity-review.md | 28410474cc3b801807109a4d05b8f9317ec85c8cb107e1462f6cd3cff651ae2b | FAIL before serial closure; closure recorded above |
| archive/state | acceptance/release/runs/A4-formal-20260901-current/evidence/review-lanes/archive-review-fresh.md | 0e1c76b5a16b250425d26100f3717f34077d3c9e0ac843657182c751e4ba3fa4 | VERIFIED |
| regression | acceptance/release/runs/A4-formal-20260901-current/evidence/review-lanes/regression-review.md | 9b05d090d8e093e56cc89c00d0679cd6d4c2f0a5fe6c73c7d22760f49c8089ac | PASS |

The identity report's pre-synthesis finding is retained as audit history; the
serial closure above is the release decision boundary. AI reviewers provide
implementation-quality evidence only and do not create a mathematical result.

## Machine verification

- `make ci-full PYTHON=.venv/bin/python`: exit 0.
- Gate 0 preflight: PASS; mypy strict: PASS; unittest: 513 passed, 2 skipped; SMT: 20 executed, 0 skipped.
- Browser gate: 52 cases x 2 campaigns x 6 widths; mobile, keyboard, SSE and M2 review workflow all passed.
- `git diff --check`: PASS.
- Remote readback: `git ls-remote origin refs/heads/main` equals `b70bac26f01046cba5d219395e48b8c5a8515815`.

The implementation candidate and delivery readback are intentionally distinct:
the accepted behavior was reviewed against `3353d6a`, while `b70bac2` carries
that accepted change and its acceptance records on the authoritative remote.

## Explicit exclusions

This acceptance is not a mathematical proof, independent proof review, live
external-literature confirmation, production/device evidence, statistical
performance claim, or public-release authorization. The fixed sources are
observations and audit fixtures only.

## Decision

- State: `ACCEPTED`.
- Proven scope: A4 one-shot topic observation plus the three checked-in source-pinned dogfood archives, replay/recovery/deduplication/budget/manual-queue integrity, read-only console projections, and fail-closed boundaries.
- Conditions: none within this bounded scope; downstream R1, Q1 and A5 remain independently bound and retain their own exclusions.
- Residual risk: environment-dependent skipped modules and all excluded external/research claims remain unresolved by design.
