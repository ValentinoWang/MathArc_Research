from __future__ import annotations

import hashlib
import json
import os
import select
import signal
import stat
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import matharc.v02.artifact_store as artifact_store_module
from matharc.v02.artifact_store import ArtifactStore
from matharc.v02.literature_base import (
    LiteratureBase,
    _topic_transaction_authorized,
    literature_writer_lock,
)
from matharc.v02.source_observation import LicenseStatus, new_observation


def _observation(observation_id: str, content: bytes):
    return new_observation(
        observation_id=observation_id,
        canonical_uri=f"https://durability.example/{observation_id}",
        pinned_version="v1",
        license_status=LicenseStatus.OPEN,
        license_basis="durability fixture license",
        content_summary="Durability fixture metadata.",
        summary_basis="fixture",
        media_type="text/plain",
        content_digest_sha256=hashlib.sha256(content).hexdigest(),
    )


def _read_with_timeout(file_descriptor: int, timeout: float) -> bytes | None:
    readable, _, _ = select.select([file_descriptor], [], [], timeout)
    if not readable:
        return None
    return os.read(file_descriptor, 1)


def _reap(pid: int, *, timeout: float = 3.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        waited_pid, status = os.waitpid(pid, os.WNOHANG)
        if waited_pid == pid:
            return status
        time.sleep(0.01)
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)
    raise AssertionError(f"child process {pid} did not exit")


class ArtifactStoreDurabilityTests(unittest.TestCase):
    def test_blob_and_manifest_replacements_are_fsync_ordered(self) -> None:
        events: list[object] = []
        original_fsync = artifact_store_module.os.fsync
        original_replace = artifact_store_module.os.replace

        def record_fsync(file_descriptor: int) -> None:
            mode = os.fstat(file_descriptor).st_mode
            events.append("file-fsync" if stat.S_ISREG(mode) else "directory-fsync")
            original_fsync(file_descriptor)

        def record_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
            events.append(("replace", Path(target).name))
            original_replace(source, target)

        with tempfile.TemporaryDirectory() as directory:
            store = ArtifactStore(Path(directory) / "store")
            with patch.object(artifact_store_module.os, "fsync", side_effect=record_fsync):
                with patch.object(artifact_store_module.os, "replace", side_effect=record_replace):
                    store.put_bytes(
                        "A",
                        b"durable artifact",
                        logical_role="fixture",
                        producer="test",
                    )

        replacements = [index for index, event in enumerate(events) if isinstance(event, tuple)]
        self.assertEqual(2, len(replacements))
        for index in replacements:
            self.assertGreater(index, 0)
            self.assertLess(index + 1, len(events))
            self.assertEqual("file-fsync", events[index - 1])
            self.assertEqual("directory-fsync", events[index + 1])

    def test_nested_directories_fsync_each_new_directory_parent(self) -> None:
        fsynced: list[Path] = []
        original_fsync_directory = artifact_store_module._fsync_directory

        def record_fsync_directory(path: Path) -> None:
            fsynced.append(path)
            original_fsync_directory(path)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "new" / "nested"
            with patch.object(
                artifact_store_module,
                "_fsync_directory",
                side_effect=record_fsync_directory,
            ):
                ArtifactStore(root)

        self.assertEqual(
            [Path(directory), Path(directory) / "new", root],
            fsynced,
        )

    def test_file_fsync_failure_cleans_temp_and_keeps_artifact_map(self) -> None:
        original_fsync = artifact_store_module.os.fsync

        def fail_regular_file_fsync(file_descriptor: int) -> None:
            if stat.S_ISREG(os.fstat(file_descriptor).st_mode):
                raise OSError("simulated blob fsync failure")
            original_fsync(file_descriptor)

        with tempfile.TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            with patch.object(
                artifact_store_module.os,
                "fsync",
                side_effect=fail_regular_file_fsync,
            ):
                with self.assertRaisesRegex(OSError, "blob fsync failure"):
                    store.put_bytes(
                        "A",
                        b"not published",
                        logical_role="fixture",
                        producer="test",
                    )
            self.assertEqual((), store.records)
            self.assertEqual([], list(Path(directory).rglob("*.tmp")))

    def test_manifest_parent_fsync_failure_keeps_last_artifact_generation(self) -> None:
        original_fsync_directory = artifact_store_module._fsync_directory

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = ArtifactStore(root)

            def fail_manifest_parent(path: Path) -> None:
                if path == root:
                    raise OSError("simulated manifest parent fsync failure")
                original_fsync_directory(path)

            with patch.object(
                artifact_store_module,
                "_fsync_directory",
                side_effect=fail_manifest_parent,
            ):
                with self.assertRaisesRegex(OSError, "manifest parent fsync failure"):
                    store.put_bytes(
                        "A",
                        b"manifest generation two",
                        logical_role="fixture",
                        producer="test",
                    )

            self.assertEqual((), store.records)
            self.assertEqual([], list(root.rglob("*.tmp")))
            self.assertEqual(1, len(json.loads((root / "manifest.json").read_text())["records"]))

    def test_observation_manifest_failure_keeps_last_observation_generation(self) -> None:
        first_content = b"first observation"
        second_content = b"second observation"
        original_fsync_directory = artifact_store_module._fsync_directory

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = LiteratureBase(root)
            first = _observation("OBS-FIRST", first_content)
            second = _observation("OBS-SECOND", second_content)
            base.import_bytes(first, first_content)

            def fail_observation_parent(path: Path) -> None:
                if path == root:
                    raise OSError("simulated observation manifest fsync failure")
                original_fsync_directory(path)

            with patch.object(
                artifact_store_module,
                "_fsync_directory",
                side_effect=fail_observation_parent,
            ):
                with self.assertRaisesRegex(OSError, "observation manifest fsync failure"):
                    base.import_bytes(second, second_content)

            self.assertEqual(["OBS-FIRST"], [item.observation_id for item in base.observations])
            self.assertEqual([], list(root.rglob("*.tmp")))


@unittest.skipUnless(hasattr(os, "fork"), "POSIX fork is required")
class LiteratureWriterForkTests(unittest.TestCase):
    def test_fork_does_not_inherit_reentrancy_or_transaction_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            read_fd, write_fd = os.pipe()
            child_pid: int | None = None
            try:
                with literature_writer_lock(root, allow_topic_transaction=True):
                    child_pid = os.fork()
                    if child_pid == 0:
                        os.close(read_fd)
                        try:
                            os.write(write_fd, b"X" if _topic_transaction_authorized(root) else b"A")
                            with literature_writer_lock(root):
                                os.write(write_fd, b"L")
                        except BaseException:
                            try:
                                os.write(write_fd, b"E")
                            finally:
                                os._exit(1)
                        os._exit(0)
                    os.close(write_fd)
                    write_fd = -1
                    self.assertEqual(b"A", _read_with_timeout(read_fd, 1.0))
                    self.assertIsNone(_read_with_timeout(read_fd, 0.1))
                self.assertEqual(b"L", _read_with_timeout(read_fd, 1.0))
            finally:
                if write_fd != -1:
                    os.close(write_fd)
                os.close(read_fd)
                if child_pid is not None and child_pid > 0:
                    status = _reap(child_pid)
                    self.assertTrue(os.WIFEXITED(status))
                    self.assertEqual(0, os.WEXITSTATUS(status))

    def test_child_exiting_inherited_context_cannot_unlock_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            read_fd, write_fd = os.pipe()
            first_child: int | None = None
            contender: int | None = None
            try:
                with literature_writer_lock(root):
                    first_child = os.fork()
                    if first_child == 0:
                        os.close(read_fd)
                    else:
                        self.assertEqual(b"C", _read_with_timeout(read_fd, 1.0))
                        contender = os.fork()
                        if contender == 0:
                            os.close(read_fd)
                            try:
                                with literature_writer_lock(root):
                                    os.write(write_fd, b"A")
                            except BaseException:
                                try:
                                    os.write(write_fd, b"E")
                                finally:
                                    os._exit(1)
                            os._exit(0)
                        self.assertIsNone(_read_with_timeout(read_fd, 0.1))
                if first_child == 0:
                    os.write(write_fd, b"C")
                    os._exit(0)
                self.assertEqual(b"A", _read_with_timeout(read_fd, 1.0))
            finally:
                os.close(read_fd)
                os.close(write_fd)
                if first_child is not None and first_child > 0:
                    status = _reap(first_child)
                    self.assertTrue(os.WIFEXITED(status))
                    self.assertEqual(0, os.WEXITSTATUS(status))
                if contender is not None and contender > 0:
                    status = _reap(contender)
                    self.assertTrue(os.WIFEXITED(status))
                    self.assertEqual(0, os.WEXITSTATUS(status))


if __name__ == "__main__":
    unittest.main()
