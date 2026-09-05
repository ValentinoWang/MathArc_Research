from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.ops import backup_runtime_store, restore_runtime_store, RuntimeBootstrapError
from matharc.v02.runtime.run_store import RuntimeStore
from matharc.v02.schema import TheoremContract
from matharc.v02.trace import (
    ResearchTrace,
    TraceValidationError,
    backup_trace,
    restore_trace_backup,
)


class RuntimeOpsBackupTests(unittest.TestCase):
    def test_backup_restore_preserves_identity_and_digest(self) -> None:
        trace = ResearchTrace("trace-1", TheoremContract("K", "p", (), "s"))
        with tempfile.TemporaryDirectory() as directory:
            path = backup_trace(trace, Path(directory) / "backup.json")
            restored = restore_trace_backup(path)
        self.assertEqual(restored.run_id, trace.run_id)
        self.assertEqual(restored.content_digest(), trace.content_digest())

    def test_tampered_backup_is_rejected(self) -> None:
        trace = ResearchTrace("trace-1", TheoremContract("K", "p", (), "s"))
        with tempfile.TemporaryDirectory() as directory:
            path = backup_trace(trace, Path(directory) / "backup.json")
            text = path.read_text(encoding="utf-8").replace("trace-1", "trace-2")
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(TraceValidationError):
                restore_trace_backup(path)

    def test_runtime_store_backup_restore_checks_identity_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "store"
            store = RuntimeStore(source)
            store.create_run({"runtime_run_id": "rr", "release_id": "rel", "workspace_id": "w", "trace_id": "t", "generation_id": "g"})
            backup = backup_runtime_store(source, root / "backup")
            manifest = __import__("json").loads((backup / "backup-manifest.json").read_text())
            restored = restore_runtime_store(backup, root / "restored", runtime_run_id="rr", release_id="rel", expected_digest=manifest["manifest_digest_sha256"])
            self.assertEqual(RuntimeStore(restored).state, store.state)
            with self.assertRaises(RuntimeBootstrapError):
                restore_runtime_store(backup, root / "wrong", runtime_run_id="other")


if __name__ == "__main__":
    unittest.main()
