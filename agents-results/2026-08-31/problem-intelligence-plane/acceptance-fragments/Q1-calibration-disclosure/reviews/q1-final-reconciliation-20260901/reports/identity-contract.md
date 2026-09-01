# Q1 Final Identity-Contract Reconciliation

- Reviewer identity: `q1-final-identity-contract-reviewer-20260901`
- Review mode: independent, zero-write except for this report
- Candidate reviewed: `agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json`
- Candidate SHA-256: `600153703b7e990e4db246d5a65fd06b2d1920d9f6a82cae1e470bb67a3d94be`
- Verdict: **FAIL**

## Files and hashes read

| Artifact | SHA-256 | Result |
| --- | --- | --- |
| `evidence/Q1.json` | `600153703b7e990e4db246d5a65fd06b2d1920d9f6a82cae1e470bb67a3d94be` | current candidate read |
| `evidence/q1-fixtures/uncalibrated-disclosure-policy.json` | `f519e824ef92274ae2f9f3749ef84dc71beece3fb1c4523c98a765db98cf17bf` | matches candidate pin |
| `evidence/R1.json` | `672a4c439c3b7de7bfebe2e09576daa0fcefd731d874c3a48d3671d7ba625c71` | matches candidate and policy pin |
| `evidence/r1-fixtures/four-route-regression.json` | `04839d8177b10b4b7749ee953b6bae0771db3ede63a79708ed9da64e6ce1b75c` | matches candidate and policy pin |
| `acceptance-contract.md` | `e2db06e4a9d863bc1963e19d5aac1c17bc070adb84df45d95c41ac1df39efc73` | matches binding and both latest result snapshots |
| `acceptance/human/Q1-calibration-disclosure/binding.md` | `484582683dea54f92acb18ec37c00fc17f41d0e5f96a9ce6458858a8e6ad2378` | matches latest human result |
| `acceptance/human/Q1-calibration-disclosure/checklist.md` | `0a25e57af95eafe3093db314eb720303bda3d6d5d6737ca62d8e44fbcbf77e81` | matches latest human result |
| `acceptance/machine/unit/runs/20260901T093000Z-local-a1c004/result.md` | `447bd501861e87ed92e80318f9d8fdeadd515233d4e2be32270c5d7804a0ec56` | PASS, but candidate hash is explicitly pending |
| `acceptance/human/Q1-calibration-disclosure/runs/20260901T093100Z-local-a1c104/result.md` | `5b0cc5ac1d851288cc35e4f07c7f9c29880a735204151e4ab832357a651b054c` | PASS for H-01 |
| `acceptance/human-acceptance-log.json` | `7dc186460bee11f2e963e0a8ef86484b50eea4d9ba79c42630a40859821c90d6` | still marks Q1 `INVALIDATED` |
| previous independent frozen-input manifest | `359984a62589023373cff985a5e1b1ad78cc25335e5ea0ec28a78e913f0dca8b` | freezes a different Q1 candidate |

## Checks that pass

- The policy digest `f11f61ab1b780ff61ed9b1211063d30d6b3632b92e05b95735b9bde9f55ca3e7`, R1 evidence identity, R1 fixture identity, implementation hash `bd5ead52e02730203ae0e1a45405c9eeaedc74b22d9fa616f417fdc6f3cb5e83`, and protected-test hash `7a38001d211c2b8ef5b6b45e8f8fa87f7b0ce9785559cc475eb511d250af5026` match the current candidate.
- The policy remains three fixed records, all `UNCALIBRATED` and `NOT_READY`, with `public_release_allowed=false`.
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation` passed: 14 tests.
- Bytecode-free compilation and `git diff --check` passed.

## Blocking findings

1. **The declared independent reviews do not review the current candidate.** Their frozen manifest pins `Q1.json` to `6e27b1665ef04f8bd4481fbd5e20388114799c9bad8b735224b5b19fd13cd197`, while the current candidate is `600153703b7e990e4db246d5a65fd06b2d1920d9f6a82cae1e470bb67a3d94be`. The reports themselves and their declared hashes are intact, but they attest only to the former byte sequence.
2. **The latest machine result does not bind the current candidate.** Its evidence manifest says `evidence/Q1.json | pending final evidence hash`; it therefore establishes the unit boundary, not final-candidate identity. The earlier v4 machine result likewise records only execution evidence, not a Q1 candidate hash.
3. **The authoritative generated human ledger is stale and contradictory.** `acceptance/human-acceptance-log.json` was generated at `2026-09-01T08:22:00Z` and records Q1 as `INVALIDATED`, pointing to the superseded 20260831 human run. The later 20260901 H-01 result is a valid PASS snapshot, but the ledger has not been regenerated to reconcile it.

## Safe non-self-referential final reconciliation

Do not add this report, a new reviewer report, or their hashes back into `Q1.json`: that mutation would change the candidate after its review and recreate the same defect. Instead, keep `Q1.json` immutable and create a separate final-reconciliation manifest outside the candidate that pins, at minimum, the current Q1 candidate hash, policy/R1/implementation/test hashes, contract/binding/checklist hashes, current machine-result hash, current human-result hash, and a freshly regenerated acceptance-ledger hash.

Freeze that manifest before dispatching distinct review lanes. Each final review should bind the manifest hash and record its own report outside `Q1.json`. A separate promotion decision may then reference the immutable manifest and review hashes without changing the reviewed candidate. Until that sequence and the regenerated ledger agree, Q1 must remain `INVALIDATED` or `PENDING`, not final `ACCEPTED`.

## Scope boundary

This FAIL concerns evidence identity and acceptance reconciliation only. It does not dispute the local policy checks and does not make a mathematical, literature, calibration-performance, production, or public-release conclusion.
