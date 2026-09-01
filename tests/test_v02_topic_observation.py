from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.budget import BudgetLedger
from matharc.v02.schema import digest_json
from matharc.v02.source_observation import LicenseStatus, new_observation
from matharc.v02.topic_observation import (
    ManualQueueObservationError,
    ManualReviewReason,
    TopicItemStatus,
    TopicObservationBatch,
    TopicObservationError,
    TopicObservationInput,
    TopicObservationRunner,
    TopicRunStatus,
    _input_projection_binding_digest,
    _input_projection_digest,
)


def input_for(input_id: str, *, risk_flags: tuple[str, ...] = ()) -> TopicObservationInput:
    content = f"source bytes for {input_id}".encode("utf-8")
    return TopicObservationInput(
        input_id=input_id,
        observation=new_observation(
            observation_id=f"OBS-{input_id}",
            canonical_uri=f"https://example.test/{input_id}",
            pinned_version="v1",
            license_status=LicenseStatus.OPEN,
            license_basis="fixture license",
            content_summary="Fixture bibliographic metadata.",
            summary_basis="fixture",
            media_type="text/plain",
            content_digest_sha256=hashlib.sha256(content).hexdigest(),
            observed_at="2026-08-31T08:00:00+00:00",
        ),
        content=content,
        risk_flags=risk_flags,
    )


def batch(cursor: str, next_cursor: str, *inputs: TopicObservationInput) -> TopicObservationBatch:
    return TopicObservationBatch("union-closed", cursor, next_cursor, tuple(inputs))


def manual_id_for(fields: dict[str, str]) -> str:
    return "manual-" + digest_json(
        {
            "schema_version": "1.0",
            **{
                key: fields[key]
                for key in ("topic_id", "cursor", "input_id", "reason", "detail")
            },
        }
    )[:24]


class TopicObservationTests(unittest.TestCase):
    def test_single_topic_batch_replays_after_restart_without_second_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first_runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            first = first_runner.run(batch("c0", "c1", input_for("A")))
            self.assertEqual(TopicRunStatus.APPLIED, first.status)
            self.assertEqual(TopicItemStatus.IMPORTED, first.item_results[0].status)
            restarted = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            replay = restarted.run(batch("c0", "c1", input_for("A")))
            self.assertEqual(TopicRunStatus.REPLAYED, replay.status)
            self.assertTrue(replay.replayed)
            self.assertEqual("c1", restarted.next_cursor)
            self.assertEqual(1, len(restarted.literature.observations))

    def test_cross_batch_duplicate_source_is_not_reimported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            original = input_for("A")
            runner.run(batch("c0", "c1", original))
            duplicate = TopicObservationInput("B", original.observation, original.content)
            result = runner.run(batch("c1", "c2", duplicate))
            self.assertEqual(TopicItemStatus.DUPLICATE, result.item_results[0].status)
            self.assertEqual(1, len(runner.literature.observations))

    def test_changed_logical_source_version_enters_manual_review_with_import_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            original = input_for("A")
            first = runner.run(batch("c0", "c1", original))
            self.assertEqual(TopicRunStatus.APPLIED, first.status)

            changed_content = b"revised source bytes"
            changed = TopicObservationInput(
                "B",
                new_observation(
                    observation_id="OBS-B",
                    canonical_uri=original.observation.canonical_uri,
                    pinned_version=original.observation.pinned_version,
                    license_status=LicenseStatus.OPEN,
                    license_basis="fixture license",
                    content_summary="Fixture bibliographic metadata.",
                    summary_basis="fixture",
                    media_type="text/plain",
                    content_digest_sha256=hashlib.sha256(changed_content).hexdigest(),
                    observed_at="2026-08-31T08:00:00+00:00",
                ),
                changed_content,
            )
            result = runner.run(batch("c1", "c2", changed))

            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)
            self.assertEqual(TopicItemStatus.MANUAL_REVIEW, result.item_results[0].status)
            self.assertEqual("c2", runner.next_cursor)
            self.assertEqual(1, len(runner.manual_queue))
            manual = runner.manual_queue[0]
            self.assertEqual(ManualReviewReason.LITERATURE_CONFLICT, manual.reason)
            self.assertEqual("B", manual.input_id)
            self.assertIn("same identity has a different digest", manual.detail)

    def test_rejected_observation_id_reuse_enters_manual_review_with_import_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            original = input_for("A")
            runner.run(batch("c0", "c1", original))
            changed_identity = TopicObservationInput(
                "B",
                new_observation(
                    observation_id=original.observation.observation_id,
                    canonical_uri="https://example.test/different-logical-source",
                    pinned_version="v1",
                    license_status=LicenseStatus.OPEN,
                    license_basis="fixture license",
                    content_summary="Fixture bibliographic metadata.",
                    summary_basis="fixture",
                    media_type="text/plain",
                    content_digest_sha256=hashlib.sha256(original.content).hexdigest(),
                    observed_at="2026-08-31T08:00:00+00:00",
                ),
                original.content,
            )

            result = runner.run(batch("c1", "c2", changed_identity))

            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)
            self.assertEqual(TopicItemStatus.MANUAL_REVIEW, result.item_results[0].status)
            self.assertEqual("c2", runner.next_cursor)
            self.assertEqual(1, len(runner.manual_queue))
            manual = runner.manual_queue[0]
            self.assertEqual(ManualReviewReason.LITERATURE_IMPORT_FAILURE, manual.reason)
            self.assertEqual("B", manual.input_id)
            self.assertIn("observation_id already names another logical identity", manual.detail)

    def test_budget_exhaustion_enters_manual_queue_without_import_or_status_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(
                directory, topic_id="union-closed", initial_cursor="c0",
                budget=BudgetLedger(cost_usd_limit=0.0),
            )
            result = runner.run(batch("c0", "c1", input_for("A")))
            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)
            self.assertEqual(TopicItemStatus.MANUAL_REVIEW, result.item_results[0].status)
            self.assertEqual(ManualReviewReason.BUDGET_EXHAUSTED, runner.manual_queue[0].reason)
            self.assertEqual(0, len(runner.literature.observations))
            self.assertFalse((Path(directory) / "claims.json").exists())
            self.assertFalse((Path(directory) / "research-trace.json").exists())

    def test_high_risk_event_enters_manual_queue_without_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            result = runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)
            self.assertEqual(ManualReviewReason.HIGH_RISK_EVENT, runner.manual_queue[0].reason)
            self.assertEqual(0, len(runner.literature.observations))

    def test_preexisting_observation_is_idempotent_and_replays(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            item = input_for("A")
            self.assertEqual(
                "IMPORTED",
                runner.literature.import_bytes(item.observation, item.content).disposition.value,
            )

            result = runner.run(batch("c0", "c1", item))

            self.assertEqual(TopicItemStatus.IDEMPOTENT, result.item_results[0].status)
            self.assertEqual(TopicRunStatus.APPLIED, result.status)
            replay = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").run(
                batch("c0", "c1", item)
            )
            self.assertEqual(TopicRunStatus.REPLAYED, replay.status)

    def test_restricted_observation_remains_pending_and_replays(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            content = b"restricted source bytes"
            item = TopicObservationInput(
                "A",
                new_observation(
                    observation_id="OBS-A",
                    canonical_uri="https://example.test/A",
                    pinned_version="v1",
                    license_status=LicenseStatus.RESTRICTED,
                    license_basis="fixture restriction",
                    content_summary="Fixture bibliographic metadata.",
                    summary_basis="fixture",
                    media_type="text/plain",
                    content_digest_sha256=hashlib.sha256(content).hexdigest(),
                    observed_at="2026-08-31T08:00:00+00:00",
                ),
                content,
            )
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")

            result = runner.run(batch("c0", "c1", item))

            self.assertEqual(TopicItemStatus.PENDING, result.item_results[0].status)
            self.assertEqual(TopicRunStatus.APPLIED, result.status)
            replay = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").run(
                batch("c0", "c1", item)
            )
            self.assertEqual(TopicRunStatus.REPLAYED, replay.status)

    def test_cursor_conflict_is_manual_and_does_not_advance_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            conflict = runner.run(batch("c0", "c1", input_for("B")))
            self.assertEqual(TopicRunStatus.CURSOR_BLOCKED, conflict.status)
            self.assertEqual(ManualReviewReason.CURSOR_CONFLICT, runner.manual_queue[0].reason)
            self.assertEqual("c1", runner.next_cursor)
            self.assertEqual(1, len(runner.literature.observations))

    def test_cursor_conflict_manual_entry_must_match_state_topic_after_id_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            runner.run(batch("c0", "c1", input_for("B")))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            manual = state["manual_queue"][0]
            old_manual_id = manual["manual_id"]
            manual["topic_id"] = "foreign-topic"
            manual["manual_id"] = manual_id_for(manual)
            state["manual_events"][0]["manual_id"] = manual["manual_id"]
            self.assertNotEqual(old_manual_id, manual["manual_id"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(ManualQueueObservationError, "cursor conflict"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_manual_queue_loader_binds_non_cursor_topic_to_enclosing_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            queue_item = state["manual_queue"][0]
            queue_item["topic_id"] = "foreign-topic"
            queue_item["manual_id"] = manual_id_for(queue_item)
            stored = state["batches"]["c0"]
            stored["result"]["item_results"][0]["manual_id"] = queue_item["manual_id"]
            stored["disposition_evidence"]["A"]["manual_id"] = queue_item["manual_id"]
            stored["result_digest_sha256"] = digest_json(stored["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(ManualQueueObservationError, "manual queue topic_id"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_malformed_manual_queue_entries_are_topic_observation_errors(self) -> None:
        mutations = {
            "missing field": lambda entry: entry.pop("detail"),
            "invalid reason": lambda entry: entry.update(reason="INVALID_MANUAL_REASON"),
        }
        for label, mutate in mutations.items():
            with self.subTest(queue_entry=label), tempfile.TemporaryDirectory() as directory:
                runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
                runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
                state_path = Path(directory) / "topic-observation-state.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                mutate(state["manual_queue"][0])
                state_path.write_text(json.dumps(state), encoding="utf-8")

                with self.assertRaises(TopicObservationError) as raised:
                    TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor
                self.assertIsInstance(raised.exception, ManualQueueObservationError)

    def test_tampered_stored_batch_result_digest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["batches"]["c0"]["result"]["status"] = "MANUAL_REVIEW"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "batch result digest"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_tampered_stored_batch_result_cross_fields_fail_closed(self) -> None:
        mutations = {
            "topic_id": lambda result: result.update(topic_id="other-topic"),
            "cursor": lambda result: result.update(cursor="other-cursor"),
            "next_cursor": lambda result: result.update(next_cursor="other-next-cursor"),
            "input_id": lambda result: result["item_results"][0].update(input_id="other-input"),
            "observation_id": lambda result: result["item_results"][0].update(observation_id="other-observation"),
        }
        for field, mutate in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
                runner.run(batch("c0", "c1", input_for("A")))
                state_path = Path(directory) / "topic-observation-state.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                stored = state["batches"]["c0"]
                mutate(stored["result"])
                stored["result_digest_sha256"] = digest_json(stored["result"])
                state_path.write_text(json.dumps(state), encoding="utf-8")

                with self.assertRaises(TopicObservationError):
                    TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_tampered_stored_manual_result_linkage_fails_closed_after_digest_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            result = runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["batches"]["c0"]
            item_result = stored["result"]["item_results"][0]
            original_manual_id = item_result["manual_id"]
            item_result["manual_id"] = "manual-replacement"
            self.assertNotEqual(original_manual_id, item_result["manual_id"])
            stored["result_digest_sha256"] = digest_json(stored["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "manual review result"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_tampered_stored_manual_result_missing_queue_fails_closed_after_digest_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            result = runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["batches"]["c0"]
            manual_id = stored["result"]["item_results"][0]["manual_id"]
            state["manual_queue"] = [
                manual for manual in state["manual_queue"] if manual["manual_id"] != manual_id
            ]
            self.assertEqual([], state["manual_queue"])
            stored["result_digest_sha256"] = digest_json(stored["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "manual review result"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_tampered_manual_queue_id_fails_closed_after_digest_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            result = runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["batches"]["c0"]
            queue_item = state["manual_queue"][0]
            queue_item["manual_id"] = "manual-tampered"
            stored["result_digest_sha256"] = digest_json(stored["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "manual queue manual_id"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_tampered_non_manual_result_with_manual_id_fails_closed_after_digest_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            result = runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["batches"]["c0"]
            stored["result"]["item_results"][0]["status"] = TopicItemStatus.IMPORTED.value
            stored["result_digest_sha256"] = digest_json(stored["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "non-manual result"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_tampered_stored_batch_status_fails_closed_after_digest_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            result = runner.run(batch("c0", "c1", input_for("A")))
            self.assertEqual(TopicRunStatus.APPLIED, result.status)

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["batches"]["c0"]
            stored["result"]["status"] = TopicRunStatus.MANUAL_REVIEW.value
            stored["result_digest_sha256"] = digest_json(stored["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "batch result status"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_imported_result_disposition_mutations_fail_closed_after_digest_recompute(self) -> None:
        for forged_status in (
            TopicItemStatus.IDEMPOTENT.value,
            TopicItemStatus.DUPLICATE.value,
            TopicItemStatus.PENDING.value,
        ):
            with self.subTest(forged_status=forged_status), tempfile.TemporaryDirectory() as directory:
                runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
                result = runner.run(batch("c0", "c1", input_for("A")))
                self.assertEqual(TopicItemStatus.IMPORTED, result.item_results[0].status)

                state_path = Path(directory) / "topic-observation-state.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                stored = state["batches"]["c0"]
                stored["result"]["item_results"][0]["status"] = forged_status
                stored["result_digest_sha256"] = digest_json(stored["result"])
                state_path.write_text(json.dumps(state), encoding="utf-8")

                with self.assertRaisesRegex(TopicObservationError, "disposition conflicts"):
                    TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_manual_result_cannot_become_imported_with_orphan_queue_after_digest_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            result = runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
            self.assertEqual(TopicRunStatus.MANUAL_REVIEW, result.status)

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["batches"]["c0"]
            item_result = stored["result"]["item_results"][0]
            item_result["status"] = TopicItemStatus.IMPORTED.value
            item_result["manual_id"] = None
            stored["result"]["status"] = TopicRunStatus.APPLIED.value
            stored["result_digest_sha256"] = digest_json(stored["result"])
            self.assertEqual(1, len(state["manual_queue"]))
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "disposition conflicts"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_valid_orphaned_manual_queue_entry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            orphan = dict(state["manual_queue"][0])
            orphan["detail"] += " independent orphan"
            orphan["manual_id"] = manual_id_for(orphan)
            state["manual_queue"].append(orphan)
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(ManualQueueObservationError, "orphaned entry"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_input_projection_rejects_cross_batch_observation_swap_after_digest_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            runner.run(batch("c1", "c2", input_for("B")))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored_a = state["batches"]["c0"]
            stored_b = state["batches"]["c1"]
            evidence_a = stored_a["disposition_evidence"]["A"]
            evidence_b = stored_b["disposition_evidence"]["B"]
            result_a = stored_a["result"]["item_results"][0]
            result_b = stored_b["result"]["item_results"][0]

            projection_a = stored_a["input_projections"]["A"]
            self.assertEqual("A", projection_a["input_id"])
            self.assertEqual(input_for("A").observation.to_dict(), projection_a["observation"])
            self.assertEqual(len(input_for("A").content), projection_a["content_size_bytes"])
            self.assertEqual(
                hashlib.sha256(input_for("A").content).hexdigest(),
                projection_a["content_sha256"],
            )
            self.assertEqual([], projection_a["risk_flags"])
            result_a["observation_id"] = result_b["observation_id"]
            stored_a["input_observation_ids"]["A"] = result_b["observation_id"]
            stored_a["input_fingerprints"]["A"] = stored_b["input_fingerprints"]["B"]
            for field in (
                "input_observation_id",
                "input_idempotency_key",
                "input_content_digest_sha256",
                "input_content_sha256",
                "input_content_size_bytes",
                "input_risk_flags",
                "observation_id",
                "persisted_observation_id",
                "persisted_observation_status",
                "persisted_content_digest_sha256",
                "persisted_artifact_id",
                "persisted_artifact_sha256",
                "import_disposition",
            ):
                evidence_a[field] = evidence_b[field]
            state["processed_input_ids"]["A"] = stored_b["input_fingerprints"]["B"]
            state["seen_observation_keys"] = [evidence_b["input_idempotency_key"]]
            stored_a["batch_digest_sha256"] = digest_json(
                {
                    "schema_version": "1.0",
                    "topic_id": "union-closed",
                    "cursor": "c0",
                    "next_cursor": "c1",
                    "inputs": [stored_a["input_fingerprints"]["A"]],
                }
            )
            stored_a["result_digest_sha256"] = digest_json(stored_a["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "projection|fingerprint"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_full_cross_batch_rewrite_cannot_reuse_a_successful_observation(self) -> None:
        """A rewritten state must not turn one observed source into two imports."""
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            runner.run(batch("c1", "c2", input_for("B")))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored_a = state["batches"]["c0"]
            stored_b = state["batches"]["c1"]
            source_b = input_for("B")
            swapped = TopicObservationInput("A", source_b.observation, source_b.content)

            # Rewrite every digest-bearing field for batch c0 to be internally
            # coherent with B. The cursor-ordered replay check must still reject
            # the second successful import of B's idempotency key.
            stored_a["input_projections"]["A"] = swapped.input_projection
            stored_a["input_fingerprints"]["A"] = swapped.fingerprint_sha256
            stored_a["input_observation_ids"]["A"] = source_b.observation.observation_id
            evidence = dict(stored_b["disposition_evidence"]["B"])
            evidence["input_id"] = "A"
            stored_a["disposition_evidence"]["A"] = evidence
            stored_a["result"]["item_results"][0]["observation_id"] = source_b.observation.observation_id
            state["processed_input_ids"]["A"] = swapped.fingerprint_sha256
            state["seen_observation_keys"] = [
                stored_b["disposition_evidence"]["B"]["input_idempotency_key"]
            ]
            stored_a["batch_digest_sha256"] = batch("c0", "c1", swapped).batch_digest_sha256
            stored_a["input_projection_digest_sha256"] = _input_projection_digest(
                topic_id="union-closed",
                cursor="c0",
                next_cursor="c1",
                batch_digest_sha256=stored_a["batch_digest_sha256"],
                input_projections=stored_a["input_projections"],
            )
            evidence["input_projection_binding_sha256"] = _input_projection_binding_digest(
                topic_id="union-closed",
                cursor="c0",
                next_cursor="c1",
                batch_digest_sha256=stored_a["batch_digest_sha256"],
                input_projection=swapped.input_projection,
            )
            stored_a["result_digest_sha256"] = digest_json(stored_a["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "successful import repeats"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_cross_batch_rewrite_cannot_hide_the_original_literature_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            runner.run(batch("c1", "c2", input_for("B")))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored_a = state["batches"]["c0"]
            stored_b = state["batches"]["c1"]
            source_b = input_for("B")
            swapped = TopicObservationInput("A", source_b.observation, source_b.content)

            stored_a["input_projections"]["A"] = swapped.input_projection
            stored_a["input_fingerprints"]["A"] = swapped.fingerprint_sha256
            stored_a["input_observation_ids"]["A"] = source_b.observation.observation_id
            evidence_a = dict(stored_b["disposition_evidence"]["B"])
            evidence_a["input_id"] = "A"
            stored_a["disposition_evidence"]["A"] = evidence_a
            stored_a["result"]["item_results"][0]["observation_id"] = source_b.observation.observation_id
            state["processed_input_ids"]["A"] = swapped.fingerprint_sha256
            state["seen_observation_keys"] = [evidence_a["input_idempotency_key"]]
            stored_a["batch_digest_sha256"] = batch("c0", "c1", swapped).batch_digest_sha256
            stored_a["input_projection_digest_sha256"] = _input_projection_digest(
                topic_id="union-closed",
                cursor="c0",
                next_cursor="c1",
                batch_digest_sha256=stored_a["batch_digest_sha256"],
                input_projections=stored_a["input_projections"],
            )
            evidence_a["input_projection_binding_sha256"] = _input_projection_binding_digest(
                topic_id="union-closed",
                cursor="c0",
                next_cursor="c1",
                batch_digest_sha256=stored_a["batch_digest_sha256"],
                input_projection=swapped.input_projection,
            )
            stored_a["result_digest_sha256"] = digest_json(stored_a["result"])

            stored_b["result"]["item_results"][0]["status"] = TopicItemStatus.DUPLICATE.value
            evidence_b = stored_b["disposition_evidence"]["B"]
            evidence_b["basis"] = "SEEN_OBSERVATION_KEY"
            evidence_b["import_disposition"] = None
            stored_b["result_digest_sha256"] = digest_json(stored_b["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "literature observations"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_disposition_evidence_rejects_cross_batch_projection_binding_swap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            runner.run(batch("c1", "c2", input_for("B")))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored_a = state["batches"]["c0"]
            stored_b = state["batches"]["c1"]
            binding_a = stored_a["disposition_evidence"]["A"]["input_projection_binding_sha256"]
            binding_b = stored_b["disposition_evidence"]["B"]["input_projection_binding_sha256"]
            self.assertNotEqual(binding_a, binding_b)
            stored_a["disposition_evidence"]["A"]["input_projection_binding_sha256"] = binding_b
            stored_a["result_digest_sha256"] = digest_json(stored_a["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "not bound to its batch input projection"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_input_projection_rejects_forged_high_risk_manual_result_and_reason(self) -> None:
        for forged_evidence_risk_flags in (True, False):
            with self.subTest(forged_evidence_risk_flags=forged_evidence_risk_flags), tempfile.TemporaryDirectory() as directory:
                runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
                runner.run(batch("c0", "c1", input_for("A")))

                state_path = Path(directory) / "topic-observation-state.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                stored = state["batches"]["c0"]
                item_result = stored["result"]["item_results"][0]
                evidence = stored["disposition_evidence"]["A"]
                self.assertEqual([], stored["input_projections"]["A"]["risk_flags"])
                detail = "High-risk flags require human review: forged-risk"
                manual_id = manual_id_for(
                    {
                        "topic_id": "union-closed",
                        "cursor": "c0",
                        "input_id": "A",
                        "reason": ManualReviewReason.HIGH_RISK_EVENT.value,
                        "detail": detail,
                    }
                )
                item_result.update(status=TopicItemStatus.MANUAL_REVIEW.value, manual_id=manual_id)
                stored["result"]["status"] = TopicRunStatus.MANUAL_REVIEW.value
                evidence.update(
                    basis="MANUAL_QUEUE",
                    manual_id=manual_id,
                    manual_reason=ManualReviewReason.HIGH_RISK_EVENT.value,
                    import_disposition=None,
                )
                if forged_evidence_risk_flags:
                    evidence["input_risk_flags"] = ["forged-risk"]
                state["manual_queue"].append(
                    {
                        "manual_id": manual_id,
                        "topic_id": "union-closed",
                        "cursor": "c0",
                        "input_id": "A",
                        "reason": ManualReviewReason.HIGH_RISK_EVENT.value,
                        "detail": detail,
                    }
                )
                state["manual_queue"].sort(key=lambda entry: entry["manual_id"])
                state["seen_observation_keys"] = []
                stored["result_digest_sha256"] = digest_json(stored["result"])
                state_path.write_text(json.dumps(state), encoding="utf-8")

                with self.assertRaisesRegex(TopicObservationError, "projection|risk|manual disposition"):
                    TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_input_projection_rejects_cross_batch_manual_reason_swap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(
                directory,
                topic_id="union-closed",
                initial_cursor="c0",
                budget=BudgetLedger(cost_usd_limit=0.0),
            )
            runner.run(batch("c0", "c1", input_for("A", risk_flags=("possible-resolution",))))
            runner.run(batch("c1", "c2", input_for("B")))

            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["batches"]["c0"]
            queue_item = next(item for item in state["manual_queue"] if item["cursor"] == "c0")
            budget_item = next(item for item in state["manual_queue"] if item["cursor"] == "c1")
            queue_item["reason"] = budget_item["reason"]
            queue_item["detail"] = budget_item["detail"]
            queue_item["manual_id"] = manual_id_for(queue_item)
            stored["result"]["item_results"][0]["manual_id"] = queue_item["manual_id"]
            stored["disposition_evidence"]["A"].update(
                manual_id=queue_item["manual_id"],
                manual_reason=queue_item["reason"],
            )
            stored["result_digest_sha256"] = digest_json(stored["result"])
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "budget manual disposition conflicts with input projection"):
                TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor

    def test_legacy_topic_state_requires_recovery_contract_and_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            state_path = Path(directory) / "topic-observation-state.json"
            current = json.loads(state_path.read_text(encoding="utf-8"))

            for legacy_version in ("1.0", "1.1", "1.2", "1.3"):
                with self.subTest(legacy_version=legacy_version):
                    legacy = dict(current)
                    legacy["schema_version"] = legacy_version
                    legacy_bytes = json.dumps(legacy).encode("utf-8")
                    state_path.write_bytes(legacy_bytes)

                    with self.assertRaisesRegex(
                        TopicObservationError,
                        f"schema_version '{legacy_version}'.*recovery contract",
                    ):
                        TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0").next_cursor
                    self.assertEqual(legacy_bytes, state_path.read_bytes())

    def test_fixture_declares_one_topic_cursor_and_non_claim_boundary(self) -> None:
        fixture = Path(__file__).parents[1] / "agents-results/2026-08-31/problem-intelligence-plane/evidence/t1-fixtures/one-topic-replay.json"
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual("t1-topic-observation-fixture", payload["fixture_kind"])
        self.assertEqual("union-closed", payload["topic_id"])
        self.assertNotEqual(payload["cursor"], payload["next_cursor"])
        self.assertIn("not", payload["non_claim_boundary"].lower())
