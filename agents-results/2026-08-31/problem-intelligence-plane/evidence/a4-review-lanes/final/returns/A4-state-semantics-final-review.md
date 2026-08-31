# A4 Persisted State Semantics Review

Verdict: **FAIL**

Scope: read-only review of the current uncommitted changes in `matharc/v02/topic_observation.py`, `matharc/v02/dogfood_archives.py`, `tests/test_v02_topic_observation.py`, and `tests/test_v02_dogfood_archives.py`.

## Findings

### P1: recomputable result digests do not preserve `TopicItemStatus` semantics

This is a real persisted-state invariant violation. `result_digest_sha256` is checked only against the mutable result object (`topic_observation.py:593-595`). Once recomputed, the loader independently constrains result identity, item IDs, observation IDs, and the aggregate `MANUAL_REVIEW` versus `APPLIED` run status (`:598-657`), but it does not derive or bind each non-manual item disposition to import evidence. Thus an original `IMPORTED` item can be changed to `IDEMPOTENT`, `DUPLICATE`, or `PENDING` while retaining valid fingerprints, observation ID, batch digest, processed-input mapping, cursor chain, and aggregate `APPLIED` status.

Focused temporary-state reproduction:

```
original IMPORTED -> IDEMPOTENT: accepted
original IMPORTED -> DUPLICATE: accepted
original IMPORTED -> PENDING: accepted
```

Each case recomputed `batches["c0"]["result_digest_sha256"]`, reloaded the runner, and replayed successfully with the forged item status.

The problem is broader than `IMPORTED -> DUPLICATE`: a high-risk `MANUAL_REVIEW` item can be changed to `IMPORTED` with `manual_id=None` and the batch run status changed to `APPLIED`. The queue entry remains orphaned because the loader requires every manual result to reference exactly one queue entry (`:611-624`) but never requires every queue entry to be referenced. The altered state reloads and replays as `REPLAYED`, while `LiteratureBase` still contains zero observations.

`DogfoodArchiveRunner._replay` does not close this gap. It verifies cursor positions, a canonical manual queue digest, observation counts, and its archive contract (`dogfood_archives.py:219-240`), but it does not bind each stored topic item status to the queued entry or import disposition. In a temporary dogfood run, changing the stored manual item at `dogfood-c2` to `IMPORTED`, clearing `manual_id`, changing the stored run status to `APPLIED`, and recomputing the result digest was accepted by archive replay. The persisted queue remained, so the archive still reported two blocking manual IDs.

Existing added tests cover a stale digest, result identity cross-fields, illegal non-manual `manual_id`, manual linkage, and aggregate run status. They do **not** cover the accepted semantic mutations above. A red test must mutate an initially imported item to `DUPLICATE` (and ideally `IDEMPOTENT`/`PENDING`) after recomputing the result digest and require load/replay failure. A second red test must mutate a manual result to a non-manual status with `manual_id=None`, recompute the digest and aggregate status, and require failure for the orphan queue / missing import evidence.

Repair direction: make item disposition a validated consequence of independently durable source/import evidence, not merely a field inside its own recomputable digest. At minimum, validate all queue entries are referenced exactly once by matching manual results and validate `DUPLICATE` ordering/identity against preceding persisted inputs. The `IMPORTED`/`IDEMPOTENT`/`PENDING` distinction also needs a durable evidence model that can be checked independently of the mutable result object; a non-secret JSON digest alone cannot provide that protection.

### P0

No P0 defect was identified in the reviewed diff. The observed P1 corrupts the topic-observation audit record and passes dogfood replay, but this path does not itself create a claim, trace, promotion authorization, or code execution. The archive's explicit per-case no-promotion checks remain present.

## Commands Run

```
python -m unittest tests.test_v02_topic_observation tests.test_v02_dogfood_archives -v
# Result: 22 tests passed.

git diff --check -- matharc/v02/topic_observation.py matharc/v02/dogfood_archives.py tests/test_v02_topic_observation.py tests/test_v02_dogfood_archives.py
# Result: passed.

python - <<'PY'
# Temporary-state matrix: create an IMPORTED batch, replace its item status
# with IDEMPOTENT/DUPLICATE/PENDING, recompute result_digest_sha256, reload,
# and replay.
PY
# Result: all three forged states accepted.

python - <<'PY'
# Temporary high-risk batch: replace MANUAL_REVIEW with IMPORTED, clear
# manual_id, set run status APPLIED, recompute result_digest_sha256, reload,
# and replay; repeat against DogfoodArchiveRunner.
PY
# Result: both generic state and dogfood archive replay accepted.
```

## Repository State

- Business project: the four reviewed implementation/test files were already modified; this review added only this evidence report.
- Harness SSOT: no Harness SSOT source was edited. `git -C develop/Harness status --short` resolves to the shared project worktree and consequently reports the same existing project modifications plus evidence directories.
