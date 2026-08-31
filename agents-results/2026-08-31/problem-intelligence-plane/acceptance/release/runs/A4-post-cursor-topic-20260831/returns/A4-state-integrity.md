# P0/P1 findings

None. No P0 or P1 finding was identified for the requested persisted `TopicObservationRunner` state-integrity scope.

# Exact commands/results

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_topic_observation`: `Ran 25 tests in 0.088s`, `OK`.
- `PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY' ... PY` independent temporary-directory probe: all four coordinated mutations failed closed.
  - Input projection swap with recomputed batch, projection, and result digests: `TopicObservationError: stored batch input projection fingerprint mismatch`.
  - Forged ordinary input disposition as `HIGH_RISK_EVENT` with recomputed `manual_id` and result digest: `TopicObservationError: high-risk manual disposition conflicts with input projection`.
  - Regular manual queue linkage mutation with recomputed `manual_id` and result digest: `ManualQueueObservationError: stored manual review result does not match exactly one manual queue entry`.
  - Cursor-conflict queue `topic_id` replacement with recomputed `manual_id` and replaced `manual_events` reference: `ManualQueueObservationError: manual event does not describe a cursor conflict`.
- `git diff --check`: passed; no whitespace errors.
- `git diff --binary | shasum -a 256`: `d8d847924653bb6df547094e525b61378d234b727f8f20d93418771c2b1fefd6`, matching the pinned candidate diff.
- The probe used only `tempfile.TemporaryDirectory` state roots and `PYTHONDONTWRITEBYTECODE=1`; no probe state was written in the repository.

# Source identity observed

- Project HEAD: `46d924fbfc4daa00eb02d3ffaf06cb17a78be4fe`, matching the pinned HEAD.
- Candidate changed source file SHA-256: `matharc/v02/topic_observation.py` = `fed3ee26dde4f3a19bbc5a624a723ed11d4463d45adbdefe8d56aebaf7a018ac`.
- Candidate focused test file SHA-256: `tests/test_v02_topic_observation.py` = `4b5caff5e3e4c9328eb5f099d2d996a35175602f8cbaf3f66b73bf372ff4d27f`.
- A4 node SHA-256: `5aa099a7ebaf6f5ee8963131b282126bc78cc50a869405048f9f92878c6e79a4`.
- T2 to A4 edge observed at `agents-results/2026-08-31/problem-intelligence-plane/.ssot/edges/E-T2-A4.json`, SHA-256 `331d94dcdd5ede19482ce5d4b098d0ea9e1b32b9936a5a51f1b63c7e8acc23eb`.
- T2 evidence SHA-256: `42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3`.
- Latest input-projection remediation record, `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/input-projection/implementation-return.json`, SHA-256: `04b6bd9056ae4fb8157954326ea065b708c917d2c666a35940aa1cd9da457b89`.
- The A4 node is `READY`, consumes T2, and has `write_authority: evidence-only`; T2 evidence itself records that a separate A4 acceptance decision remains unverified.

# Protected-test integrity

- The three remediation red cases are present and passed: cross-batch input projection swap, forged high-risk manual disposition, and cursor-conflict manual entry topic binding after ID recomputation.
- The normal-path protected cases are present and passed: restart replay without second import, preexisting-observation idempotency/replay, restricted-observation pending replay, cross-batch duplicate suppression, high-risk manual queue creation without import, and the cursor-conflict non-advancing behavior.
- The current test diff is `401` insertions and `0` deletions for `tests/test_v02_topic_observation.py`. No deletion, skip, weakened assertion, or fixture-specific production branch was observed in the reviewed test scope.
- The four independent probes additionally exercised the regular manual queue linkage boundary beyond the three named remediation red cases.

# Acceptance-criterion disposition

- Persisted input identity is bound to a canonical projection containing the input ID, complete source-observation identity, content digest, byte size, and sorted risk flags. Loader checks recomputed projection fingerprints and projection digests: `VERIFIED` for this lane.
- Persisted item disposition is cross-checked against the projection, result, literature state, processed-input state, seen keys, and import disposition. Forged ordinary-to-manual conversion failed as `TopicObservationError`: `VERIFIED` for this lane.
- A regular manual result must match exactly one queue entry by manual ID, topic, cursor, and input, with matching reason and evidence: `VERIFIED` for this lane.
- Cursor-conflict queue entries must be deterministic, belong to the state topic, use the cursor input identity, and have a matching manual event. Foreign-topic substitution with local ID/event recomputation failed as `ManualQueueObservationError`: `VERIFIED` for this lane.
- `ManualQueueObservationError` is a subclass of `TopicObservationError`; the observed failures therefore normalize within the requested error boundary.
- This lane cannot accept A4. It reports only the independent state-integrity disposition; it does not move the A4 node, write A4 evidence, or authorize R1 or release.

# Residual risk

The local digests and IDs provide fail-closed detection for the reviewed coordinated mutations, but they are not an external trust anchor. A fully compromised host that can replace every persisted input, literature record, artifact, and local digest remains outside this bounded state-integrity proof. This review also does not establish live retrieval, independent mathematical proof review, production/device evidence, remote readback, or human A4 acceptance.

# Proposed state

`VERIFIED`

This is the proposed state of this independent review lane only. It is not an A4 acceptance decision.
