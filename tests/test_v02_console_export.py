from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from matharc.v02.console_export import build_console_export, write_console_export
from matharc.v02.workspace_bundle import write_full_workspace_bundle


class ConsoleExportTests(unittest.TestCase):
    def test_export_is_read_only_and_discloses_absent_campaign(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            before = (root / "workspace.json").read_bytes()
            payload = build_console_export(root)
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertTrue(payload["workspace"]["audit"]["valid"])
            self.assertFalse(payload["campaign"]["available"])
            self.assertEqual(payload["view_contract"]["source_registry_projection"], "live")
            source_claims = payload["source_topic"]["source_claims"]
            self.assertEqual(source_claims[0]["source_claim_id"], "SRC-INDUCTION")
            self.assertEqual(source_claims[0]["status"], "VERIFIED")
            self.assertEqual(before, (root / "workspace.json").read_bytes())

    def test_campaign_and_json_output_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            report = Path(directory) / "campaign.json"
            report.write_text(json.dumps({"rounds": [], "stop_reason": "done", "final_metrics": {}, "budget": None, "creation_log": []}), encoding="utf-8")
            target = write_console_export(root, Path(directory) / "console.json", campaign_report_path=report)
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertTrue(payload["campaign"]["available"])
            self.assertEqual(payload["campaign"]["report"]["stop_reason"], "done")
            with self.assertRaises(ValueError):
                write_console_export(root, Path(directory) / "console.txt")

    def test_module_cli_writes_the_same_versioned_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            output = Path(directory) / "console.json"
            write_full_workspace_bundle(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "matharc.v02",
                    "export",
                    "--workspace-root",
                    str(root),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["view_contract"]["verification_publication"], "live")


if __name__ == "__main__":
    unittest.main()
