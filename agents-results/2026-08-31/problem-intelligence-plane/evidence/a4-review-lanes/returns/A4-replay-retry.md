STATE: CONDITIONAL

Findings:

- severity: HIGH
  path: matharc/v02/dogfood_archives.py
  line: 207-216
  finding: Restart compares only manual_id values and checks reconstructed budget equality. It does not bind the complete manual-queue entries to the persisted archive, so a queue entry can retain the same manual_id while its reason, detail, cursor, topic_id, or input_id is changed and still pass. This also leaves persisted replay state only partially revalidated.
  failure_class: persisted_manual_queue_semantic_integrity_gap
  failure_origin: implementation; _replay performs ID-only queue comparison. The test covers queue removal at tests/test_v02_dogfood_archives.py:82-89, but not same-ID field tampering.

- severity: HIGH
  path: matharc/v02/topic_observation.py
  line: 501-507
  finding: Persisted batch records are parsed but their stored batch_digest_sha256 is not recomputed against the stored result, and dogfood replay does not validate each stored batch result against its cursor/input history. A state mutation that preserves valid result enums, final cursors, observation counts, and manual IDs can therefore evade the replay failure-closed boundary.
  failure_class: persisted_replay_state_digest_not_revalidated
  failure_origin: implementation; state loading validates shape only and dogfood replay checks final cursor/counts at matharc/v02/dogfood_archives.py:205-211.

Assessment:

- Source, fixture, and contract drift is checked on every run through matharc/v02/dogfood_archives.py:40-44, 47-70, 79-125, and 199-201.
- Normal cursor replay, input deduplication, missing-state detection, and queue-removal detection are covered by matharc/v02/topic_observation.py:316-395 and tests/test_v02_dogfood_archives.py:74-89.
- Budget drift is correctly fail-closed: matharc/v02/dogfood_archives.py:212-216 requires the rebuilt ledger and persisted snapshot to equal the contract, while tests/test_v02_dogfood_archives.py:126-150 recompute both internal digests and still expect rejection.
- The T2 evidence is not an A4 acceptance record: agents-results/2026-08-31/problem-intelligence-plane/evidence/T2.json:56-60 explicitly leaves the separate A4 decision unverified. Its recorded source revision also differs from the frozen A4 identity supplied for this review.

command_result: `python3 -m unittest -v tests.test_v02_dogfood_archives` not run; the conclusion is based on the frozen source/test/evidence read and the targeted static gaps above. T2.json:15-27 reports the focused test as passed, but that report was not treated as independent A4 execution evidence. Frozen SHA checks passed for dogfood_archives.py (2573c6a2b8486931abaabe589d73f6df51a57161badf5463e086e100bdb2dec9), tests/test_v02_dogfood_archives.py (cd8b242ac75add9915504e61bc9c2236a1331e817327bf53322d38193403aff6), and T2.json (42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3).

residual_risk: A locally tampered persisted state can preserve superficial IDs/counts and be accepted on restart; no A4 acceptance, live retrieval, independent mathematical proof review, or public promotion is established.

failure_class: persisted_state_semantic_integrity_gap
failure_origin: dogfood replay validates hashes for external source/fixture inputs and the budget snapshot, but not the complete semantics of persisted queue and batch state.
changed_files:
- matharc/v02/dogfood_archives.py
- matharc/v02/topic_observation.py
- matharc/v02/budget.py
- tests/test_v02_dogfood_archives.py
- agents-results/2026-08-31/problem-intelligence-plane/evidence/T2.json
- agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures/

proposed_state: REVIEWED
