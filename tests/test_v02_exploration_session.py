from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.exploration_session import ExplorationEntry, ExplorationSessionStore
from matharc.v02.local_store import LocalStoreError
from matharc.v02.workspace_bundle import write_full_workspace_bundle


PROVENANCE = {"run_id": "R", "state_digest_sha256": "a" * 64, "event_head_hash": "b" * 64}


class ExplorationSessionStoreTests(unittest.TestCase):
    def test_create_append_reload_and_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ExplorationSessionStore(Path(directory) / "sessions")
            created = store.create("S-1", PROVENANCE, created_at="2026-09-01T00:00:00+00:00")
            self.assertEqual(store.create("S-1", PROVENANCE, created_at="2026-09-01T00:00:00+00:00"), created)
            entry = ExplorationEntry("E-1", "CONJECTURE", {"text": "bounded draft"}, "2026-09-01T00:01:00+00:00")
            updated = store.append("S-1", entry)
            self.assertEqual(store.append("S-1", entry), updated)
            reloaded = ExplorationSessionStore(Path(directory) / "sessions").load("S-1")
            self.assertEqual(reloaded.entries, (entry,))

    def test_tamper_and_conflicting_entry_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sessions"
            store = ExplorationSessionStore(root)
            store.create("S-1", PROVENANCE)
            store.append("S-1", ExplorationEntry("E-1", "EXPERIMENT", {"input": "x"}, "2026-09-01T00:00:00+00:00"))
            data = json.loads((root / "exploration-sessions.json").read_text(encoding="utf-8"))
            data["sessions"][0]["entries"][0]["payload"] = {"input": "tampered"}
            (root / "exploration-sessions.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(LocalStoreError):
                ExplorationSessionStore(root).list()

    def test_rejects_research_workspace_location_and_malformed_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            write_full_workspace_bundle(workspace)
            with self.assertRaises(LocalStoreError):
                ExplorationSessionStore(workspace / "sessions")
            store = ExplorationSessionStore(Path(directory) / "sessions")
            with self.assertRaises(LocalStoreError):
                store.create("S-1", {"run_id": "R"})


if __name__ == "__main__":
    unittest.main()
