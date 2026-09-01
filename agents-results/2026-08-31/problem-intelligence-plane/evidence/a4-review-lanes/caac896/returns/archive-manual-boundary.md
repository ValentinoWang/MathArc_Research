# A4 caac896 Archive / Manual Boundary Review

- Task ID: `A4-caac896-archive-manual-boundary`
- Lane: `archive-manual-boundary`
- Review mode: independent zero-write review; this return is the sole permitted direct write
- Pinned commit: `caac896db393550817da9e57c56f03f46277cb54`
- Scope: topic-observation persisted state, dogfood archive/manual-result linkage, protected tests, and the offline fixed-source non-proof/non-public boundary
- Acceptance authority: none. This lane cannot accept A4, alter its SSOT state, or unlock downstream work.

## Findings

### P0

None.

### P1

None.

The reviewed implementation rejects all four requested adversarial states. No deleted test, skip, assertion weakening, fixture-specific production branch, network fallback, or boundary expansion was found in the target diff.

### P2

1. **The approved protected-test hash has not been re-pinned to the target commit.** The A4 v2 acceptance contract is approved and `LOCKED`, but it remains bound to `main@3353d6a` and lists `tests/test_v02_topic_observation.py` as `1b505da5...`; the target commit's file is `9c38ac4b...`. The diff is additive: 51 lines add one adversarial regression for a fully recomputed cross-batch rewrite, with zero deletions. The archive test still matches its approved hash. This is non-blocking for this narrowly pinned code-review lane because inspection found strengthening rather than weakening, but a serial A4 acceptance owner must re-pin and reconcile the protected-test identity before using this return in any new formal A4 acceptance synthesis.

   - `failure_class: PROTECTED_TEST_BASELINE_IDENTITY_DRIFT`
   - `failure_origin: acceptance contract remains pinned to 3353d6a while caac896 additively strengthens tests/test_v02_topic_observation.py`

## Adversarial Verification

| Required property | Probe | Observed result | Disposition |
| --- | --- | --- | --- |
| `CURSOR_CONFLICT` cannot attach to a normal batch | Converted a valid high-risk batch manual item to `CURSOR_CONFLICT`, recomputed its semantic `manual_id`, updated result/evidence linkage, and recomputed `result_digest_sha256` | `ManualQueueObservationError: cursor conflict manual disposition cannot be attached to a batch item` | PASS |
| Successful imports cannot reuse an observation key | Rewrote the first of two successful batches to the second observation, updating projections, fingerprints, observation IDs, binding digest, batch digest, result digest, processed map, and seen-key set | `TopicObservationError: successful import repeats a prior seen observation key` | PASS |
| Archive/manual result binding remains fail closed | Changed archived `dogfood-c2` manual result to `IMPORTED`, removed `manual_id`, changed batch status to `APPLIED`, and recomputed the result digest | `DogfoodArchiveError` chained from persisted disposition mismatch | PASS |
| Offline fixed-source non-proof/non-public boundary remains closed | Fresh offline dogfood run plus a copied contract whose exact `non_claim_boundary` was rewritten to authorize public claims | Clean run had all promotion/claim/trace flags false and no claim/trace files; forged contract failed with `T2 non-claim boundary identity drift` | PASS |

The cursor attachment is rejected directly at `matharc/v02/topic_observation.py:1488`. Cursor-ordered replay rejects repeated successful keys at `matharc/v02/topic_observation.py:1267`. Dogfood replay revalidates topic state before accepting the archive, while the exact non-claim string, fixed fixture directory, per-case non-promotion flags, source hashes, and forbidden claim/trace artifacts remain enforced in `matharc/v02/dogfood_archives.py`.

## Protected-Test Integrity

| Path | Approved contract SHA-256 | Observed SHA-256 at `caac896` | Result |
| --- | --- | --- | --- |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` | `9c38ac4bad23ed85f753e331164f9ed6c8cebdfd59bec28908691ad989d92666` | Additive strengthening; P2 re-pin required before formal reuse |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | Exact match |

`git diff 3353d6a..caac896 -- <protected tests>` reports `51` additions and `0` deletions, all in the topic-observation test. The focused run discovered 42 tests and completed with 42 passes, zero failures, zero errors, and zero skips.

## Commands And Results

1. `git show --stat --oneline caac896` and `git diff caac896^ caac896 -- matharc/v02/topic_observation.py tests/test_v02_topic_observation.py`
   - Exit `0`; target changes only those two files, `166` insertions, no deletions.
2. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives`
   - Exit `0`; `Ran 42 tests in 1.345s`; `OK`; no skips.
3. Four inline Python probes using separate `TemporaryDirectory` roots
   - Exit `0`; all four requested attacks were rejected with the exact results recorded above. No probe state was written inside the repository.
4. `git diff --check caac896^ caac896` and AST parsing of the two implementation and two protected-test files under Python `3.13.7`
   - Exit `0`; no whitespace error; all four files parsed.
5. `git rev-parse HEAD origin/main caac896` and `git merge-base --is-ancestor caac896 origin/main`
   - Exit `0`; `HEAD == origin/main == caac896`; target is on the current remote-tracking main ref.
6. `git diff --exit-code HEAD -- <reviewed source, tests, A4 SSOT, contract paths>`
   - Exit `0`; no tracked review-scope changes before writing this return.

## Hashes

| Identity | Value |
| --- | --- |
| Commit | `caac896db393550817da9e57c56f03f46277cb54` |
| Parent | `3830310398590b1e20ee67854256a64d7afc85c1` |
| Tree | `6ac2c94b7ac7c748664035850877bea76ed41e38` |
| `matharc/v02/topic_observation.py` | `d86e18b37472673afc726a074140260ce61a7d7f54df88bf2001166ac411bbd2` |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` |
| A4 acceptance contract v2 | `4b7ac7ea035d59be7c87fef9867b97529f8b00f68c207d7460963cd625095c84` |
| A4 node | `8dfe33ef6a3f2cc8666e2d948694ce89344f437710dd51eeda63071e6cd4e1d8` |
| A4 execution contract | `f1258adac692989c52f91579972cf11bb4589066467b5812bd2f2fc5ac0fba5e` |
| T2-to-A4 edge | `331d94dcdd5ede19482ce5d4b098d0ea9e1b32b9936a5a51f1b63c7e8acc23eb` |
| T2 evidence | `42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3` |
| Three-archive fixture contract | `475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c` |

## Residual Risk

- All integrity digests are local. A fully compromised host able to replace code, fixed sources, state, artifacts, and every local digest is outside this review.
- This review used checked-in fixed bytes only. It does not prove live source freshness, literature completeness, mathematical correctness, production/device behavior, deployment, or public-release authorization.
- The clean-run absence check covers the declared claim/trace artifact names and exact schema flags; it is not a semantic classifier for arbitrary future filenames or outputs.
- The approved protected-test identity still names the pre-`caac896` topic test. Formal acceptance synthesis must resolve that identity explicitly; this lane cannot do so.
- Harness SSOT was read through the linked authority at `/Users/vsiyo/Desktop/Opensource_Tool/Harness_Engineering`; it was not changed. Its repository was already `main...origin/main [ahead 3]` with unrelated untracked paths.

## Disposition

- `proposed_state: VERIFIED`
- `acceptance_self_check: pass`
- `failure_class: PROTECTED_TEST_BASELINE_IDENTITY_DRIFT` (P2, non-blocking for this lane)
- `failure_origin: approved A4 contract metadata predates the additive protected-test change in caac896`
- Business project status before this return: `main...origin/main`, no tracked diff, pre-existing untracked `agents-results/.../caac896/` review directory.
- Harness SSOT git status: `main...origin/main [ahead 3]` with pre-existing unrelated untracked skill links and `agents-results/2026-09-02/harness-delivery-console-v2/execution-orchestration/`.
- This lane cannot accept A4.

Verdict: PASS
