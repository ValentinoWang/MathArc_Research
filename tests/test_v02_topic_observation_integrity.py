from __future__ import annotations

import hashlib
import json
import stat
import tempfile
import unittest
from pathlib import Path
from typing import Any

from matharc.v02.schema import digest_json
from matharc.v02.source_observation import LicenseStatus, new_observation
from matharc.v02.topic_observation import (
    ManualReviewReason,
    TopicItemStatus,
    TopicObservationBatch,
    TopicObservationError,
    TopicObservationInput,
    TopicObservationRunner,
    _input_projection_binding_digest,
    _input_projection_digest,
)


def input_for(input_id: str, *, risk_flags: tuple[str, ...] = ()) -> TopicObservationInput:
    content = f"integrity source bytes for {input_id}".encode("utf-8")
    return TopicObservationInput(
        input_id=input_id,
        observation=new_observation(
            observation_id=f"OBS-{input_id}",
            canonical_uri=f"https://integrity.example/{input_id}",
            pinned_version="v1",
            license_status=LicenseStatus.OPEN,
            license_basis="integrity fixture license",
            content_summary="Descriptive integrity fixture metadata.",
            summary_basis="fixture",
            media_type="text/plain",
            content_digest_sha256=hashlib.sha256(content).hexdigest(),
            observed_at="2026-09-02T08:00:00+00:00",
        ),
        content=content,
        risk_flags=risk_flags,
    )


def batch(cursor: str, next_cursor: str, *inputs: TopicObservationInput) -> TopicObservationBatch:
    return TopicObservationBatch("integrity-topic", cursor, next_cursor, tuple(inputs))


class TopicObservationIntegrityTests(unittest.TestCase):
    def test_authentication_files_are_private_and_restartable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))

            self.assertEqual(32, len(runner.signing_key_path.read_bytes()))
            self.assertEqual(0o600, stat.S_IMODE(runner.signing_key_path.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(runner.authentication_path.stat().st_mode))
            authentication = json.loads(runner.authentication_path.read_text(encoding="utf-8"))
            self.assertEqual("1.5", authentication["state_schema_version"])
            self.assertEqual("c1", TopicObservationRunner(
                directory, topic_id="integrity-topic", initial_cursor="c0"
            ).next_cursor)

    def test_missing_malformed_and_replaced_authentication_fail_closed(self) -> None:
        for label in ("missing", "malformed", "replaced", "state_and_auth_missing"):
            with self.subTest(authentication=label), tempfile.TemporaryDirectory() as directory:
                runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
                runner.run(batch("c0", "c1", input_for("A")))
                state_path = Path(directory) / "topic-observation-state.json"
                state_bytes = state_path.read_bytes()
                authentication_path = runner.authentication_path
                authentication = json.loads(authentication_path.read_text(encoding="utf-8"))
                if label == "missing":
                    authentication_path.unlink()
                elif label == "malformed":
                    authentication_path.write_bytes(b"not-json\n")
                elif label == "replaced":
                    authentication_path.write_text(
                        json.dumps({**authentication, "mac_sha256": "0" * 64}),
                        encoding="utf-8",
                    )
                else:
                    state_path.unlink()
                    authentication_path.unlink()

                with self.assertRaisesRegex(TopicObservationError, "authentication"):
                    TopicObservationRunner(
                        directory, topic_id="integrity-topic", initial_cursor="c0"
                    ).next_cursor
                if label != "state_and_auth_missing":
                    self.assertEqual(state_bytes, state_path.read_bytes())

    def test_partial_preexisting_inventory_supports_incremental_existing_observed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
            item_a = input_for("A")
            item_b = input_for("B")
            self.assertEqual(
                "IMPORTED", runner.literature.import_bytes(item_a.observation, item_a.content).disposition.value
            )
            self.assertEqual(
                "IMPORTED", runner.literature.import_bytes(item_b.observation, item_b.content).disposition.value
            )

            first = runner.run(batch("c0", "c1", item_a))
            second_runner = TopicObservationRunner(
                directory, topic_id="integrity-topic", initial_cursor="c0"
            )
            second = second_runner.run(batch("c1", "c2", item_b))

            self.assertEqual(TopicItemStatus.IDEMPOTENT, first.item_results[0].status)
            self.assertEqual(TopicItemStatus.IDEMPOTENT, second.item_results[0].status)
            self.assertEqual("c2", second_runner.next_cursor)

    def test_snapshot_rejects_literature_changed_after_state_save(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            item_b = input_for("B")
            self.assertEqual(
                "IMPORTED", runner.literature.import_bytes(item_b.observation, item_b.content).disposition.value
            )

            with self.assertRaisesRegex(TopicObservationError, "literature snapshot"):
                TopicObservationRunner(
                    directory, topic_id="integrity-topic", initial_cursor="c0"
                ).next_cursor

    def test_coordinated_literature_replacement_fails_after_unkeyed_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            runner.run(batch("c1", "c2", input_for("B")))
            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self._rewrite_first_batch_to_b_and_second_to_duplicate(state)

            literature_path = Path(directory) / "literature" / "observations.json"
            literature = json.loads(literature_path.read_text(encoding="utf-8"))
            literature["observations"] = [
                item for item in literature["observations"] if item["observation_id"] == "OBS-B"
            ]
            literature_path.write_text(json.dumps(literature), encoding="utf-8")
            artifact_path = Path(directory) / "literature" / "artifacts" / "manifest.json"
            artifacts = json.loads(artifact_path.read_text(encoding="utf-8"))
            artifact_id = literature["observations"][0]["artifact_id"]
            artifacts["records"] = [
                item for item in artifacts["records"] if item["artifact_id"] == artifact_id
            ]
            artifact_path.write_text(json.dumps(artifacts), encoding="utf-8")

            replacement_runner = TopicObservationRunner(
                directory, topic_id="integrity-topic", initial_cursor="c0"
            )
            state["literature_snapshot_sha256"] = replacement_runner._literature_snapshot_sha256()
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "authentication"):
                replacement_runner.next_cursor

    def test_manual_reference_laundering_fails_after_unkeyed_recompute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            runner.run(batch("c1", "c2", input_for("B")))
            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self._rewrite_manual_reference_laundering(state)
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(TopicObservationError, "authentication"):
                TopicObservationRunner(
                    directory, topic_id="integrity-topic", initial_cursor="c0"
                ).next_cursor

    def test_legacy_v14_bytes_are_preserved_for_explicit_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            state_path = Path(directory) / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["schema_version"] = "1.4"
            legacy_bytes = json.dumps(state).encode("utf-8")
            state_path.write_bytes(legacy_bytes)

            with self.assertRaisesRegex(TopicObservationError, "schema_version '1.4'.*recovery contract"):
                TopicObservationRunner(
                    directory, topic_id="integrity-topic", initial_cursor="c0"
                ).next_cursor
            self.assertEqual(legacy_bytes, state_path.read_bytes())

    @staticmethod
    def _rewrite_first_batch_to_b_and_second_to_duplicate(state: dict[str, Any]) -> None:
        batches = state["batches"]
        assert isinstance(batches, dict)
        stored_a = batches["c0"]
        stored_b = batches["c1"]
        assert isinstance(stored_a, dict) and isinstance(stored_b, dict)
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
            topic_id="integrity-topic",
            cursor="c0",
            next_cursor="c1",
            batch_digest_sha256=stored_a["batch_digest_sha256"],
            input_projections=stored_a["input_projections"],
        )
        evidence_a["input_projection_binding_sha256"] = _input_projection_binding_digest(
            topic_id="integrity-topic",
            cursor="c0",
            next_cursor="c1",
            batch_digest_sha256=stored_a["batch_digest_sha256"],
            input_projection=swapped.input_projection,
        )
        stored_a["result_digest_sha256"] = digest_json(stored_a["result"])
        stored_b["result"]["item_results"][0]["status"] = TopicItemStatus.DUPLICATE.value
        stored_b["disposition_evidence"]["B"]["basis"] = "SEEN_OBSERVATION_KEY"
        stored_b["disposition_evidence"]["B"]["import_disposition"] = None
        stored_b["result_digest_sha256"] = digest_json(stored_b["result"])

    @staticmethod
    def _rewrite_manual_reference_laundering(state: dict[str, Any]) -> None:
        batches = state["batches"]
        assert isinstance(batches, dict)
        stored_a = batches["c0"]
        stored_b = batches["c1"]
        assert isinstance(stored_a, dict) and isinstance(stored_b, dict)
        original_a_evidence = dict(stored_a["disposition_evidence"]["A"])
        source_b = input_for("B", risk_flags=("forged-risk",))
        source_b_without_risk = input_for("B")
        swapped = TopicObservationInput(
            "A", source_b_without_risk.observation, source_b_without_risk.content
        )
        stored_a["input_projections"]["A"] = swapped.input_projection
        stored_a["input_fingerprints"]["A"] = swapped.fingerprint_sha256
        stored_a["input_observation_ids"]["A"] = "OBS-B"
        evidence_a = dict(stored_b["disposition_evidence"]["B"])
        evidence_a["input_id"] = "A"
        stored_a["disposition_evidence"]["A"] = evidence_a
        stored_a["result"]["item_results"][0]["observation_id"] = "OBS-B"
        state["processed_input_ids"]["A"] = swapped.fingerprint_sha256
        state["seen_observation_keys"] = [evidence_a["input_idempotency_key"]]
        stored_a["batch_digest_sha256"] = batch("c0", "c1", swapped).batch_digest_sha256
        stored_a["input_projection_digest_sha256"] = _input_projection_digest(
            topic_id="integrity-topic",
            cursor="c0",
            next_cursor="c1",
            batch_digest_sha256=stored_a["batch_digest_sha256"],
            input_projections=stored_a["input_projections"],
        )
        evidence_a["input_projection_binding_sha256"] = _input_projection_binding_digest(
            topic_id="integrity-topic",
            cursor="c0",
            next_cursor="c1",
            batch_digest_sha256=stored_a["batch_digest_sha256"],
            input_projection=swapped.input_projection,
        )
        stored_a["result_digest_sha256"] = digest_json(stored_a["result"])

        original_a = input_for("A")
        detail = "High-risk flags require human review: forged-risk"
        manual_id = "manual-" + hashlib.sha256(
            "|".join(
                (
                    "integrity-topic",
                    "c1",
                    "B",
                    ManualReviewReason.HIGH_RISK_EVENT.value,
                    detail,
                )
            ).encode("utf-8")
        ).hexdigest()[:24]
        state["manual_queue"] = [{
            "manual_id": manual_id,
            "topic_id": "integrity-topic",
            "cursor": "c1",
            "input_id": "B",
            "reason": ManualReviewReason.HIGH_RISK_EVENT.value,
            "detail": detail,
        }]
        stored_b["input_projections"]["B"] = source_b.input_projection
        stored_b["input_fingerprints"]["B"] = source_b.fingerprint_sha256
        state["processed_input_ids"]["B"] = source_b.fingerprint_sha256
        evidence_b = stored_b["disposition_evidence"]["B"]
        evidence_b.update(
            basis="MANUAL_QUEUE",
            input_risk_flags=["forged-risk"],
            persisted_observation_id="OBS-A",
            persisted_observation_status="OBSERVED",
            persisted_content_digest_sha256=original_a.observation.content_digest_sha256,
            persisted_artifact_id=original_a_evidence["persisted_artifact_id"],
            persisted_artifact_sha256=original_a_evidence["persisted_artifact_sha256"],
            manual_id=manual_id,
            manual_reason=ManualReviewReason.HIGH_RISK_EVENT.value,
            import_disposition=None,
        )
        stored_b["result"]["item_results"][0].update(
            status=TopicItemStatus.MANUAL_REVIEW.value,
            observation_id="OBS-B",
            manual_id=manual_id,
        )
        stored_b["batch_digest_sha256"] = batch("c1", "c2", source_b).batch_digest_sha256
        stored_b["input_projection_digest_sha256"] = _input_projection_digest(
            topic_id="integrity-topic",
            cursor="c1",
            next_cursor="c2",
            batch_digest_sha256=stored_b["batch_digest_sha256"],
            input_projections=stored_b["input_projections"],
        )
        evidence_b["input_projection_binding_sha256"] = _input_projection_binding_digest(
            topic_id="integrity-topic",
            cursor="c1",
            next_cursor="c2",
            batch_digest_sha256=stored_b["batch_digest_sha256"],
            input_projection=source_b.input_projection,
        )
        stored_b["result"]["status"] = "MANUAL_REVIEW"
        stored_b["result_digest_sha256"] = digest_json(stored_b["result"])


if __name__ == "__main__":
    unittest.main()
