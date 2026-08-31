# Acceptance Run: 20260831T164137Z-local-a51e32

- Run ID: 20260831T164137Z-local-a51e32
- Task ID: Q1-calibration-disclosure
- Lane: machine/unit
- Status: PARTIAL
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- Contract version: 1
- Contract SHA-256: 77e6ae2b08e1b27aeb4852c56f0f3dd21fa85108fff1e65c7065658f72287c7a
- Source identity: c0dcc523ba00de9f660a8e1f1badd887f21de1f7+q1-pre-r1-metadata-migration
- Runtime identity: python-3.13
- Executor or reviewer: codex
- Started at: 2026-08-31T16:41:37.404932Z
- Completed at: 2026-08-31T16:43:04Z
- Evidence directory: evidence/

## Scope

AC-01 through AC-04 for the fixed, local Q1 policy. The run covers source identity, policy schema, uncalibrated dual-track semantics, fail-closed deserialization and the passive non-public boundary. It excludes all mathematical, external, statistical, production and public-release claims.

## Procedure

Executed the focused Q1/R1 unit suite, the complete v0.2 suite, the complete repository suite, and Python compilation under Python 3.13. Exact commands and outcomes are recorded in `evidence/verification-summary.md`.

## Requirement disposition

| Requirement | Result | Evidence | Notes |
| --- | --- | --- | --- |
| AC-01 | PASS | evidence/verification-summary.md | R1 evidence and fixture byte/content identity plus three-case order are checked directly. |
| AC-02 | PASS | evidence/verification-summary.md | `UNCALIBRATED`, priority and `NOT_READY` are checked independently. |
| AC-03 | PASS | evidence/verification-summary.md | Identity, status, priority, disclosure, public flag, cardinality, field and digest tampering are rejected. |
| AC-04 | PASS | evidence/verification-summary.md | Static dependency guard and immutable `public_release_allowed: false` both pass. |

## Findings

None.

## Evidence manifest

| Artifact | SHA-256 | Meaning |
| --- | --- | --- |
| evidence/verification-summary.md | a87a6b571a7b8668eba10d496ae88b73e3eea03cc6a13036a2467c76e3c4b72d | Executed commands, outcomes and bounded AC coverage. |

## Unverified items

Mathematical proof, reported-open status, novelty, external literature retrieval, calibration quality, statistical performance, generalization, production/device behavior and public release approval.

## Conclusion

PARTIAL: this run passed before the accepted R1 evidence was structurally migrated to a valid immutable human-run ID. That migration changed the R1 evidence byte digest, so this run is retained as history and is not selected for Q1 acceptance.
