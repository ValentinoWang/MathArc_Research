# A4 1b05e61 Post-Fix State-Integrity Review

- Task ID: `A4-1b05e61-post-fix-review`
- Lane: `state-integrity`
- Authority: independent zero-write review; this return is the sole authorized write
- Frozen candidate: `HEAD == origin/main == 1b05e6105b0d7c98a5b6e037ebd66b916c3a921e` (local refs)
- Parent: `caac896db393550817da9e57c56f03f46277cb54`
- Tree: `8c35023d729d40b7828e1c82bcfdc35b64dad922`
- Diff SHA-256 (`git diff caac896..1b05e61`): `7ef4fe9a95b8f88f9d6ffdc557afd6f04e2c232d3a6eaa560e96074dd75456be`
- Boundary: offline, fixed repository sources, non-mathematical-proof, non-public-release
- Acceptance authority: none. This lane cannot accept A4 or make the old contract/human run current.

## Findings

### P0

None observed.

### P1

1. **The exact-set invariant can be satisfied by laundering a displaced literature ID through unrelated manual evidence.**

   `matharc/v02/topic_observation.py:1114-1116` adds every non-null `persisted_observation_id` to one undifferentiated set, and `:1286-1289` compares that set with all persisted literature IDs. The general checks at `:1382-1408` prove that the named literature record exists and is internally coherent, but the `HIGH_RISK_EVENT` branch at `:1502-1510` does not require that record's observation ID or idempotency key to match the manual item's input projection. Set membership therefore does not prove the record's causal batch/disposition history.

   A fresh `TemporaryDirectory` negative probe left literature records `OBS-A` and `OBS-B` unchanged, rewrote `c0/A` into `NEW_IMPORT:OBS-B`, rewrote `c1/B` into a high-risk `MANUAL_QUEUE` item, attached `OBS-A` as that manual item's persisted record, and recomputed the batch, projection-binding, projection, result, processed-input, seen-key, and manual IDs/digests. The loader accepted the state:

   ```text
   PROBE=manual-reference-laundering
   load_status=ACCEPTED:next_cursor=c2
   c0_meaning=NEW_IMPORT:OBS-B
   c1_meaning=MANUAL_QUEUE:OBS-A
   literature_ids=['OBS-A', 'OBS-B']
   ```

   This is a state-only bypass: it does not require deleting or rewriting either literature record. The equality is true while the original `c0/A` import meaning is hidden and the original `c1/B` successful import is changed to manual review. AC-02 remains blocked.

   The same root cause also permits direct history relabeling. A second probe changed a valid `NEW_IMPORT/IMPORTED` record to `EXISTING_OBSERVED/IDEMPOTENT`, recomputed `result_digest_sha256`, and was accepted at `next_cursor=c1`. The persisted-ID set is identical, so the new invariant cannot distinguish "created by this batch" from "already existed before this batch."

2. **The global equality rejects a legitimate incremental `EXISTING_OBSERVED` transition and prevents recovery by processing the remaining record.**

   A fresh probe pre-imported valid observations A and B through the runner's public `LiteratureBase`, then processed A at `c0`. A correctly returned `IDEMPOTENT`, but the next run for B failed during state load because B existed in literature and had not yet appeared in stored batch evidence:

   ```text
   PROBE=preexisting-partial-reconciliation
   preimport_A=IMPORTED
   preimport_B=IMPORTED
   first_status=IDEMPOTENT
   second_status=REJECTED:persisted literature observations do not match stored batch evidence
   ```

   The runner cannot ingest B to repair the equality because `_load_state()` rejects before `_process_input()` runs. An isolated one-record `EXISTING_OBSERVED` state passes, so the protected positive fixture misses this partial-reconciliation/restart state. This is a compatibility regression in the supported existing-observation path and also blocks AC-02.

### P2

1. **The additive protected test is real but too narrow for the invariant it is used to justify.**

   `tests/test_v02_topic_observation.py:579-626` constructs the exact prior two-batch attack and requires the new `literature observations` error. It proves that an unreferenced original literature record is rejected. It does not test reference laundering, a multi-record partial `EXISTING_OBSERVED` inventory, or `NEW_IMPORT`/`EXISTING_OBSERVED` history relabeling. All three gaps are material because the first two fresh probes above respectively bypass and false-trigger the production invariant.

2. **The candidate-wide diff whitespace check is not clean outside the implementation/test patch.**

   `git diff --check caac896..1b05e61` exited `2` for trailing whitespace/new EOF whitespace in the three newly added `caac896/logs/*.log` files. The scoped implementation/test command exited `0`. This is not the AC-02 cause, but it is part of the pinned eight-file commit diff and must not be reported as a candidate-wide clean `diff --check`.

## Frozen Input And Identity Verification

The frozen manifest SHA-256 is `9fb431f51ed31713114a26f18eebea1284c33035893b81f1ceb62f64017cc0e3`.

| Manifest identity | Expected | Observed | Result |
| --- | --- | --- | --- |
| `schema_version` | `1` | `1` | MATCH |
| `task_id` | `A4-1b05e61-post-fix-review` | requested task and manifest agree | MATCH |
| `direct_parent` | `A4-caac896-replay-integrity` | caac896 replay return task/lane | MATCH |
| `head` | `1b05e6105b0d7c98a5b6e037ebd66b916c3a921e` | local `HEAD` same | MATCH |
| `remote_main` | same SHA | local `origin/main` same | MATCH |
| `parent` | `caac896db393550817da9e57c56f03f46277cb54` | `HEAD^` same, object type `commit` | MATCH |
| `tree` | `8c35023d729d40b7828e1c82bcfdc35b64dad922` | `HEAD^{tree}` same, object type `tree` | MATCH |
| `decision_ref` | `decision.problem-intelligence.amendment@2` | contract lines 13-14 and A4 node lines 16-24 agree | MATCH |
| `invalidation_key` | `acceptance.problem-intelligence.dogfood` | contract and A4 node agree | MATCH |
| `contract_version` | `2` | contract line 4 and evidence contract tuple agree | MATCH |
| `contract_baseline` | `3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80` | resolves as a commit and is the contract baseline | MATCH |
| historical topic-test SHA | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` | exact SHA of `3353d6a:tests/test_v02_topic_observation.py` | MATCH |
| `formal_acceptance_current_for_frozen_source` | `false` | contract/evidence/human tuple is bound to `3353d6a`, not `1b05e61` | MATCH |

Live GitHub readback was attempted without updating refs. `git ls-remote --exit-code origin refs/heads/main` exited `128` after `Failed to connect to github.com port 443`; therefore only the pinned local `origin/main` identity is verified, not current server-side readback.

### Frozen file hashes

All eight working-tree bytes and all eight corresponding `HEAD:<path>` blobs matched the manifest.

| Path | Manifest/observed SHA-256 |
| --- | --- |
| `matharc/v02/topic_observation.py` | `f191c010e6388bc5de07f979c9ca90ab10c83a3d74db7a31827e9f3c7887dfd3` |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` |
| `tests/test_v02_topic_observation.py` | `a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb` |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` |
| `acceptance-fragments/A4-topic-observation-dogfood/acceptance-contract.md` | `4b7ac7ea035d59be7c87fef9867b97529f8b00f68c207d7460963cd625095c84` |
| `.ssot/nodes/A4.json` | `8dfe33ef6a3f2cc8666e2d948694ce89344f437710dd51eeda63071e6cd4e1d8` |
| `evidence/A4.json` | `0e22f563f17c00506ba7d482e8addb37b5e72ce52194c5e4d876ad8abbfc153b` |
| `evidence/t2-fixtures/three-real-archives.json` | `475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c` |

The two permitted caac896 returns also match their committed identities:

- `archive-manual-boundary.md`: `2bf94a3775dabdf8123fec45798720737060eb92a3c3da616d6313b022db6f43`
- `replay-integrity.md`: `0b20cb5d20f305e6c399a7b62f0302905195f52eceedcdab20e8ecd07ddb08f8`

## State Compatibility Matrix

| State/path | Evidence | Disposition |
| --- | --- | --- |
| `NEW_IMPORT` | focused suite plus positive matrix probe | PASS for ordinary creation/restart |
| `EXISTING_OBSERVED` | isolated preexisting record | PASS |
| `EXISTING_OBSERVED` with another valid preexisting record awaiting a later batch | negative probe | FAIL: loader deadlocks before later record can be processed |
| `PROCESSED_INPUT_REPLAY` | positive matrix probe | PASS |
| `SEEN_OBSERVATION_KEY` | focused suite plus positive matrix probe | PASS |
| legitimate high-risk `MANUAL_QUEUE` | focused suite plus positive matrix probe | PASS |
| forged manual reference used to cover displaced history | negative probe | FAIL: accepted instead of fail-closed |
| same-cursor replay and normal restart | focused suite | PASS |

Positive matrix stdout:

```text
PROBE=legitimate-state-matrix
statuses=['IMPORTED', 'DUPLICATE', 'DUPLICATE', 'MANUAL_REVIEW']
bases=['NEW_IMPORT', 'PROCESSED_INPUT_REPLAY', 'SEEN_OBSERVATION_KEY', 'MANUAL_QUEUE']
restart_next_cursor=c4
manual_queue_size=1
PROBE=isolated-existing-observed
status=IDEMPOTENT
basis=EXISTING_OBSERVED
restart_next_cursor=c1
```

## Protected-Test Assessment

| Path | Approved v2 SHA-256 | Parent `caac896` SHA-256 | Candidate SHA-256 | Result |
| --- | --- | --- | --- | --- |
| `tests/test_v02_topic_observation.py` | `1b505da5...` | `9c38ac4b...` | `a6ac5fdb...` | additive strengthening, but not current approved identity and incomplete for findings above |
| `tests/test_v02_dogfood_archives.py` | `e1efa41c...` | unchanged | `e1efa41c...` | exact approved hash |

- `caac896..1b05e61` adds `49` topic-test lines and deletes `0`; `3353d6a..1b05e61` adds `100` and deletes `0`.
- The production patch adds `8` lines and deletes `0`.
- AST inspection found `30` topic test methods, no `skip`/`expectedFailure` decorators, and one target assertion: `self.assertRaisesRegex`.
- The new test uses a real `TopicObservationRunner` and `TemporaryDirectory`; it does not use mocks or patches.
- The production equality is unconditional. No fixture, test-name, `union-closed`, or `OBS-*` branch exists in `topic_observation.py`.
- The assertion is strong for the exact orphan-record attack because it requires the new error text, but it is not strong enough to establish the broader historical-meaning invariant.

## AC Dispositions

| Criterion | Lane result | Basis |
| --- | --- | --- |
| AC-02 replay/recovery/dedup/budget/manual binding and fail-closed tamper behavior | **FAIL** | manual-reference laundering is accepted; incremental preexisting reconciliation is rejected |
| AC-03 fixed-source/non-claim metadata boundary | **PASS for candidate behavior only** | unchanged dogfood implementation/test hashes; all 13 dogfood tests pass, including exact boundary and fixture-directory negatives; no new network/public/proof path |

AC-03's behavioral pass is not formal acceptance for `1b05e61`. The contract and historical human run are not current for this source identity.

## Offline Fixed-Source Boundary

The changed invariant does not expand the dogfood runner's authority. `matharc/v02/dogfood_archives.py` remains byte-identical, requires the exact fixture directory and exact non-claim string, keeps all promotion/claim/trace flags false, and reconstructs canonical topic state on replay. The focused dogfood module passed all 13 tests. This proves only compatibility with the declared fixed fixture execution; it does not prove live literature freshness, mathematical truth, production/device behavior, or public-release authorization.

## Commands And Results

1. `GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD origin/main HEAD^ 'HEAD^{tree}'`
   - Exit `0`; returned, in order, `1b05e610...`, `1b05e610...`, `caac896d...`, `8c35023d...`.
2. `printf '%s\n' <head> <parent> <tree> <baseline> | GIT_OPTIONAL_LOCKS=0 git cat-file --batch-check='%(objectname) %(objecttype)'`
   - Exit `0`; types were `commit`, `commit`, `tree`, `commit`.
3. `jq -r '.files | to_entries[] | [.key, .value] | @tsv' frozen-inputs.json | while ... shasum -a 256 ...`
   - Exit `0`; `8/8 MATCH` for working files. The equivalent `git show "HEAD:$file" | shasum -a 256` loop also returned `8/8 MATCH`.
4. `GIT_OPTIONAL_LOCKS=0 git show 3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80:tests/test_v02_topic_observation.py | shasum -a 256`
   - Exit `0`; `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56`.
5. `GIT_OPTIONAL_LOCKS=0 git diff --name-status caac896db393550817da9e57c56f03f46277cb54..1b05e6105b0d7c98a5b6e037ebd66b916c3a921e`
   - Exit `0`; six added caac896 review artifacts plus modifications to `topic_observation.py` and its protected test; `8 files changed, 36909 insertions(+)`.
6. `GIT_OPTIONAL_LOCKS=0 git diff --check caac896db393550817da9e57c56f03f46277cb54..1b05e6105b0d7c98a5b6e037ebd66b916c3a921e -- matharc/v02/topic_observation.py tests/test_v02_topic_observation.py`
   - Exit `0`.
7. `GIT_OPTIONAL_LOCKS=0 git diff --check caac896db393550817da9e57c56f03f46277cb54..1b05e6105b0d7c98a5b6e037ebd66b916c3a921e`
   - Exit `2`; whitespace findings are confined to `logs/adversarial-test-review.log`, `logs/archive-manual-boundary.log`, and `logs/replay-integrity.log`.
8. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives`
   - Exit `0`; `Ran 43 tests in 1.358s`; `OK`; zero skips.
9. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -` with separate `TemporaryDirectory` positive-state, preexisting-partial, import-history-relabel, and manual-reference-laundering probes.
   - Every probe process exited `0`. Ordinary state matrix and isolated existing-observation reload passed. The partial-existing probe failed production load, while both adversarial history rewrites were accepted; exact stdout is recorded above and in P1.
10. `GIT_TERMINAL_PROMPT=0 GIT_OPTIONAL_LOCKS=0 git ls-remote --exit-code origin refs/heads/main`
    - Exit `128`; GitHub port 443 connection failed; no ref was updated.
11. `GIT_OPTIONAL_LOCKS=0 git diff --exit-code HEAD -- <all frozen files and the two caac896 returns>`
    - Exit `0`; reviewed tracked inputs were unchanged before this return.

## Acceptance Identity

Implementation correctness and acceptance identity are separate failures/surfaces:

- The v2 contract is approved against `main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80` and protects the older topic-test hash `1b505da5...`.
- `evidence/A4.json` records source/implementation candidate `3353d6a`, an old human-result hash, and historical `ACCEPTED` state.
- Candidate `1b05e61` changes both production state validation and the protected topic test after that tuple.
- The manifest correctly says `formal_acceptance_current_for_frozen_source: false`.
- This lane did not read beyond the frozen acceptance identity artifacts and cannot validate, renew, impersonate, or issue human acceptance.
- `proposed_state: FAILED` for this lane; no A4 state transition is authorized.

## Residual Risk

- Even a corrected causal invariant built only from recomputable local JSON/SHA-256 fields is not an authenticated append-only history. A writer able to replace every state, literature, and artifact byte remains outside what an unkeyed local integrity check can prove.
- Live remote-main readback is unavailable in this run; only local `origin/main` is pinned.
- Full CI, browser gates, AC-04, AC-05, production/device behavior, live literature, mathematical review, and public release were outside this lane and were not claimed.
- The green focused suite does not override the two fresh negative-control failures.

## Repository Status

- Business project before this return: `main...origin/main`, no tracked changes; five pre-existing/unmanaged untracked frozen-input, prompt, and log files under the `1b05e61` lane directory. This return is the only lane-authored file.
- Harness SSOT real repository: `/Users/vsiyo/Desktop/Opensource_Tool/Harness_Engineering`, `main...origin/main`, already dirty with `22` tracked/index changes and `21` untracked paths. This lane made no Harness SSOT change.

Verdict: FAIL
