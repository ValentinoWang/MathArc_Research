# Independent Post-Fix Review: A4-1b05e61-post-fix-review

Lane: `replay-closure`
Direct parent finding: `A4-caac896-replay-integrity`
Pinned candidate: `HEAD` and live `origin/main` at `1b05e6105b0d7c98a5b6e037ebd66b916c3a921e`
Decision ref: `decision.problem-intelligence.amendment@2`
Invalidation key: `acceptance.problem-intelligence.dogfood`
Boundary: offline, fixed repository sources, non-mathematical-proof, non-public-release

## Findings

### P0

None observed.

### P1

1. **A coordinated literature replacement still bypasses replay integrity.**

   The fix at `matharc/v02/topic_observation.py:974-977,984,1114-1116,1286-1288`
   turns the persisted-literature check into equality between the set of current
   observation IDs and the set of IDs referenced by current batch evidence. It
   does not authenticate the literature store, preserve historical record
   identity, enforce unique idempotency keys across distinct observation IDs, or
   bind a literature record to the cursor that first persisted it.

   A fresh temporary-directory probe performed the parent mutation, then also
   replaced the persisted literature set with only `OBS-B` (including removing
   the `OBS-A` artifact record/file). The coordinated batch state referenced
   `OBS-B` from `c0/A` and reclassified `c1/B` as
   `SEEN_OBSERVATION_KEY/DUPLICATE`; all state digests available to the local
   implementation were recomputed. The loader returned `next_cursor=c2`.

   A second fresh probe appended a distinct persisted record `OBS-C` with the
   same idempotency key as `OBS-A`, changed the duplicate batch evidence to
   reference `OBS-C`, and kept the second disposition as
   `SEEN_OBSERVATION_KEY/DUPLICATE`. The loader again returned `next_cursor=c2`.

   These are equivalent persisted cross-batch replay bypasses, not the original
   leftover-record shape. They block closure of AC-02.

2. **The candidate is not validly rebound to the approved A4 acceptance identity.**

   The contract remains bound to `main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
   and locks `tests/test_v02_topic_observation.py` to
   `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56`
   (`acceptance-contract.md:15,33-38`). The current candidate has the protected
   topic-test hash `a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb`.
   The frozen manifest explicitly records
   `formal_acceptance_current_for_frozen_source: false`, and `evidence/A4.json`
   still records source identity `3353d6a` and `ACCEPTED` rather than the
   candidate identity. This blocks formal A4 acceptance independently of the
   replay result.

### P2

3. **The complete candidate diff is not whitespace-clean.**

   `git diff --check caac896db393550817da9e57c56f03f46277cb54..1b05e6105b0d7c98a5b6e037ebd66b916c3a921e`
   returned status `2`, with trailing-whitespace diagnostics in the added
   `caac896` review log artifacts. The implementation and topic-test portion
   of the diff passed the same check. This is acceptance-hygiene evidence, not
   the cause of the replay finding.

## Identity and SHA verification

The first read was the frozen manifest. Its source identities resolved as:

```text
HEAD       1b05e6105b0d7c98a5b6e037ebd66b916c3a921e  PASS
origin/main 1b05e6105b0d7c98a5b6e037ebd66b916c3a921e  PASS
parent     caac896db393550817da9e57c56f03f46277cb54  PASS
tree       8c35023d729d40b7828e1c82bcfdc35b64dad922  PASS
```

`git ls-remote origin refs/heads/main` returned
`1b05e6105b0d7c98a5b6e037ebd66b916c3a921e refs/heads/main`.
The manifest `contract_baseline` exists as commit
`3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`, and the test bytes at that
commit hash to the manifest `contract_topic_test_sha256` value
`1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56`.
The manifest decision ref and invalidation key match the contract. Its review
task/direct-parent identities match this lane and the parent return; its
boundary is consistent with the contract scope.

All eight manifest file SHA-256 checks passed:

| File | SHA-256 |
| --- | --- |
| `matharc/v02/topic_observation.py` | `f191c010e6388bc5de07f979c9ca90ab10c83a3d74db7a31827e9f3c7887dfd3` |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` |
| `tests/test_v02_topic_observation.py` | `a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb` |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` |
| `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A4-topic-observation-dogfood/acceptance-contract.md` | `4b7ac7ea035d59be7c87fef9867b97529f8b00f68c207d7460963cd625095c84` |
| `agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A4.json` | `8dfe33ef6a3f2cc8666e2d948694ce89344f437710dd51eeda63071e6cd4e1d8` |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/A4.json` | `0e22f563f17c00506ba7d482e8addb37b5e72ce52194c5e4d876ad8abbfc153b` |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures/three-real-archives.json` | `475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c` |

The direct-parent return was read at
`agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-review-lanes/caac896/returns/replay-integrity.md`;
its SHA-256 is
`0b20cb5d20f305e6c399a7b62f0302905195f52eceedcdab20e8ecd07ddb08f8`.

## Commit diff review

`git diff --stat caac896db393550817da9e57c56f03f46277cb54..1b05e6105b0d7c98a5b6e037ebd66b916c3a921e`
reported 8 changed paths and 36,909 insertions. The diff added the parent lane
artifacts and modified only the topic implementation and protected topic test
for the functional repair. The relevant implementation change adds
`referenced_literature_ids` and the set-equality rejection; the relevant test
change is `test_cross_batch_rewrite_cannot_hide_the_original_literature_record`
at `tests/test_v02_topic_observation.py:579-626`.

`git diff --exit-code 1b05e6105b0d7c98a5b6e037ebd66b916c3a921e --` followed by
all eight frozen file paths exited `0`; no frozen file had an uncommitted
worktree change. The source/test-only `git diff --check` exited `0`.

## Focused tests

Commands and results:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_topic_observation
exit 0; Ran 30 tests in 0.104s; OK

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_dogfood_archives
exit 0; Ran 13 tests in 1.310s; OK
```

The topic test count includes the new negative test. The dogfood tests cover
the fixed three-archive contract, replay, budget/manual boundaries, and
canonical archive-state comparison. No full regression, browser gate, or
new human run was executed in this focused lane.

## Exact parent attack

Command: fresh inline Python probe in a `TemporaryDirectory`, using
`tests.test_v02_topic_observation.input_for` and `batch`, creating valid
`c0/A` and `c1/B`, relocating B's complete projection/fingerprint/observation
identity/evidence/result to `c0/A`, recomputing `c0` batch/projection/binding/
result digests, changing `c1/B` to `SEEN_OBSERVATION_KEY/DUPLICATE`,
recomputing its result digest, and loading a fresh runner.

Result:

```text
literature_ids= ['OBS-A', 'OBS-B']
batch_evidence_referenced_ids= ['OBS-B', 'OBS-B']
recomputed_digests=c0.batch,c0.projection,c0.binding,c0.result,c1.result
loader=FAIL_CLOSED
error= persisted literature observations do not match stored batch evidence
```

The implementation therefore closes the exact parent attack when the original
unreferenced `OBS-A` literature record remains present.

## Equivalent literature-record probes

Each probe used a fresh temporary directory and mutated only temporary JSON/
artifact files.

| Probe | Result |
| --- | --- |
| Retain orphaned/unreferenced `OBS-B` after removing its batch and recomputing current state collections | `FAIL_CLOSED`; `TopicObservationError: persisted literature observations do not match stored batch evidence` |
| Append an exact duplicate with the same `observation_id` | `FAIL_CLOSED`; `ValueError: duplicate observation id` during literature load |
| Append a duplicate logical identity with new `observation_id` but leave it unreferenced | `FAIL_CLOSED`; `TopicObservationError: persisted literature observations do not match stored batch evidence` |
| Append distinct `OBS-C` with the same idempotency key, reference it from a `SEEN_OBSERVATION_KEY/DUPLICATE` batch, and recompute state digests | `ACCEPTED_UNEXPECTEDLY`; `next_cursor=c2`; loaded IDs `['OBS-A', 'OBS-C']` |
| Replace the persisted `OBS-A` literature/artifact set with the unique `OBS-B` record/artifact while preserving the coordinated batch rewrite and recomputed state digests | `ACCEPTED_UNEXPECTEDLY`; `next_cursor=c2`; loaded IDs `['OBS-B']` |

The last two results are the P1 residual bypass. A set equality check proves
current referential closure only; it does not prove that the current literature
records are the records historically persisted by the cursor batches.

## Protected-test and acceptance assessment

| Item | Disposition |
| --- | --- |
| Candidate HEAD and live `origin/main` | PASS: both are `1b05e6105b0d7c98a5b6e037ebd66b916c3a921e` |
| Candidate source/test file hashes vs frozen manifest | PASS: all eight manifest hashes match |
| Protected `tests/test_v02_topic_observation.py` | FAIL identity: contract `1b505d...`, candidate `a6ac5f...`; the candidate test is additive but not the locked bytes |
| Protected `tests/test_v02_dogfood_archives.py` | PASS: candidate equals locked `e1efa41...` |
| Exact parent replay attack | PASS: fails closed with the new literature-reference equality check |
| Equivalent replaced/duplicated literature attacks | FAIL: loader accepts both coordinated variants |
| Full diff whitespace check | FAIL: status `2` on added parent log artifacts; functional source/test subset passes |

## AC disposition

| Requirement | Lane disposition |
| --- | --- |
| AC-01 | Focused dogfood tests pass for the fixed T2 fixture/archive boundary; not a formal release decision |
| AC-02 | **FAIL**. The exact parent shape is closed, but referenced duplicate-key and replaced-literature variants reach `c2` |
| AC-03 | Focused dogfood boundary tests pass; no broader acceptance claim made |
| AC-04 | MISSING in this lane: no full regression, browser gate, or technical precheck synthesis |
| AC-05 | **FAIL/UNAVAILABLE**: contract and protected-test identity remain bound to the older baseline; current A4 evidence is stale for this candidate |
| H-01 | UNAVAILABLE: this lane did not create or validate a new human run |

## Residual risk and required authority boundary

An actor who can rewrite the unkeyed persisted state and literature JSON can
also replace the historical literature set, reuse an idempotency key under a
new observation ID, and recompute all currently checked digests. The current
loader has no authenticated or immutable per-cursor literature ledger and no
cross-record idempotency-key uniqueness check. A repair would need a historical
source-batch commitment or authenticated literature manifest, plus explicit
duplicate-identity rejection, followed by a new negative test for both
accepted variants.

This independent lane is evidence only and cannot accept A4. A4 formal
acceptance remains unavailable until the contract, protected-test identity,
current source identity, and a new human run are validly rebound by their named
authorities. The business project status observed before this return write was
`## main...origin/main` with only the untracked `1b05e61` lane directory. The
Harness SSOT status was also `## main...origin/main` but had unrelated tracked
and untracked changes; it was left untouched.

Verdict: FAIL
