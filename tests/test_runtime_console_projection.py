import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.view_model import ConsoleSnapshot, project_console_snapshot
from matharc.v02.workspace_bundle import write_full_workspace_bundle


class RuntimeConsoleProjectionTests(unittest.TestCase):
    def test_projection_has_provenance_cursor_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            write_full_workspace_bundle(root)
            snapshot = project_console_snapshot(root)
            self.assertTrue(snapshot.run_id)
            self.assertGreaterEqual(snapshot.sequence, 0)
            self.assertEqual(len(snapshot.payload_digest_sha256), 64)
            self.assertEqual(ConsoleSnapshot.from_payload(snapshot.payload).run_id, snapshot.run_id)


if __name__ == "__main__":
    unittest.main()
