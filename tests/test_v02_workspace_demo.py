from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_demo import build_workspace_demo, write_workspace_demo


class WorkspaceDemoTests(unittest.TestCase):
    def test_demo_audit_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = build_workspace_demo(directory)
            self.assertTrue(workspace.audit().valid)
            self.assertEqual(len(workspace.artifacts.records), 6)
            self.assertEqual(len(workspace.objects.objects), 3)
            self.assertEqual(len(workspace.sources.claims), 1)
            paths = write_workspace_demo(Path(directory) / "export")
            for path in paths.values():
                self.assertTrue(path.is_file(), path)
            loaded = ResearchWorkspace.load(Path(directory) / "export")
            self.assertTrue(loaded.audit().valid)
            summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
            self.assertEqual(summary["state_digest_sha256"], loaded.state_digest())
            self.assertEqual(summary["event_head_hash"], loaded.events.head_hash)


if __name__ == "__main__":
    unittest.main()
