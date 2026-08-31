STATE: CONDITIONAL

# A4 Archive Boundary Final Review

Scope was limited to the frozen candidate files and the implementation return. This is a review of the candidate only. It does not accept A4 or T2, create a claim, create proof, create a promotion assertion, or change SSOT/Git/remote state.

## Findings

### HIGH: Replay does not close the persisted case set or per-case no-promotion fields

- `failure_class: REPLAY_CASE_SET_AND_NO_PROMOTION_RECORD_NOT_ENFORCED`
- `failure_origin: matharc/v02/dogfood_archives.py:242-260 and :266-282`
- `file/line: matharc/v02/dogfood_archives.py:238, :247-260`
- `_replay()` calls `_assert_contract_results()` at line 238, but that method only checks the expected fields in the `checks` mapping. It never checks `claim_created` or `trace_created`, although `_case()` emits both fields as `False` at line 203. It also builds a dictionary from the case list and never requires exactly the three contract case IDs, so undeclared or duplicate case records are ignored.
- The replay-level checks at lines 206 and 237 verify the top-level `no_claim_or_trace_created` flag and the absence of selected filesystem artifacts, but they do not make the per-case records consistent with that boundary.
- Independent in-memory negative mutation, without filesystem writes, produced exit 0: `_load_result()` plus `_assert_contract_results()` accepted `claim_created=True` and `trace_created=True` with the remaining contract fields valid. A second in-memory mutation accepted an undeclared fourth case with `promotion_allowed=True`.
- This is a code-path finding, not an inference from a passing test. A persisted payload whose archive digest is recomputed can retain these mutations; no later case validation in `_replay()` rejects them.
- Proposed repair: require a list with exactly the contract case set, reject duplicates/extras, and require strict `False` values for `promotion_allowed`, `claim_created`, and `trace_created` during replay. Add a digest-recomputed negative test for each boundary.

### MEDIUM: Some malformed manual-queue state is reported as missing state

- `failure_class: MANUAL_QUEUE_DIAGNOSTIC_MISCLASSIFICATION`
- `failure_origin: matharc/v02/dogfood_archives.py:47-53; matharc/v02/topic_observation.py:218-228`
- `file/line: matharc/v02/dogfood_archives.py:47-52`
- The public wrapper selects the manual-queue diagnostic only when the underlying message contains `manual queue` or `manual review result`. `ManualReviewItem.from_dict()` reports a missing field as `missing manual-review fields: [...]` (with a hyphen), which is a malformed manual-queue condition but is classified as `topic observation state is missing or invalid`.
- Independent in-memory check using the actual `ManualReviewItem.from_dict()` error produced: `source=missing manual-review fields: ['detail']`; `public=topic observation state is missing or invalid: missing manual-review fields: ['detail']`.
- The valid semantic tampering cases in `tests/test_v02_dogfood_archives.py:194-211` do exercise the manual-queue path, but they do not cover malformed queue shape or an invalid enum value. The latter can also surface the raw `ValueError` from `ManualReviewReason(payload["reason"])` at `topic_observation.py:227`, outside the `TopicObservationError` translation path.
- Proposed repair: carry an explicit validation category from the topic-state loader, or normalize all manual-queue decoding failures to a dedicated `TopicObservationError` category before public translation; do not classify by free-form message text.

## Verified Contract Paths

- `DogfoodArchiveError` is the public archive exception at `matharc/v02/dogfood_archives.py:19-20`. `run()` catches only `TopicObservationError` at lines 47-53 and raises a chained `DogfoodArchiveError` with `raise ... from exc`. The in-memory contract injection check passed (exit 0) for manual-queue, missing-state, and other topic-observation messages. A directly raised non-topic `DogfoodArchiveError` passed through unchanged and was not relabeled.
- Manual-queue state validation is present at `matharc/v02/topic_observation.py:559-575`, and stored manual-review results must match a queue entry at lines 623-635. Replay compares the complete sorted queue entries and IDs at `matharc/v02/dogfood_archives.py:226-229`.
- Fixture and source artifact hashes are checked at `matharc/v02/dogfood_archives.py:72-77` and `:119-144`; replay rechecks contract/source identity at line 220. The residual budget is reconstructed and compared with the contract and persisted snapshot at lines 232-236. Archive digest and canonical queue checks are at lines 262-282.
- Actual no-claim/no-trace filesystem checking remains present at `matharc/v02/dogfood_archives.py:206` and is enforced during both execute and replay. The finding above concerns persisted case-record integrity and exact case closure, not evidence that this code creates those artifacts.

## Command Results

- `git diff --check -- matharc/v02/dogfood_archives.py matharc/v02/topic_observation.py tests/test_v02_dogfood_archives.py tests/test_v02_topic_observation.py`: exit 0.
- `PYTHONDONTWRITEBYTECODE=1 python3` source `compile()` check for `matharc/v02/topic_observation.py`, `matharc/v02/dogfood_archives.py`, and `tests/test_v02_dogfood_archives.py`: exit 0; no bytecode was requested.
- `git diff --binary --no-ext-diff --no-textconv -- matharc/v02/topic_observation.py matharc/v02/dogfood_archives.py tests/test_v02_topic_observation.py tests/test_v02_dogfood_archives.py | shasum -a 256`: exit 0 and matched the frozen combined patch hash.
- The implementation return reports the targeted unittest command as 19 passed and the v02 discovery command as 205 passed with 8 skipped at `implementation-return.json:7-18`. Those commands were not rerun here because their tests create and mutate temporary files, which is outside this strict zero-write review. Their reported pass does not cover the two negative replay conditions above.

## Frozen Identity Check

- Combined patch SHA-256: `11ae14101270c98c54387579917c1c9d20da585d5d33a12dd9ae763c5df18a8f` - matched.
- `matharc/v02/topic_observation.py`: `48cf857cca156a72c3e3676d561801bdd83ca99a6fb91a48aab05a447114bbad` - matched.
- `matharc/v02/dogfood_archives.py`: `7ec934f7330e72e83e4f25bd7eee3e419e66db9121243adef4d343bf3287f5e2` - matched.
- `tests/test_v02_topic_observation.py`: `7f7157c421259c06eb67b6d36e2c2a7c5e092e5d1ef72521064dc4b71d6e5865` - matched.
- `tests/test_v02_dogfood_archives.py`: `c4b8084c0c8d89ff290784911e1b7a9dc17e8036b7bc5733c93e4c82f74d7806` - matched.

## Review Metadata

- `failure_class: CONDITIONAL_REPLAY_BOUNDARY_REVIEW`
- `failure_origin: persisted-result validation omissions and message-marker classification`
- `changed_files:`
  - `matharc/v02/topic_observation.py`
  - `matharc/v02/dogfood_archives.py`
  - `tests/test_v02_topic_observation.py`
  - `tests/test_v02_dogfood_archives.py`
- `residual_risk: The current manual-queue classifier depends on stable free-form diagnostic markers; malformed queue-shape errors can receive the generic state diagnostic, and persisted replay case records are not fully closed under the T2 case/no-promotion schema.`
- `proposed_state: REVIEWED`
