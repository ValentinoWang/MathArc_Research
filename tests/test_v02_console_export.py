from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from matharc.v02.console_export import (
    ConsoleLocalProjectionConfig,
    build_console_export,
    write_console_export,
)
from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workers import StaticProposalWorker
from tests.fake_claude_code import write_fake_claude_code


class ConsoleExportTests(unittest.TestCase):
    @staticmethod
    def _record_campaign(root: Path) -> str:
        workspace = ResearchWorkspace.load(root)
        campaign = ResearchCampaign(
            workspace.trace,
            [StaticProposalWorker("prover", {})],
            budget=BudgetLedger(wall_seconds_limit=0.0),
        )
        report = campaign.run()
        artifact_id = workspace.record_campaign_result(campaign, report)
        workspace.save()
        return artifact_id

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
            self.assertEqual(payload["view_contract"]["admin_roster"], "not_configured_fail_closed")
            self.assertEqual(payload["view_contract"]["accounting"], "not_configured_fail_closed")
            for view in ("acct_overview", "acct_usage", "acct_billing", "acct_limits"):
                self.assertEqual(payload["view_contract"][view], "not_configured_fail_closed")
            self.assertEqual(payload["view_contract"]["admin_cost"], "not_configured_fail_closed")
            source_claims = payload["source_topic"]["source_claims"]
            self.assertEqual(source_claims[0]["source_claim_id"], "SRC-INDUCTION")
            self.assertEqual(source_claims[0]["status"], "VERIFIED")
            self.assertEqual(payload["routes"]["state"], "live")
            self.assertEqual(payload["disclosure"]["state"], "live")
            self.assertEqual(len(payload["routes"]["routes"]), len(payload["workspace"]["trace"]["routes"]))
            self.assertEqual(len(payload["disclosure"]["records"]["state"]), len(payload["workspace"]["trace"]["claims"]))
            self.assertNotIn("workspace_root", payload["provenance"])
            self.assertEqual(before, (root / "workspace.json").read_bytes())
            self.assertEqual(payload["novelty"]["state"], "not_configured")

    def test_configured_novelty_audit_is_exported_and_missing_record_fails_closed(self) -> None:
        fixture = Path(__file__).parents[1] / "agents-results/2026-08-31/problem-intelligence-plane/evidence/s2-fixtures/q6-candidate-audit.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            payload = build_console_export(
                root,
                local_projection_config=ConsoleLocalProjectionConfig(novelty_audit_path=fixture),
            )
            self.assertEqual(payload["view_contract"]["novelty_projection"], "live_if_configured")
            self.assertEqual(payload["novelty"]["state"], "live")
            self.assertEqual(payload["novelty"]["audit"]["audit_id"], "NOVELTY-Q6-1")
            self.assertEqual(payload["novelty"]["authorization"]["status"], "CONTRACT_ONLY")
            with self.assertRaisesRegex(ValueError, "novelty audit record is missing"):
                build_console_export(
                    root,
                    local_projection_config=ConsoleLocalProjectionConfig(
                        novelty_audit_path=Path(directory) / "missing.json"
                    ),
                )

    def test_campaign_and_json_output_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            artifact_id = self._record_campaign(root)
            target = write_console_export(root, Path(directory) / "console.json")
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertTrue(payload["campaign"]["available"])
            self.assertEqual(
                payload["campaign"]["report"]["stop_reason"],
                "release_state_terminal:PROVED_AND_AUDITED",
            )
            self.assertEqual(payload["campaign"]["artifact_id"], artifact_id)
            with self.assertRaises(ValueError):
                write_console_export(root, Path(directory) / "console.txt")

    def test_export_refuses_to_overwrite_any_workspace_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            manifest = root / "workspace.json"
            before = manifest.read_bytes()
            with self.assertRaises(ValueError):
                write_console_export(root, manifest)
            self.assertEqual(before, manifest.read_bytes())

    def test_external_campaign_json_cannot_be_presented_as_a_registered_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            report = Path(directory) / "campaign.json"
            write_full_workspace_bundle(root)
            report.write_text(
                json.dumps({"rounds": "not-an-array", "stop_reason": 7, "final_metrics": {}, "budget": None, "creation_log": []}),
                encoding="utf-8",
            )
            payload = build_console_export(root)
            self.assertFalse(payload["campaign"]["available"])
            self.assertEqual(payload["campaign"]["reason"], "campaign_report_not_recorded")

    def test_workspace_rejects_a_report_not_returned_by_its_campaign_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            workspace = ResearchWorkspace.load(root)
            campaign = ResearchCampaign(
                workspace.trace,
                [StaticProposalWorker("prover", {})],
                budget=BudgetLedger(wall_seconds_limit=0.0),
            )
            report = campaign.run()
            other_campaign = ResearchCampaign(
                workspace.trace,
                [StaticProposalWorker("prover", {})],
                budget=BudgetLedger(wall_seconds_limit=0.0),
            )
            with self.assertRaisesRegex(ValueError, "not produced"):
                workspace.record_campaign_result(other_campaign, report)

    def test_later_workspace_transition_makes_a_campaign_report_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            self._record_campaign(root)
            workspace = ResearchWorkspace.load(root)
            workspace._seal_transition(
                "TEST_FOLLOWUP", actor="test", subject_ids=(), details={}
            )
            workspace.save()
            payload = build_console_export(root)
            self.assertFalse(payload["campaign"]["available"])
            self.assertEqual(payload["campaign"]["reason"], "campaign_report_stale")

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

    def test_workspace_run_then_export_exposes_only_the_registered_campaign(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            report = Path(directory) / "run-report.json"
            output = Path(directory) / "console.json"
            fake = write_fake_claude_code(directory)
            write_full_workspace_bundle(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "matharc.v02",
                    "run",
                    "--workspace-root",
                    str(root),
                    "--role",
                    "prover",
                    "--rounds",
                    "1",
                    "--claude-executable",
                    str(fake),
                    "--output",
                    str(report),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertIn("campaign_artifact_id", run_payload)
            exported = subprocess.run(
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
            self.assertEqual(exported.returncode, 0, exported.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(payload["campaign"]["available"])
            self.assertEqual(payload["campaign"]["artifact_id"], run_payload["campaign_artifact_id"])


if __name__ == "__main__":
    unittest.main()
