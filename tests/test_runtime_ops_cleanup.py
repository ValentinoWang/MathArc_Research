from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
