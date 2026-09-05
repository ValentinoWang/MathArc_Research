from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import subprocess
import sys

from matharc.v02.runtime.run_store import RuntimeStore

ROOT = Path(__file__).resolve().parents[1]


class RuntimeOpsCleanupTests(unittest.TestCase):
    def test_cleanup_checklist_requires_explicit_regenerable_scope(self) -> None:
        text = (ROOT / "acceptance/runtime-pilot/ops-checklist.md").read_text(encoding="utf-8")
        self.assertIn("explicit", text.lower())
        self.assertIn("backup", text.lower())
        self.assertIn("protected", text.lower())

    def test_explicit_cache_cleanup_keeps_runtime_store_replayable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            store = RuntimeStore(root)
            store.append_event("NOTE", {"value": "durable"})
            cache = root / "regenerable.cache"
            cache.write_text("cache", encoding="utf-8")
            cache.unlink()
            restarted = RuntimeStore(root)
            self.assertEqual(restarted.state, store.state)
            self.assertTrue((root / "events.jsonl").exists())

    def test_ops_release_checklist_keeps_release_identity_and_rollback(self) -> None:
        text = (ROOT / "acceptance/runtime-pilot/ops-release-checklist.md").read_text(encoding="utf-8")
        lowered = text.lower()
        for token in ("release id", "commit", "rollback", "not ready"):
            self.assertIn(token, lowered)

    def test_cleanup_cli_backs_up_then_removes_explicit_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"; root.mkdir()
            RuntimeStore(root).append_event("NOTE", {"value": "durable"})
            cache = root / "cache.tmp"; cache.write_text("cache", encoding="utf-8")
            backup = Path(directory) / "backup"
            completed = subprocess.run([sys.executable, "-m", "matharc.v02.runtime.ops", "cleanup", "--root", str(root), "--backup", str(backup), "--candidate", "cache.tmp"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(cache.exists())
            self.assertTrue((backup / "backup-manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
