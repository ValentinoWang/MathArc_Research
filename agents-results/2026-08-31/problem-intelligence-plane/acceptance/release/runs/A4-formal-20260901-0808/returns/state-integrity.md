# A4 state-integrity independent acceptance review

- Review lane: `state-integrity`
- Scope: SSOT node `A4` only
- Review mode: zero-write review of frozen repository bytes; temporary probe roots were outside the repository
- Source commit: `5af1d9ff6fde02d86633cca50cf815ef04661d4a`
- Source tree: `fb14013eb548b220ec319d60e9c3814c9158a029`
- Review boundary: offline fixed-source review only. This is not mathematical proof, external literature confirmation, production/device evidence, public-release authorization, or a remote-delivery review.

## Findings

### P0

None.

### P1

None.

The first independent restart probe used an overstrict reviewer assertion that the entire archive file remain byte-identical. It exited `1` because replay intentionally persists only `replayed: false -> true`. Inspection confirmed that `archive_digest_sha256` excludes `replayed`; the archive body and digest remained stable and both topic-state files remained byte-identical. The corrected probe exited `0`. This was a probe defect, not an implementation finding.

## Source identity

Command:

```bash
git rev-parse HEAD^{commit} HEAD^{tree}
```

Result: exit `0`; commit `5af1d9ff6fde02d86633cca50cf815ef04661d4a`; tree `fb14013eb548b220ec319d60e9c3814c9158a029`.

Selected SHA-256 identities:

| Artifact | SHA-256 | Disposition |
| --- | --- | --- |
| `matharc/v02/topic_observation.py` | `ee7b31685b58ed0130df17006244ca7c43b8afc416d84c02da863ff8686dfa20` | matches frozen `HEAD` |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` | matches frozen `HEAD` |
| `.ssot/nodes/A4.json` | `8e667181bafda099594037805028725d8b6c71e567e1a3ec113863dc4612ad30` | inspected |
| `.ssot/execution-contracts/A4.json` | `f1258adac692989c52f91579972cf11bb4589066467b5812bd2f2fc5ac0fba5e` | matches `A4.execution_contract_sha256` |
| `.ssot/edges/E-T2-A4.json` | `331d94dcdd5ede19482ce5d4b098d0ea9e1b32b9936a5a51f1b63c7e8acc23eb` | inspected |
| `evidence/T2.json` | `42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3` | inspected; `EV-T2-ACCEPTED-1` |
| `evidence/t2-fixtures/three-real-archives.json` | `475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c` | inspected and executed |

The three S1 fixture hashes are `2eac896e...5053a`, `d76d9f4a...5c592`, and `935ec7a4...dd2acd`; all match the T2 contract. The four pinned source hashes are `540973d1...647bd`, `f0090168...4cb`, `ba778973...6885`, and `8ef2177a...3476`; all match the T2 contract. `git diff --exit-code HEAD -- <A4 reviewed paths>` exited `0`.

## Protected-test integrity

| Protected test | Working SHA-256 | `git show HEAD:<path>` SHA-256 | Result |
| --- | --- | --- | --- |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` | same | PASS |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | same | PASS |

Both protected tests exist, are tracked, match the frozen source commit, and ran without skips. No deletion, broad skip, weakened assertion, fixture-specific production branch, or uncommitted change was observed. The A4/T2 node and evidence records do not declare a separate pre-`HEAD` protected-test hash baseline; this lane therefore binds integrity to the user-pinned `HEAD` bytes.

## Commands and results

Focused protected suite:

```bash
env PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/matharc-a4-pycache TMPDIR=/tmp python3 -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives
```

Result: exit `0`; `Ran 41 tests in 13.642s`; `OK`; zero skips.

Identity and worktree check:

```bash
shasum -a 256 matharc/v02/topic_observation.py matharc/v02/dogfood_archives.py tests/test_v02_topic_observation.py tests/test_v02_dogfood_archives.py agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A4.json agents-results/2026-08-31/problem-intelligence-plane/.ssot/execution-contracts/A4.json agents-results/2026-08-31/problem-intelligence-plane/.ssot/edges/E-T2-A4.json agents-results/2026-08-31/problem-intelligence-plane/evidence/T2.json agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures/three-real-archives.json
git show HEAD:tests/test_v02_topic_observation.py | shasum -a 256
git show HEAD:tests/test_v02_dogfood_archives.py | shasum -a 256
git diff --exit-code HEAD -- matharc/v02/topic_observation.py matharc/v02/dogfood_archives.py tests/test_v02_topic_observation.py tests/test_v02_dogfood_archives.py agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A4.json agents-results/2026-08-31/problem-intelligence-plane/.ssot/execution-contracts/A4.json agents-results/2026-08-31/problem-intelligence-plane/.ssot/edges/E-T2-A4.json agents-results/2026-08-31/problem-intelligence-plane/evidence/T2.json agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures
```

Result: all commands exited `0`; working hashes matched frozen `HEAD`.

Independent probes were executed with:

```bash
env PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/matharc-a4-probe-pycache TMPDIR=/tmp python3 - <<'PY'
# Six isolated TemporaryDirectory probes using the public A4 runners:
# restart_replay, cursor_conflict, coordinated_tampering,
# manual_queue_linkage, budget_binding, legacy_recovery.
PY
```

The probe mutations recomputed attacker-controlled result/manual/archive digests where applicable; fixed contract bytes and fresh canonical execution remained outside the mutated state.

| Probe | Exact observed result |
| --- | --- |
| Coordinated manual/state/archive tampering | PASS; `DogfoodArchiveError: persisted topic observation state does not match canonical dogfood state` |
| Restart replay | PASS after correcting the reviewer assertion; `replayed=false->true`; archive body/digest stable; both topic-state files byte-stable |
| Cursor conflict | PASS; `CURSOR_BLOCKED`; `next_cursor` remained `dogfood-c4`; one linked `CURSOR_CONFLICT` manual event |
| Manual queue linkage | PASS; `DogfoodArchiveError: topic observation manual queue does not match persisted archive: stored manual review result does not match exactly one manual queue entry` |
| Budget binding with recomputed budget and archive digests | PASS; `DogfoodArchiveError: persisted budget snapshot identity mismatch` |
| Legacy state `1.3` recovery | PASS; `TopicObservationError` named `topic-observation-state-recovery-v2`; legacy bytes preserved |
| Legacy archive `1.1` recovery | PASS; `DogfoodArchiveError` named `dogfood-archive-recovery-v1`; legacy bytes preserved |

The initial combined probe exited `1` solely on the overstrict whole-archive byte assertion; its other five negative probes passed. The corrected restart-only command exited `0` with `PASS restart replay: replayed=false->true; archive body/digest stable; both topic-state files byte-stable`.

## A4 criterion disposition

| A4 criterion | Evidence reviewed | Disposition |
| --- | --- | --- |
| Three source-pinned archives and non-promotion boundary | Contract path binding, three S1 fixture hashes, four source hashes, exact case order/status, focused suite | PASS |
| Restart replay, deduplication, budget, and manual queue closure | Protected tests plus independent restart, cursor, manual, and budget probes | PASS |
| Legacy state/archive recovery fails closed without rewrite | Protected tests plus byte-preservation probes for state `1.3` and archive `1.1` | PASS |
| Coordinated input/disposition/manual/archive tampering fails closed | Protected tests plus recomputed-identity coordinated tamper probe | PASS |
| Cursor conflict and manual queue linkage remain topic/cursor/input-bound | State re-derivation, manual-event validation, focused tests, independent probes | PASS |
| Full persisted archive/state equals canonical replay | `DogfoodArchiveRunner._canonical_expected_execution` and `_assert_canonical_execution`, exercised on replay and tamper | PASS |
| No claim/trace/promotion authority | Exact T2 `non_claim_boundary`; all three `expected_promotion_allowed=false`; focused execution creates no claim or trace artifact | PASS within offline fixed-source scope |

SSOT binding is coherent for this lane: A4 is a `VERIFIED` acceptance gate with separate `验收负责人` authority; its contract hash matches the node; hard edge `E-T2-A4` requires T2 `ACCEPTED` and transfers `DL-T2`; T2 is `ACCEPTED` and its fixture/source identities passed current readback.

## Residual risk and authority boundary

- The archive intentionally persists the non-semantic `replayed` marker on restart; consumers comparing raw archive bytes must exclude that marker as the implementation digest does.
- This review used checked-in snapshots only. It does not confirm current external literature, source availability, licenses outside the recorded provenance, or mathematical truth.
- It does not establish production/device behavior, remote GitHub readback, monitoring/rollback readiness, or public-release authorization.
- No human acceptance decision was made. The designated A4 acceptance owner must independently synthesize all required lanes and is the only authority that can accept A4.

## Repository status

- Business project: frozen `HEAD` remained `5af1d9ff6fde02d86633cca50cf815ef04661d4a`; the reviewed tracked paths had no diff. The pre-existing untracked `A4-formal-20260901-0808/` run directory remains, with this return as this lane's sole write.
- Harness SSOT: `/Users/vsiyo/Desktop/Opensource_Tool/Harness_Engineering` at `86d7c2cc7bdb0ed6f6628c8ad40250119ccb84a2`; clean; no Harness SSOT change.

## Lane disposition

`proposed_state: VERIFIED`

This lane cannot accept A4. It reports no P0/P1 finding for the reviewed state-integrity criteria and proposes `VERIFIED` only for this bounded lane at the pinned source identity.
