STATE: CONDITIONAL

Findings:

- severity: P1/HIGH (resolved for the requested queue-field mutations)
  path: matharc/v02/dogfood_archives.py:218-221
  finding: Dogfood replay now compares the complete reconstructed manual queue against the persisted archive entry list, after _load_result also canonicalizes each persisted entry and checks its manual_id list. Changing reason, detail, cursor, topic_id, or input_id while preserving manual_id therefore fails closed at replay. The five mutations are covered by tests/test_v02_dogfood_archives.py:194-211.
  failure_class: persisted_manual_queue_semantic_integrity_gap
  failure_origin: repaired implementation; the prior ID-only comparison was replaced with full-entry digest comparison.

- severity: P1/HIGH (partially resolved; residual linkage gap remains)
  path: matharc/v02/topic_observation.py:568-612
  finding: Stored result digests are now recomputed, and result topic_id, cursor, next_cursor-derived batch digest, input IDs, observation IDs, processed fingerprints, and cursor-chain linkage are checked. The covered digest and cross-field mutations fail closed, as exercised by tests/test_v02_topic_observation.py:172-204. However, TopicItemResult.manual_id is only validated as non-empty at :225-235; _load_state does not require a manual-review result manual_id to name a matching manual_queue entry. A syntactically valid stored manual result can therefore change manual_id to another non-empty value, recompute result_digest_sha256, and retain all checked cursor/input/observation links while replay remains accepted. Result status/item-status consistency is likewise not enforced by TopicBatchResult.from_dict or _load_state.
  failure_class: persisted_batch_result_manual_linkage_gap
  failure_origin: implementation; digest integrity and several structural links were added, but the result-to-manual-queue relationship and complete result semantic invariants remain unbound.

Normal replay evidence: the focused command passed, including restart replay without a second import and the three-archive dogfood replay/non-promotion boundary.

command_result: `python3 -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives` exited 0; 14 tests ran and all passed (`OK`).

residual_risk: The manual queue field mutations requested here fail closed only at the dogfood archive replay boundary; TopicObservationRunner.manual_queue itself still parses a syntactically valid tampered entry until an archive comparison is performed. The remaining batch-result manual_id/status semantic gap permits a coordinated-looking but locally digest-valid state mutation. Local digests also have no external trust anchor against a fully compromised host. No A4 acceptance, release, promotion, or independent mathematical proof is established.

failure_class: persisted_state_semantic_integrity_gap
failure_origin: the repair binds persisted records to local digests and selected cross-field invariants, but not every semantic relationship between batch results, manual queue entries, and imported literature state.

changed_files:
- matharc/v02/dogfood_archives.py
- matharc/v02/topic_observation.py
- tests/test_v02_dogfood_archives.py
- tests/test_v02_topic_observation.py

proposed_state: REVIEWED
ssot_acceptance: NONE; no SSOT node accepted.
