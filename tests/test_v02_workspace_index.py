from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_index import WorkspaceIndex


class WorkspaceIndexTests(unittest.TestCase):
    def test_scan_reads_valid_workspaces_without_mutating_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid = root / "valid"
            write_full_workspace_bundle(valid)
            before = (valid / "workspace.json").read_bytes()
            result = WorkspaceIndex.scan(root)
            self.assertEqual(len(result.workspaces), 1)
            self.assertEqual(result.workspaces[0].workspace_root, str(valid.resolve()))
            self.assertEqual(result.invalid_candidates, ())
            self.assertEqual(before, (valid / "workspace.json").read_bytes())

    def test_scan_reports_malformed_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = root / "invalid"
            invalid.mkdir()
            (invalid / "workspace.json").write_text("{not json", encoding="utf-8")
            result = WorkspaceIndex.scan(root)
            self.assertEqual(result.workspaces, ())
            self.assertEqual(result.invalid_candidates[0]["workspace_root"], str(invalid.resolve()))

    def test_scan_requires_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                WorkspaceIndex.scan(Path(directory) / "missing")


if __name__ == "__main__":
    unittest.main()
