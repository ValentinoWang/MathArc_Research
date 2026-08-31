STATE: PASS

Findings (severity-ranked):

- severity: NONE (no blocking finding in the requested mutation set)
  file/line: matharc/v02/topic_observation.py:341-361, 534-684
  finding: No fail-open `continue`, weak queue-only shortcut, or state-ordering bypass was found. `manual_queue` and `next_cursor` both call `_load_state`; `run()` calls `_load_state` before checking the replayed batch digest. `_load_state` validates the complete manual queue before batches, validates every stored result before adding it to `validated_batches`, and validates the complete cursor chain before returning state.
  failure_class: none
  failure_origin: none in the frozen candidate

Requested persisted-state cases:

- deleted manual queue entry: rejected by the exact-one queue match at matharc/v02/topic_observation.py:623-636; covered by tests/test_v02_topic_observation.py:225-243.
- result `manual_id` substitution with a recomputed result digest: rejected unless it names exactly one matching queue entry with the same topic, cursor, and input; the result digest is checked first at matharc/v02/topic_observation.py:603-607; covered by tests/test_v02_topic_observation.py:206-223.
- queue `manual_id` mismatch: rejected because the ID is recomputed from all queue fields at matharc/v02/topic_observation.py:567-575; covered by tests/test_v02_topic_observation.py:245-260.
- queue reason/detail/cursor/topic_id/input_id changes retaining `manual_id`: rejected by the same full-field derivation at matharc/v02/topic_observation.py:568-575. The permitted prior review records the five-field semantic-tamper coverage at the dogfood archive boundary; the focused run also passed `test_same_manual_id_manual_queue_semantic_tampering_fails_closed`.
- non-manual result with `manual_id`: rejected by TopicItemResult construction at matharc/v02/topic_observation.py:239-249; covered by tests/test_v02_topic_observation.py:262-276.
- batch status mutation with a recomputed result digest: rejected when stored status does not equal the derived manual-versus-applied status at matharc/v02/topic_observation.py:616-622; covered by tests/test_v02_topic_observation.py:278-292.
- normal replay: the persisted state is fully validated before the replay return at matharc/v02/topic_observation.py:355-361; restart replay without a second import passed in tests/test_v02_topic_observation.py:49-60.

The manual queue is validated before any stored batch can be accepted. Queue fields are bound indirectly through the derived manual ID, while result linkage binds the derived ID to topic, cursor, and input. The batch digest binds topic, cursor, next cursor, and all input fingerprints at matharc/v02/topic_observation.py:662-669. No requested mutation can reach the replay return after digest recomputation.

Non-blocking residual risk:

- severity: P2/LOW
  file/line: matharc/v02/topic_observation.py:102-111, 568-575, 605-669
  finding: Manual IDs use a 24-hex-character prefix of a SHA-256 digest, and persisted result/batch digests are local integrity signals without an external trust anchor. A fully compromised host or deliberate digest collision is outside this local fail-closed check. This does not open any of the requested single-record mutations.
  failure_class: local_digest_without_external_trust_anchor
  failure_origin: design boundary retained in the listed prior findings

Test command/output:

- command: `python3 -B -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives`
- output: exit code 0; 19 tests ran; all passed; `OK`.

Frozen identity check:

- combined patch: expected `11ae14101270c98c54387579917c1c9d20da585d5d33a12dd9ae763c5df18a8f`; observed the same SHA-256 from `git diff --no-ext-diff --binary HEAD -- matharc/v02/topic_observation.py matharc/v02/dogfood_archives.py tests/test_v02_topic_observation.py tests/test_v02_dogfood_archives.py | shasum -a 256`.
- matharc/v02/topic_observation.py: expected and observed `48cf857cca156a72c3e3676d561801bdd83ca99a6fb91a48aab05a447114bbad`.
- matharc/v02/dogfood_archives.py: expected and observed `7ec934f7330e72e83e4f25bd7eee3e419e66db9121243adef4d343bf3287f5e2`.
- tests/test_v02_topic_observation.py: expected and observed `7f7157c421259c06eb67b6d36e2c2a7c5e092e5d1ef72521064dc4b71d6e5865`.
- tests/test_v02_dogfood_archives.py: expected and observed `c4b8084c0c8d89ff290784911e1b7a9dc17e8036b7bc5733c93e4c82f74d7806`.
- agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/manual-linkage-v2/implementation-return.json was absent during the review.

changed_files:
- matharc/v02/topic_observation.py
- matharc/v02/dogfood_archives.py
- tests/test_v02_topic_observation.py
- tests/test_v02_dogfood_archives.py

residual_risk: Local digest integrity has no external trust anchor; no additional fail-open path was found in the requested state transitions.
failure_class: none for the requested mutation set
failure_origin: none in the frozen candidate; the residual trust boundary is recorded above
proposed_state: REVIEWED
