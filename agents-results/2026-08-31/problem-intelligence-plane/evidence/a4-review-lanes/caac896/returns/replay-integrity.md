# Acceptance Release Review: A4-caac896-replay-integrity

## Findings

### P0

None observed.

### P1

1. **Persisted cross-batch coordinated replacement bypasses replay integrity.**
   `matharc/v02/topic_observation.py:1212-1278` records the first `input_id` and
   rejects a repeated successful observation key, but accepts a later
   `SEEN_OBSERVATION_KEY` disposition whenever that key was seen earlier in the
   cursor-ordered replay. It does not bind that later duplicate disposition to
   the historical disposition of the same input/observation before accepting a
   rewritten state.

   Fresh bounded probe: create valid `c0/A` and `c1/B`; rewrite `c0/A` with B's
   complete input projection, fingerprint, observation identity, evidence,
   processed-input entry, batch digest, projection digest, binding digest, and
   result digest; then rewrite `c1/B` from `NEW_IMPORT/IMPORTED` to
   `SEEN_OBSERVATION_KEY/DUPLICATE` and recompute its result digest. A fresh
   runner loaded the state and returned `next_cursor=c2` instead of failing
   closed:

   `ACCEPTED: next_cursor=c2; coordinated rewrite bypassed validation`

   This is the exact attack shape required to coordinate both batches, so no
   successful observation key is repeated in the validator's final set. The
   existing negative test at `tests/test_v02_topic_observation.py:530-577`
   only leaves the second batch as a successful import and therefore passes
   without covering this reclassification. This blocks AC-02.

2. **The target commit is outside the locked A4 acceptance identity.**
   The approved contract at
   `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A4-topic-observation-dogfood/acceptance-contract.md:15,33-38`
   locks `main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80` and
   `tests/test_v02_topic_observation.py` at
   `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56`.
   The requested target is `caac896db393550817da9e57c56f03f46277cb54` and its
   protected test bytes hash to
   `9c38ac4bad23ed85f753e331164f9ed6c8cebdfd59bec28908691ad989d92666`.
   `evidence/A4.json:8-11,45` likewise records the older `3353d6a` source
   identity and `ACCEPTED` state. The contract hash itself matches its A4
   declaration, but the contract/evidence tuple is not bound to `caac896`.
   This is a blocking protected-test/acceptance identity failure and blocks
   AC-05.

### P2

None observed.

## Scope and identity

- Task ID: `A4-caac896-replay-integrity`
- Target commit: `caac896db393550817da9e57c56f03f46277cb54`
- Parent: `3830310398590b1e20ee67854256a64d7afc85c1`
- Target subject: `fix: close persisted topic replay integrity gaps`
- `HEAD` and `origin/main`: both `caac896db393550817da9e57c56f03f46277cb54`
- Target scope exactness: `git diff --exit-code caac896... -- matharc/v02/topic_observation.py tests/test_v02_topic_observation.py` exited `0`.
- Commit changed only the two requested tracked paths; the lane did not edit
  source, tests, contracts, SSOT, human acceptance, or existing evidence.
- Review runtime: Darwin arm64, Python 3.13.7, `.venv/bin/python`,
  `PYTHONDONTWRITEBYTECODE=1`.
- Acceptance fragment: A4-topic-observation-dogfood, contract version `2`,
  decision ref `decision.problem-intelligence.amendment@2`, invalidation key
  `acceptance.problem-intelligence.dogfood`.
- This lane is independent evidence only and cannot accept A4.

## Protected-test integrity

| Path | Approved hash in A4 contract | Observed hash at target/current worktree | Result |
| --- | --- | --- | --- |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` | `9c38ac4bad23ed85f753e331164f9ed6c8cebdfd59bec28908691ad989d92666` | FAIL: target changed the locked protected test |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | PASS |

Additional target hashes: `matharc/v02/topic_observation.py` is
`d86e18b37472673afc726a074140260ce61a7d7f54df88bf2001166ac411bbd2` and
`evidence/A4.json` is
`0e22f563f17c00506ba7d482e8addb37b5e72ce52194c5e4d876ad8abbfc153b`.

## Requirements-test traceability

| Requirement | Observed evidence | Result | Blocking |
| --- | --- | --- | --- |
| AC-01 | T2 fixed fixture digest probe; `tests.test_v02_dogfood_archives` | PASS for fixed T2 bytes and archive behavior | No, within this lane |
| AC-02 | 29 topic tests, 13 dogfood tests, plus fresh coordinated rewrite probe | FAIL: P1 bypass | Yes |
| AC-03 | A4 contract SHA equals `evidence/A4.json` declared contract SHA; fixed negative tests passed | PASS for internal contract hash, but not target acceptance | Yes for release identity |
| AC-04 | Not rerun; full browser/release gate is outside this focused lane | MISSING in this lane | Yes for full A4 |
| AC-05 | A4 source identity is `3353d6a`; target is `caac896`; protected test hash drift | FAIL | Yes |
| H-01 | Historical human run `20260901T141500Z-local-a4f002` is bound to `3353d6a` | Not current evidence for `caac896` | Yes |

## Exact commands and results

1. `git status --short --branch; git rev-parse HEAD; git rev-parse origin/main`
   returned `## main...origin/main`, target `caac896...` for both refs, and
   only the pre-existing untracked lane directory.
2. `git diff --exit-code caac896db393550817da9e57c56f03f46277cb54 -- matharc/v02/topic_observation.py tests/test_v02_topic_observation.py`
   exited `0`; `git diff --check ...` exited `0`.
3. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_topic_observation`
   exited `0`: `Ran 29 tests`, `OK`.
4. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_dogfood_archives`
   exited `0`: `Ran 13 tests`, `OK`.
5. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_frozen_review_inputs`
   exited `0`: `Ran 7 tests`, `OK`.
6. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_v02*.py'`
   exited `0`: `Ran 318 tests`, `OK`.
7. Fresh positive replay/duplicate/determinism probe exited `0` with:

   ```text
   same_input_status= DUPLICATE
   same_input_basis= PROCESSED_INPUT_REPLAY
   same_input_prior_cursor= c0
   same_input_literature_count= 1
   duplicate_key_status= DUPLICATE
   duplicate_key_basis= SEEN_OBSERVATION_KEY
   duplicate_key_literature_count= 1
   deterministic_statuses= REPLAYED REPLAYED
   deterministic_replayed_flags= True True
   deterministic_result_equal= True
   deterministic_state_unchanged= True
   ```
8. Fresh coordinated-rewrite probe described in P1-1 exited `0` but printed
   `ACCEPTED: next_cursor=c2; coordinated rewrite bypassed validation`; this
   is a failed negative-control result, not a pass.
9. Fixed evidence probe exited `0`: A4 contract actual SHA matched its declared
   SHA; all three T2 S1 fixture hashes matched their fixed values; T2 and A4
   embedded states were `ACCEPTED`/`pass`, but A4 embedded source identity was
   the older `3353d6a`.

## Engineering review and residual risk

Atomic state replacement and cursor-chain traversal are present, and normal
replay, duplicate-key suppression, deterministic replay, and malformed-state
fail-closed tests pass. The integrity model remains structural: an actor able
to rewrite the JSON state and recompute its unkeyed SHA-256 fields can also
rewrite a later successful import into a seen-key duplicate. Repair requires an
immutable or authenticated per-cursor input/disposition ledger (or equivalent
source-batch commitment) and a negative test for the exact reclassification
attack before AC-02 can be reconsidered. Historical T2/A4 and human/release
records do not prove the target commit's acceptance.

No external sandbox, production/device, mathematical-proof, live-literature,
or public-release evidence was claimed; those are explicit A4 non-goals.

## Decision

- `proposed_state: FAILED`
- `acceptance_self_check: fail`
- `failure_class: persisted_cross_batch_replay_identity_gap; protected_test_baseline_drift`
- `failure_origin: matharc/v02/topic_observation.py:1212-1278; A4 contract/evidence remains bound to main@3353d6a`
- `residual_risk: a coordinated state writer can relocate an observed input across cursors and evade the current replay validator by reclassifying the later successful import as SEEN_OBSERVATION_KEY`
- This lane cannot accept A4. Rebind/invalidate the A4 acceptance tuple and repair the replay disposition invariant before any A4 acceptance decision.

Verdict: FAIL
