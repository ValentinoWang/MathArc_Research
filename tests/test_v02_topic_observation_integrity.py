from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import threading
import unittest
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest.mock import patch

import matharc.v02.topic_observation as topic_observation_module
from matharc.v02.budget import BudgetLedger
from matharc.v02.literature_base import LiteratureBase
from matharc.v02.schema import digest_json
from matharc.v02.source_observation import (
    LicenseStatus,
    ObservationStatus,
    SourceObservation,
    new_observation,
)
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
    def test_absent_nested_runner_root_fsyncs_each_component_before_storage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / "runner" / "nested"
            fsynced: list[Path] = []
            original_fsync_directory = topic_observation_module._fsync_directory

            def record_fsync(path: Path) -> None:
                fsynced.append(path)
                self.assertFalse((root / "literature").exists())
                self.assertFalse((root / ".topic-observation.lock").exists())
                original_fsync_directory(path)

            with patch.object(
                topic_observation_module,
                "_fsync_directory",
                side_effect=record_fsync,
            ):
                TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )

            self.assertEqual([base, base / "runner"], fsynced)
            self.assertTrue(root.is_dir())

    def test_absent_nested_runner_root_fsync_failure_stops_initialization(self) -> None:
        original_fsync_directory = topic_observation_module._fsync_directory

        for failure_index in range(2):
            with self.subTest(failure_index=failure_index), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                root = base / "runner" / "nested"
                fsynced: list[Path] = []

                def fail_at_selected_parent(path: Path) -> None:
                    fsynced.append(path)
                    if len(fsynced) == failure_index + 1:
                        raise OSError("simulated runner-root parent fsync failure")
                    original_fsync_directory(path)

                with patch.object(
                    topic_observation_module,
                    "_fsync_directory",
                    side_effect=fail_at_selected_parent,
                ):
                    with self.assertRaisesRegex(
                        OSError,
                        "runner-root parent fsync failure",
                    ):
                        TopicObservationRunner(
                            root,
                            topic_id="integrity-topic",
                            initial_cursor="c0",
                        )

                self.assertEqual(failure_index + 1, len(fsynced))
                self.assertFalse((root / "literature").exists())
                self.assertFalse((root / ".topic-observation.lock").exists())

    def test_authentication_files_are_private_and_restartable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))

            self.assertEqual(32, len(runner.signing_key_path.read_bytes()))
            self.assertEqual(0o600, stat.S_IMODE(runner.signing_key_path.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(runner.authentication_path.stat().st_mode))
            authentication = json.loads(runner.authentication_path.read_text(encoding="utf-8"))
            self.assertEqual("1.8", authentication["state_schema_version"])
            self.assertEqual("c1", TopicObservationRunner(
                directory, topic_id="integrity-topic", initial_cursor="c0"
            ).next_cursor)

    def test_restored_prior_data_tuple_cannot_rollback_without_new_signing_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            old_paths = (
                runner.state_path,
                runner.authentication_path,
                root / "literature" / "observations.json",
                root / "literature" / "artifacts" / "manifest.json",
            )
            old_bytes = {path: path.read_bytes() for path in old_paths}
            old_key = runner.signing_key_path.read_bytes()

            runner.run(batch("c1", "c2", input_for("B")))
            self.assertNotEqual(old_key, runner.signing_key_path.read_bytes())
            self.assertEqual("c2", TopicObservationRunner(
                root, topic_id="integrity-topic", initial_cursor="c0"
            ).next_cursor)

            for path, content in old_bytes.items():
                path.write_bytes(content)

            with self.assertRaisesRegex(TopicObservationError, "authentication MAC"):
                TopicObservationRunner(
                    root, topic_id="integrity-topic", initial_cursor="c0"
                ).next_cursor

    def test_interrupted_literature_persistence_recovers_first_and_later_generation(self) -> None:
        for has_prior_generation in (False, True):
            with self.subTest(has_prior_generation=has_prior_generation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                runner = TopicObservationRunner(
                    root, topic_id="integrity-topic", initial_cursor="c0"
                )
                if has_prior_generation:
                    runner.run(batch("c0", "c1", input_for("A")))
                    interrupted_batch = batch("c1", "c2", input_for("B"))
                    expected_cursor = "c1"
                    expected_observations = ["OBS-A"]
                else:
                    interrupted_batch = batch("c0", "c1", input_for("A"))
                    expected_cursor = "c0"
                    expected_observations = []

                def interrupt(_state: Mapping[str, Any]) -> None:
                    raise RuntimeError("simulated interruption after literature persistence")

                runner._save_state = interrupt
                with self.assertRaisesRegex(RuntimeError, "after literature persistence"):
                    runner.run(interrupted_batch)
                self.assertTrue((root / ".topic-observation-transaction.json").exists())

                recovered = TopicObservationRunner(
                    root, topic_id="integrity-topic", initial_cursor="c0"
                )
                self.assertEqual(expected_cursor, recovered.next_cursor)
                self.assertEqual(
                    expected_observations,
                    [item.observation_id for item in recovered.literature.observations],
                )
                self.assertFalse((root / ".topic-observation-transaction.json").exists())

                if has_prior_generation:
                    completed = recovered.run(batch("c1", "c2", input_for("B")))
                else:
                    completed = recovered.run(batch("c0", "c1", input_for("A")))
                self.assertEqual("c2" if has_prior_generation else "c1", completed.next_cursor)

    def test_crash_blocks_concurrent_literature_writer_until_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            save_reached = threading.Event()
            release_save = threading.Event()
            writer_started = threading.Event()
            writer_done = threading.Event()
            runner_errors: list[BaseException] = []
            writer_results: list[Any] = []

            def interrupt_save(_state: Mapping[str, Any]) -> None:
                save_reached.set()
                if not release_save.wait(timeout=5):
                    raise RuntimeError("test did not release interrupted save")
                raise RuntimeError("simulated crash before topic state commit")

            def run_topic_transaction() -> None:
                try:
                    runner.run(batch("c0", "c1", input_for("A")))
                except BaseException as exc:
                    runner_errors.append(exc)

            external_input = input_for("EXTERNAL")

            def run_external_writer() -> None:
                writer_started.set()
                writer_results.append(
                    LiteratureBase(root / "literature").import_bytes(
                        external_input.observation,
                        external_input.content,
                    )
                )
                writer_done.set()

            runner._save_state = interrupt_save
            runner_thread = threading.Thread(target=run_topic_transaction)
            runner_thread.start()
            self.assertTrue(save_reached.wait(timeout=5))

            writer_thread = threading.Thread(target=run_external_writer)
            writer_thread.start()
            self.assertTrue(writer_started.wait(timeout=5))
            self.assertFalse(writer_done.wait(timeout=0.2))

            release_save.set()
            runner_thread.join(timeout=5)
            writer_thread.join(timeout=5)
            self.assertFalse(runner_thread.is_alive())
            self.assertFalse(writer_thread.is_alive())
            self.assertEqual(1, len(runner_errors))
            self.assertRegex(str(runner_errors[0]), "simulated crash")
            self.assertEqual(1, len(writer_results))
            self.assertEqual("REJECTED", writer_results[0].disposition.value)
            self.assertEqual(
                "topic observation transaction recovery is pending",
                writer_results[0].reason,
            )

            recovered = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual("c0", recovered.next_cursor)
            retry = LiteratureBase(root / "literature").import_bytes(
                external_input.observation,
                external_input.content,
            )
            self.assertEqual("IMPORTED", retry.disposition.value)
            restarted = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual(
                ["OBS-EXTERNAL"],
                [item.observation_id for item in restarted.literature.observations],
            )
            self.assertFalse((root / ".topic-observation-transaction.json").exists())

    def test_literature_alias_cannot_bypass_transaction_fences(self) -> None:
        for marker_name in (
            ".topic-observation-transaction.json",
            ".topic-observation-transaction.retiring.json",
        ):
            with self.subTest(marker_name=marker_name), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                topic_root = base / "topic"
                literature_root = topic_root / "literature"
                literature_root.mkdir(parents=True)
                alias = base / "literature-alias"
                alias.symlink_to(literature_root, target_is_directory=True)
                (topic_root / marker_name).write_text("{}\n", encoding="utf-8")

                external = input_for("EXTERNAL")
                blocked = LiteratureBase(alias).import_bytes(
                    external.observation,
                    external.content,
                )
                self.assertEqual("REJECTED", blocked.disposition.value)
                self.assertEqual(
                    "topic observation transaction recovery is pending",
                    blocked.reason,
                )

                (topic_root / marker_name).unlink()
                accepted = LiteratureBase(alias).import_bytes(
                    external.observation,
                    external.content,
                )
                self.assertEqual("IMPORTED", accepted.disposition.value)

    def test_interrupted_between_state_and_authentication_reverts_to_one_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            original_atomic_write = topic_observation_module._atomic_write_bytes

            def interrupt_authentication(path: Path, content: bytes, mode: int) -> None:
                if path == runner.authentication_path:
                    raise RuntimeError("simulated interruption between state and authentication")
                original_atomic_write(path, content, mode)

            with patch.object(
                topic_observation_module,
                "_atomic_write_bytes",
                side_effect=interrupt_authentication,
            ):
                with self.assertRaisesRegex(RuntimeError, "between state and authentication"):
                    runner.run(batch("c1", "c2", input_for("B")))

            recovered = TopicObservationRunner(
                root, topic_id="integrity-topic", initial_cursor="c0"
            )
            self.assertEqual("c1", recovered.next_cursor)
            self.assertEqual(["OBS-A"], [item.observation_id for item in recovered.literature.observations])
            self.assertFalse((root / ".topic-observation-transaction.json").exists())
            self.assertEqual("c2", recovered.run(batch("c1", "c2", input_for("B"))).next_cursor)

    def test_initial_commit_without_signing_authority_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            original_atomic_write = topic_observation_module._atomic_write_bytes

            def interrupt_key(path: Path, content: bytes, mode: int) -> None:
                if path == runner.signing_key_path:
                    raise RuntimeError("simulated interruption before initial signing authority")
                original_atomic_write(path, content, mode)

            with patch.object(
                topic_observation_module,
                "_atomic_write_bytes",
                side_effect=interrupt_key,
            ):
                with self.assertRaisesRegex(RuntimeError, "initial signing authority"):
                    runner.run(batch("c0", "c1", input_for("A")))

            with self.assertRaisesRegex(TopicObservationError, "no signing authority"):
                TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )
            self.assertTrue(runner.transaction_path.exists())
            external = input_for("EXTERNAL")
            blocked = LiteratureBase(root / "literature").import_bytes(
                external.observation,
                external.content,
            )
            self.assertEqual("REJECTED", blocked.disposition.value)

    def test_committed_signing_authority_rolls_forward_after_verification_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            with patch.object(
                runner,
                "_verify_state_authentication",
                side_effect=RuntimeError("simulated crash after signing authority commit"),
            ):
                with self.assertRaisesRegex(RuntimeError, "after signing authority commit"):
                    runner.run(batch("c0", "c1", input_for("A")))

            recovered = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual("c1", recovered.next_cursor)
            self.assertEqual(
                ["OBS-A"],
                [item.observation_id for item in recovered.literature.observations],
            )
            self.assertFalse(runner.transaction_path.exists())

    def test_initial_commit_intent_missing_entire_authority_tuple_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            with patch.object(
                runner,
                "_verify_state_authentication",
                side_effect=RuntimeError("simulated crash after initial authority commit"),
            ):
                with self.assertRaisesRegex(RuntimeError, "initial authority commit"):
                    runner.run(batch("c0", "c1", input_for("A")))

            for path in (
                runner.signing_key_path,
                runner.state_path,
                runner.authentication_path,
            ):
                path.unlink()

            with self.assertRaisesRegex(TopicObservationError, "no signing authority"):
                TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )
            self.assertTrue(runner.transaction_path.exists())
            external = input_for("EXTERNAL")
            blocked = LiteratureBase(root / "literature").import_bytes(
                external.observation,
                external.content,
            )
            self.assertEqual("REJECTED", blocked.disposition.value)

    def test_retirement_fsync_failure_keeps_external_writer_fenced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            original_fsync_directory = topic_observation_module._fsync_directory
            failed = False

            def fail_retirement_once(path: Path) -> None:
                nonlocal failed
                if (
                    not failed
                    and path == runner.root
                    and runner.retired_transaction_path.exists()
                    and not runner.transaction_path.exists()
                ):
                    failed = True
                    raise OSError("simulated retirement fsync failure")
                original_fsync_directory(path)

            with patch.object(
                topic_observation_module,
                "_fsync_directory",
                side_effect=fail_retirement_once,
            ):
                with self.assertRaisesRegex(TopicObservationError, "durably retire"):
                    runner.run(batch("c0", "c1", input_for("A")))

            self.assertTrue(failed)
            self.assertTrue(runner.retired_transaction_path.exists())
            external = input_for("EXTERNAL")
            blocked = LiteratureBase(root / "literature").import_bytes(
                external.observation,
                external.content,
            )
            self.assertEqual("REJECTED", blocked.disposition.value)

            recovered = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual("c1", recovered.next_cursor)
            self.assertFalse(runner.retired_transaction_path.exists())

    def test_recovery_fsyncs_each_deleted_literature_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))

            def interrupt(_state: Mapping[str, Any]) -> None:
                raise RuntimeError("simulated interruption after literature persistence")

            runner._save_state = interrupt
            with self.assertRaisesRegex(RuntimeError, "after literature persistence"):
                runner.run(batch("c1", "c2", input_for("B")))
            shutil.rmtree(root / "literature")

            original_fsync_directory = topic_observation_module._fsync_directory
            fsynced_directories: list[Path] = []

            def record_fsync(path: Path) -> None:
                fsynced_directories.append(path)
                original_fsync_directory(path)

            with patch.object(
                topic_observation_module,
                "_fsync_directory",
                side_effect=record_fsync,
            ):
                TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )

            self.assertTrue(
                {
                    runner.root,
                    runner.root / "literature",
                    runner.root / "literature" / "artifacts",
                    runner.root / "literature" / "artifacts" / "sha256",
                }.issubset(set(fsynced_directories))
            )

    def test_candidate_state_is_rejected_before_self_invalidating_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            runner.run(batch("c0", "c1", input_for("A")))
            old_state = runner.state_path.read_bytes()
            old_authentication = runner.authentication_path.read_bytes()
            runner._active_transaction = runner._begin_transaction()
            try:
                invalid = runner._load_state()
                invalid["next_cursor"] = "not-the-cursor-chain"
                with self.assertRaisesRegex(TopicObservationError, "cursor chain"):
                    runner._save_state(invalid)
            finally:
                runner._active_transaction = None

            self.assertEqual(old_state, runner.state_path.read_bytes())
            self.assertEqual(old_authentication, runner.authentication_path.read_bytes())

    def test_retired_marker_normal_restore_failure_uses_fallback_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            original_fsync_directory = topic_observation_module._fsync_directory
            original_atomic_write = topic_observation_module._atomic_write_bytes
            failed_unlink_fsync = False

            def fail_unlink_fsync_once(path: Path) -> None:
                nonlocal failed_unlink_fsync
                if (
                    not failed_unlink_fsync
                    and path == runner.root
                    and not runner.retired_transaction_path.exists()
                    and not runner.transaction_path.exists()
                ):
                    failed_unlink_fsync = True
                    raise OSError("simulated retired unlink fsync failure")
                original_fsync_directory(path)

            def fail_normal_restore(path: Path, content: bytes, mode: int) -> None:
                if path == runner.retired_transaction_path:
                    raise OSError("simulated normal marker restore failure")
                original_atomic_write(path, content, mode)

            with (
                patch.object(
                    topic_observation_module,
                    "_fsync_directory",
                    side_effect=fail_unlink_fsync_once,
                ),
                patch.object(
                    topic_observation_module,
                    "_atomic_write_bytes",
                    side_effect=fail_normal_restore,
                ),
            ):
                with self.assertRaisesRegex(TopicObservationError, "normally restore"):
                    runner.run(batch("c0", "c1", input_for("A")))

            self.assertTrue(failed_unlink_fsync)
            self.assertTrue(runner.retired_transaction_path.exists())
            external = input_for("EXTERNAL")
            blocked = LiteratureBase(root / "literature").import_bytes(
                external.observation,
                external.content,
            )
            self.assertEqual("REJECTED", blocked.disposition.value)

    def test_topic_and_literature_lock_symlinks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            topic_lock_backing = root / "topic-lock.backing"
            topic_lock_backing.touch()
            runner.lock_path.unlink()
            runner.lock_path.symlink_to(topic_lock_backing.name)
            with self.assertRaisesRegex(TopicObservationError, "lock is unreadable"):
                TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = LiteratureBase(root)
            literature_lock_backing = root / "literature-lock.backing"
            literature_lock_backing.touch()
            base.lock_path.symlink_to(literature_lock_backing.name)
            with self.assertRaisesRegex(ValueError, "lock is unreadable"):
                base.import_bytes(input_for("A").observation, input_for("A").content)

    def test_long_lived_runner_reloads_literature_before_public_state_reads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            owner.run(batch("c0", "c1", input_for("A")))
            stale = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            item_b = input_for("B")
            self.assertEqual(
                "IMPORTED",
                LiteratureBase(root / "literature").import_bytes(
                    item_b.observation, item_b.content
                ).disposition.value,
            )

            with self.assertRaisesRegex(TopicObservationError, "literature snapshot"):
                stale.next_cursor
            with self.assertRaisesRegex(TopicObservationError, "literature snapshot"):
                stale.manual_queue

    def test_existing_observed_accepts_recorded_id_and_replays_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_item = input_for("A")
            recorded_observation = SourceObservation.from_dict(
                {**input_item.observation.to_dict(), "observation_id": "OBS-RECORDED"}
            )
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            self.assertEqual(
                "IMPORTED",
                runner.literature.import_bytes(
                    recorded_observation, input_item.content
                ).disposition.value,
            )

            result = runner.run(batch("c0", "c1", input_item))
            self.assertEqual(TopicItemStatus.IDEMPOTENT, result.item_results[0].status)
            self.assertEqual("OBS-RECORDED", result.item_results[0].observation_id)

            restarted = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            replay = restarted.run(batch("c0", "c1", input_item))
            self.assertTrue(replay.replayed)
            self.assertEqual("OBS-RECORDED", replay.item_results[0].observation_id)
            self.assertEqual("c1", restarted.next_cursor)

    def test_alternate_persisted_id_remains_stable_across_duplicate_paths(self) -> None:
        for replay_kind in ("processed-input", "seen-key"):
            with self.subTest(replay_kind=replay_kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                original = input_for("A")
                recorded = SourceObservation.from_dict(
                    {**original.observation.to_dict(), "observation_id": "OBS-RECORDED"}
                )
                runner = TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )
                self.assertEqual(
                    "IMPORTED",
                    runner.literature.import_bytes(recorded, original.content).disposition.value,
                )
                first = runner.run(batch("c0", "c1", original))
                self.assertEqual("OBS-RECORDED", first.item_results[0].observation_id)

                if replay_kind == "processed-input":
                    duplicate_input = original
                else:
                    duplicate_input = TopicObservationInput(
                        "B",
                        SourceObservation.from_dict(
                            {
                                **original.observation.to_dict(),
                                "observation_id": "OBS-INCOMING-ALTERNATE",
                            }
                        ),
                        original.content,
                    )
                duplicate = runner.run(batch("c1", "c2", duplicate_input))
                self.assertEqual(TopicItemStatus.DUPLICATE, duplicate.item_results[0].status)
                self.assertEqual("OBS-RECORDED", duplicate.item_results[0].observation_id)

                restarted = TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )
                self.assertEqual("c2", restarted.next_cursor)

    def test_alternate_persisted_id_remains_stable_when_budget_is_exhausted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = input_for("A")
            recorded = SourceObservation.from_dict(
                {**original.observation.to_dict(), "observation_id": "OBS-RECORDED"}
            )
            runner = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual(
                "IMPORTED",
                runner.literature.import_bytes(recorded, original.content).disposition.value,
            )

            exhausted = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
                budget=BudgetLedger(cost_usd_limit=0.0),
            )
            result = exhausted.run(batch("c0", "c1", original))

            self.assertEqual(TopicItemStatus.MANUAL_REVIEW, result.item_results[0].status)
            self.assertEqual("OBS-RECORDED", result.item_results[0].observation_id)
            self.assertEqual("c1", exhausted.next_cursor)
            self.assertEqual(
                "c1",
                TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                    budget=BudgetLedger(cost_usd_limit=0.0),
                ).next_cursor,
            )

    def test_persisted_observation_id_and_key_cross_match_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(
                directory,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            item_a = input_for("A")
            item_b = input_for("B")
            self.assertEqual(
                "IMPORTED",
                runner.literature.import_bytes(item_a.observation, item_a.content).disposition.value,
            )
            self.assertEqual(
                "IMPORTED",
                runner.literature.import_bytes(item_b.observation, item_b.content).disposition.value,
            )
            crossed = TopicObservationInput(
                "CROSSED",
                SourceObservation.from_dict(
                    {
                        **item_b.observation.to_dict(),
                        "observation_id": item_a.observation.observation_id,
                    }
                ),
                item_b.content,
            )

            with self.assertRaisesRegex(
                TopicObservationError,
                "persisted observation id and idempotency key identify different records",
            ):
                runner.run(batch("c0", "c1", crossed))

    def test_cursor_conflict_survives_later_progress_and_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(
                directory,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            conflict = runner.run(batch("c1", "c2", input_for("EARLY")))
            self.assertEqual("CURSOR_BLOCKED", conflict.status.value)
            self.assertEqual(
                "Expected cursor 'c0', received 'c1'.",
                runner.manual_queue[0].detail,
            )

            self.assertEqual("APPLIED", runner.run(batch("c0", "c1", input_for("A"))).status.value)
            self.assertEqual("APPLIED", runner.run(batch("c1", "c2", input_for("B"))).status.value)

            restarted = TopicObservationRunner(
                directory,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual("c2", restarted.next_cursor)
            self.assertEqual(
                "Expected cursor 'c0', received 'c1'.",
                restarted.manual_queue[0].detail,
            )

    def test_historical_pending_upgrade_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b"pending upgrade source"
            pending = TopicObservationInput(
                "A",
                new_observation(
                    observation_id="OBS-A",
                    canonical_uri="https://integrity.example/pending-upgrade",
                    pinned_version="v1",
                    license_status=LicenseStatus.RESTRICTED,
                    license_basis="restricted fixture",
                    content_summary="Descriptive pending upgrade fixture.",
                    summary_basis="fixture",
                    media_type="text/plain",
                    content_digest_sha256=hashlib.sha256(content).hexdigest(),
                    observed_at="2026-09-02T08:00:00+00:00",
                ),
                content,
            )
            observed = TopicObservationInput(
                "B",
                SourceObservation.from_dict(
                    {
                        **pending.observation.to_dict(),
                        "license_status": LicenseStatus.OPEN.value,
                        "license_basis": "open fixture",
                    }
                ),
                content,
            )
            runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")

            first = runner.run(batch("c0", "c1", pending))
            second = runner.run(batch("c1", "c2", observed))

            self.assertEqual(TopicItemStatus.PENDING, first.item_results[0].status)
            self.assertEqual(TopicItemStatus.IMPORTED, second.item_results[0].status)
            restarted = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
            self.assertEqual("c2", restarted.next_cursor)
            stored = json.loads(restarted.state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                "PENDING",
                stored["batches"]["c0"]["disposition_evidence"]["A"][
                    "persisted_observation_status"
                ],
            )
            self.assertEqual("OBSERVED", restarted.literature.observations[0].status.value)

    def test_pre_import_budget_upgrade_and_processed_replay_survive_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b"pre-import budget replay source"
            digest = hashlib.sha256(content).hexdigest()
            pending_observation = new_observation(
                observation_id="OBS-PRE",
                canonical_uri="https://integrity.example/pre-import-budget",
                pinned_version="v1",
                license_status=LicenseStatus.RESTRICTED,
                license_basis="restricted fixture",
                content_summary="Descriptive pre-import budget fixture.",
                summary_basis="fixture",
                media_type="text/plain",
                content_digest_sha256=digest,
                observed_at="2026-09-02T08:00:00+00:00",
            )
            open_observation = SourceObservation.from_dict(
                {
                    **pending_observation.to_dict(),
                    "license_status": LicenseStatus.OPEN.value,
                    "license_basis": "open fixture",
                }
            )
            pending_input = TopicObservationInput("A", pending_observation, content)
            open_input = TopicObservationInput("B", open_observation, content)

            seed = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual(
                "PENDING",
                seed.literature.import_bytes(pending_observation, content).disposition.value,
            )

            exhausted = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
                budget=BudgetLedger(cost_usd_limit=0.0),
            )
            first = exhausted.run(batch("c0", "c1", pending_input))
            self.assertEqual(TopicItemStatus.MANUAL_REVIEW, first.item_results[0].status)
            first_evidence = json.loads(exhausted.state_path.read_text(encoding="utf-8"))["batches"]["c0"][
                "disposition_evidence"
            ]["A"]
            self.assertEqual("MANUAL_QUEUE", first_evidence["basis"])
            self.assertEqual("BUDGET_EXHAUSTED", first_evidence["manual_reason"])
            self.assertEqual("PENDING", first_evidence["persisted_observation_status"])
            self.assertIsNone(first_evidence["import_disposition"])

            restarted_before_upgrade = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
                budget=BudgetLedger(cost_usd_limit=0.0),
            )
            self.assertEqual("c1", restarted_before_upgrade.next_cursor)

            upgrader = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            second = upgrader.run(batch("c1", "c2", open_input))
            self.assertEqual(TopicItemStatus.IMPORTED, second.item_results[0].status)
            self.assertEqual("OBS-PRE", second.item_results[0].observation_id)
            self.assertEqual("OBSERVED", upgrader.literature.observations[0].status.value)
            self.assertTrue(upgrader.literature.artifacts.verify()["valid"])

            replay = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            ).run(batch("c2", "c3", pending_input))
            self.assertEqual(TopicItemStatus.DUPLICATE, replay.item_results[0].status)
            self.assertEqual("OBS-PRE", replay.item_results[0].observation_id)
            self.assertFalse((root / ".topic-observation-transaction.json").exists())
            self.assertFalse((root / ".topic-observation-transaction.retiring.json").exists())

            stored = json.loads(
                (root / "topic-observation-state.json").read_text(encoding="utf-8")
            )
            replay_evidence = stored["batches"]["c2"]["disposition_evidence"]["A"]
            self.assertEqual("PROCESSED_INPUT_REPLAY", replay_evidence["basis"])
            self.assertEqual("PENDING", replay_evidence["persisted_observation_status"])
            self.assertIsNone(replay_evidence["import_disposition"])
            self.assertIsNone(replay_evidence["persisted_artifact_id"])
            self.assertIsNone(replay_evidence["persisted_artifact_sha256"])

            restarted_after_replay = TopicObservationRunner(
                root,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            self.assertEqual("c3", restarted_after_replay.next_cursor)

    def test_pending_upgrade_rejects_identity_digest_and_cursor_variants(self) -> None:
        content = b"pending upgrade negative fixture"
        digest = hashlib.sha256(content).hexdigest()
        changed_content = b"pending upgrade changed digest"
        changed_digest = hashlib.sha256(changed_content).hexdigest()
        restricted_observation = new_observation(
            observation_id="OBS-NEGATIVE",
            canonical_uri="https://integrity.example/pending-negative",
            pinned_version="v1",
            license_status=LicenseStatus.RESTRICTED,
            license_basis="restricted fixture",
            content_summary="Descriptive negative upgrade fixture.",
            summary_basis="fixture",
            media_type="text/plain",
            content_digest_sha256=digest,
            observed_at="2026-09-02T08:00:00+00:00",
        )
        open_observation = SourceObservation.from_dict(
            {
                **restricted_observation.to_dict(),
                "license_status": LicenseStatus.OPEN.value,
                "license_basis": "open fixture",
            }
        )
        identity_variant = SourceObservation.from_dict(
            {
                **open_observation.to_dict(),
                "canonical_uri": "https://integrity.example/pending-negative-other",
            }
        )
        digest_variant = SourceObservation.from_dict(
            {
                **open_observation.to_dict(),
                "content_digest_sha256": changed_digest,
            }
        )
        cases = {
            "identity": (
                batch(
                    "c1",
                    "c2",
                    TopicObservationInput("B", identity_variant, content),
                ),
                TopicItemStatus.MANUAL_REVIEW,
                "c2",
            ),
            "digest": (
                batch(
                    "c1",
                    "c2",
                    TopicObservationInput("B", digest_variant, changed_content),
                ),
                TopicItemStatus.MANUAL_REVIEW,
                "c2",
            ),
            "cursor": (
                batch(
                    "c0",
                    "c2",
                    TopicObservationInput("B", open_observation, content),
                ),
                TopicItemStatus.MANUAL_REVIEW,
                "c1",
            ),
        }

        for variant, (candidate_batch, expected_status, expected_cursor) in cases.items():
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                seed = TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )
                self.assertEqual(
                    "PENDING",
                    seed.literature.import_bytes(
                        restricted_observation,
                        content,
                    ).disposition.value,
                )
                exhausted = TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                    budget=BudgetLedger(cost_usd_limit=0.0),
                )
                first = exhausted.run(
                    batch(
                        "c0",
                        "c1",
                        TopicObservationInput("A", restricted_observation, content),
                    )
                )
                self.assertEqual(TopicItemStatus.MANUAL_REVIEW, first.item_results[0].status)

                candidate_runner = TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )
                candidate = candidate_runner.run(candidate_batch)
                self.assertEqual(expected_status, candidate.item_results[0].status)
                self.assertEqual(expected_cursor, candidate_runner.next_cursor)
                current = next(
                    observation
                    for observation in candidate_runner.literature.observations
                    if observation.observation_id == restricted_observation.observation_id
                )
                self.assertEqual(ObservationStatus.PENDING, current.status)

                restarted = TopicObservationRunner(
                    root,
                    topic_id="integrity-topic",
                    initial_cursor="c0",
                )
                self.assertEqual(expected_cursor, restarted.next_cursor)

    def test_manual_ids_are_delimiter_safe_across_batches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(
                directory,
                topic_id="integrity-topic",
                initial_cursor="c|x",
            )
            first = runner.run(
                batch("c|x", "c", input_for("y", risk_flags=("r",)))
            )
            second = runner.run(
                batch("c", "done", input_for("x|y", risk_flags=("r",)))
            )
            first_id = first.item_results[0].manual_id
            second_id = second.item_results[0].manual_id
            self.assertIsNotNone(first_id)
            self.assertIsNotNone(second_id)
            self.assertNotEqual(first_id, second_id)
            self.assertEqual(
                {("c|x", "y"), ("c", "x|y")},
                {(item.cursor, item.input_id) for item in runner.manual_queue},
            )
            restarted = TopicObservationRunner(
                directory,
                topic_id="integrity-topic",
                initial_cursor="c|x",
            )
            self.assertEqual("done", restarted.next_cursor)
            self.assertEqual(2, len(restarted.manual_queue))

    def test_topic_state_path_requires_private_regular_file(self) -> None:
        for mutation in ("symlink", "mode"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
                runner.run(batch("c0", "c1", input_for("A")))
                if mutation == "symlink":
                    backing = root / "topic-observation-state.backing"
                    runner.state_path.rename(backing)
                    runner.state_path.symlink_to(backing.name)
                else:
                    os.chmod(runner.state_path, 0o644)

                with self.assertRaisesRegex(TopicObservationError, "topic observation state"):
                    TopicObservationRunner(
                        root, topic_id="integrity-topic", initial_cursor="c0"
                    ).next_cursor

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

    def test_legacy_state_bytes_are_preserved_for_explicit_replay(self) -> None:
        for legacy_version in ("1.4", "1.5", "1.6"):
            with self.subTest(legacy_version=legacy_version), tempfile.TemporaryDirectory() as directory:
                runner = TopicObservationRunner(
                    directory, topic_id="integrity-topic", initial_cursor="c0"
                )
                runner.run(batch("c0", "c1", input_for("A")))
                state_path = Path(directory) / "topic-observation-state.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                state["schema_version"] = legacy_version
                legacy_bytes = json.dumps(state).encode("utf-8")
                state_path.write_bytes(legacy_bytes)

                with self.assertRaisesRegex(
                    TopicObservationError,
                    f"schema_version '{legacy_version}'.*recovery contract",
                ):
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
        manual_id = "manual-" + digest_json(
            {
                "schema_version": "1.0",
                "topic_id": "integrity-topic",
                "cursor": "c1",
                "input_id": "B",
                "reason": ManualReviewReason.HIGH_RISK_EVENT.value,
                "detail": detail,
            }
        )[:24]
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


@unittest.skipUnless(hasattr(os, "fork"), "POSIX fork is required")
class TopicWriterForkTests(unittest.TestCase):
    def test_forked_child_exit_cannot_unlock_parent_topic_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = TopicObservationRunner(
                directory,
                topic_id="integrity-topic",
                initial_cursor="c0",
            )
            child_pid: int | None = None
            contender_pid: int | None = None
            try:
                with runner._writer_lock():
                    child_pid = os.fork()
                    if child_pid == 0:
                        os._exit(0)
                    _, child_status = os.waitpid(child_pid, 0)
                    child_pid = None
                    self.assertTrue(os.WIFEXITED(child_status))
                    self.assertEqual(0, os.WEXITSTATUS(child_status))

                    contender_pid = os.fork()
                    if contender_pid == 0:
                        try:
                            import fcntl

                            descriptor = os.open(runner.lock_path, os.O_RDWR)
                            try:
                                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            finally:
                                os.close(descriptor)
                        except BlockingIOError:
                            os._exit(0)
                        except BaseException:
                            os._exit(2)
                        os._exit(1)
                    _, contender_status = os.waitpid(contender_pid, 0)
                    contender_pid = None
                    self.assertTrue(os.WIFEXITED(contender_status))
                    self.assertEqual(0, os.WEXITSTATUS(contender_status))
            finally:
                for pid in (child_pid, contender_pid):
                    if pid is not None:
                        os.waitpid(pid, 0)


if __name__ == "__main__":
    unittest.main()
