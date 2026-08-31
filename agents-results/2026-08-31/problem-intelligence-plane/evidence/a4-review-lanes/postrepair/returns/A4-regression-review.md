STATE: PASS

Scope: independent, zero-write post-repair review of the four implementation/test files listed in the task, with T2 and A4 remediation evidence used as supporting records. No SSOT node was accepted.

Findings:

- [PASS] State-version handling remains fail-closed and does not alter the batch contract. `matharc/v02/topic_observation.py:27-29` keeps batch schema `1.0` separate from persisted state schema `1.1`; `:504-527` writes and requires the new state version and rejects incompatible legacy state. `matharc/v02/dogfood_archives.py:13` and `:254-279` likewise bind the persisted archive schema and archive digest.
- [PASS] Normal cursor replay is preserved. `topic_observation.py:335-394` returns `REPLAYED` for the same batch digest without re-importing and advances the cursor only for a newly accepted batch; `dogfood_archives.py:139-153` exercises the same replay and duplicate sequence. Covered by `tests/test_v02_topic_observation.py:49-60` and `tests/test_v02_dogfood_archives.py:20-40,74-80`.
- [PASS] Duplicate and conflict routing is preserved. `topic_observation.py:402-430` keeps same-fingerprint input reuse and seen observation keys as `DUPLICATE`, while changed input identity routes to manual review; high-risk and budget paths remain manual-only at `:412-427`. Collision review and recheck are explicitly exercised at `dogfood_archives.py:149-153`. Covered by `tests/test_v02_topic_observation.py:62-138,154-170` and `tests/test_v02_dogfood_archives.py:43-60`.
- [PASS] Manual-review persistence and new integrity fields are consistent. Batch result, input fingerprint, observation-ID, and digest cross-checks are enforced at `topic_observation.py:540-626`; persisted manual entries are parsed at `:627-631`. The archive binds the normalized queue and IDs at `dogfood_archives.py:210-231,254-274`. The added negative coverage for stored result tampering and same-ID manual-queue tampering is present at `tests/test_v02_topic_observation.py:172-204` and `tests/test_v02_dogfood_archives.py:194-212`.
- [PASS] Source pinning and byte integrity remain enforced. `dogfood_archives.py:111-126` rechecks source artifact existence and SHA-256, and `:129-137` carries canonical URI, pinned version, locator, and content digest into observations/provenance. The T2 assertions require these fields at `tests/test_v02_dogfood_archives.py:62-70`; the recorded T2 matrix also marks source-byte and provenance checks passed (`evidence/T2.json:29-36`).
- [PASS] Budget snapshot behavior remains deterministic. Contract identity is checked at `dogfood_archives.py:66-69`; execution compares the spent snapshot at `:155-164`, and replay reconstructs and compares both snapshot and digest at `:224-228,271-274`. The altered-snapshot and recomputed-digest negatives are covered by `tests/test_v02_dogfood_archives.py:126-169`.
- [PASS] No-claim/no-trace and no-promotion boundaries remain intact. `dogfood_archives.py:165-168,197-198,229-230` requires a blocked archive, checks for forbidden artifacts on initial run and replay, and all cases remain non-promotable at `:194-195`; the test asserts these boundaries at `tests/test_v02_dogfood_archives.py:29-31,60-72`.
- [PASS] Tests were expanded, not weakened within the permitted review scope. The current files retain normal replay, duplicate, conflict, risk, budget, and non-claim assertions and add fail-closed tamper cases at `tests/test_v02_topic_observation.py:172-204` and `tests/test_v02_dogfood_archives.py:126-212`. The remediation ledger records the three added test names and a 14-test focused pass (`ledger/A4-persisted-state-repair.json:38-73`). No skip or assertion removal is present in the reviewed test files.

Command result:

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives` -> exit code `0`; `Ran 14 tests`; `OK`.

Residual risk:

- Legacy topic-observation state without the `1.1` integrity fields is intentionally rejected rather than migrated (`topic_observation.py:515-527`). The local persisted digests detect inconsistent records but do not provide an external trust anchor against a fully compromised host, matching the remediation ledger's stated residual risk (`ledger/A4-persisted-state-repair.json:86-90`).
- This review establishes focused local behavior only. It does not establish live retrieval, independent mathematical proof review, external-service behavior, or release/SSOT acceptance. The T2 evidence explicitly leaves the separate A4 decision unverified (`evidence/T2.json:57-64`).

failure_class: none
failure_origin: none
changed_files:
  - matharc/v02/dogfood_archives.py
  - matharc/v02/topic_observation.py
  - tests/test_v02_dogfood_archives.py
  - tests/test_v02_topic_observation.py
proposed_state: REVIEWED
