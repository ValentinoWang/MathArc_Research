import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.run_store import RuntimeStore, RuntimeStoreError


class RuntimeStoreReplayTests(unittest.TestCase):
    def test_restart_replays_hash_chain_and_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RuntimeStore(Path(tmp) / "runtime")
            store.append_event("NOTE", {"value": 1})
            restarted = RuntimeStore(Path(tmp) / "runtime")
            self.assertEqual(restarted.state, store.state)
            self.assertEqual(restarted.head_hash, store.head_hash)

    def test_truncated_or_corrupt_log_and_snapshot_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runtime"
            store = RuntimeStore(root)
            store.append_event("NOTE", {"value": 1})
            log = root / "events.jsonl"
            log.write_text(log.read_text()[:-4], encoding="utf-8")
            with self.assertRaises(RuntimeStoreError): RuntimeStore(root)

            store = RuntimeStore(Path(tmp) / "other")
            store.append_event("NOTE", {"value": 1})
            snapshot = Path(tmp) / "other" / "snapshot.json"
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            payload["state_digest_sha256"] = "0" * 64
            snapshot.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(RuntimeStoreError): RuntimeStore(Path(tmp) / "other")


if __name__ == "__main__": unittest.main()
