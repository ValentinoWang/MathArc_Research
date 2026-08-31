# A4 Regression And Scope Review

Verdict: CONDITIONAL

## Scope reviewed

- `matharc/v02/topic_observation.py`
- `matharc/v02/dogfood_archives.py`
- `tests/test_v02_topic_observation.py`
- `tests/test_v02_dogfood_archives.py`

The repair is narrowly scoped to fail-closed validation of persisted
topic-observation batches, manual-review linkage, and dogfood archive replay.
It adds semantic checks after digest recomputation, preserving the intended
boundary that no claim or trace may be created by this pipeline.

## Positive findings

- Normal fresh execution and replay remain covered: the focused tests retain
  single-topic restart/replay and three-archive replay assertions.
- The new tests strengthen coverage rather than replacing it. They cover
  stored-result digest and cross-field tampering, manual queue identity and
  linkage, duplicate/missing/extra archive cases, and false promotion/claim/
  trace flags after archive-digest recomputation.
- Public exception coherence is retained: malformed topic state remains a
  `TopicObservationError` (with the new
  `ManualQueueObservationError` subclass); archive callers receive
  `DogfoodArchiveError` chained from the topic-state cause.

## Blocking condition

Persisted-artifact compatibility is not addressed.

1. `topic-observation-state.json` changes from state schema `1.0` to `1.1`
   and the loader accepts only `1.1`
   (`matharc/v02/topic_observation.py:529`, `:549`). A compatibility probe
   changed a valid fresh state to `1.0`; restart failed with
   `TopicObservationError: topic observation state does not match runner`.
2. `dogfood-archives.json` newly requires `blocking_manual_queue` but retains
   archive schema `1.0` (`matharc/v02/dogfood_archives.py:286`). A probe
   constructed a digest-valid archive without that new field; replay failed
   with `DogfoodArchiveError: missing persisted archive fields:
   ['blocking_manual_queue']`.

The change therefore breaks replay of all pre-repair persisted states and
archives without a versioned migration or an explicit, approved invalidation
policy. Before promotion, either add and test a deterministic migration from
the former formats, or version the archive format and document/test the
intentional invalidation and recovery path.

## Verification

- `python3 -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives`
  - PASS: 22 tests.
- `python3 -m unittest discover -s tests -p 'test_v02*.py' -q`
  - PASS: 208 tests, 8 skipped.
- `git diff --check -- matharc/v02/topic_observation.py matharc/v02/dogfood_archives.py tests/test_v02_topic_observation.py tests/test_v02_dogfood_archives.py`
  - PASS: no whitespace errors.

No source or test files were changed by this review.
