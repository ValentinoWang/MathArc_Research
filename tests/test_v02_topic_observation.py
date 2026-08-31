from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.budget import BudgetLedger
from matharc.v02.source_observation import LicenseStatus, new_observation
from matharc.v02.topic_observation import (
    ManualReviewReason,
    TopicItemStatus,
    TopicObservationBatch,
    TopicObservationInput,
    TopicObservationRunner,
    TopicRunStatus,
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

    def test_cursor_conflict_is_manual_and_does_not_advance_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="union-closed", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            conflict = runner.run(batch("c0", "c1", input_for("B")))
            self.assertEqual(TopicRunStatus.CURSOR_BLOCKED, conflict.status)
            self.assertEqual(ManualReviewReason.CURSOR_CONFLICT, runner.manual_queue[0].reason)
            self.assertEqual("c1", runner.next_cursor)
            self.assertEqual(1, len(runner.literature.observations))

    def test_fixture_declares_one_topic_cursor_and_non_claim_boundary(self) -> None:
        fixture = Path(__file__).parents[1] / "agents-results/2026-08-31/problem-intelligence-plane/evidence/t1-fixtures/one-topic-replay.json"
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual("t1-topic-observation-fixture", payload["fixture_kind"])
        self.assertEqual("union-closed", payload["topic_id"])
        self.assertNotEqual(payload["cursor"], payload["next_cursor"])
        self.assertIn("not", payload["non_claim_boundary"].lower())
