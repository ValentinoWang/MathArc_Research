from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from matharc.operations import OperationsLedgerError
from matharc.v02.operations_ledger import open_workspace_operations_ledger, workspace_replay_digest
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle


class WorkspaceOperationsLedgerTests(unittest.TestCase):
    def test_model_and_upstream_switch_preserves_historical_conclusion_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            conclusion_before = (root / "research-trace.json").read_bytes()
            ledger = open_workspace_operations_ledger(root, Path(directory) / "ops.json")
            ledger.append(
                record_id="upstream-local-model-a",
                kind="UPSTREAM_CONFIGURED",
                payload={"provider": "local", "model": "model-a"},
            )
            ledger.append(
                record_id="upstream-remote-model-b",
                kind="UPSTREAM_CONFIGURED",
                payload={"provider": "remote", "model": "model-b"},
            )
            self.assertEqual(conclusion_before, (root / "research-trace.json").read_bytes())

    def test_binding_is_derived_and_workspace_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            ledger = open_workspace_operations_ledger(root, Path(directory) / "ops.json")
            ledger.append(record_id="record-1", kind="USAGE_RECORDED", payload={"units": 1})
            self.assertEqual(workspace_replay_digest(root), ledger.snapshot()["research_replay_digest"])
            after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            with self.assertRaisesRegex(ValueError, "outside"):
                open_workspace_operations_ledger(root, root / "ops.json")

    def test_existing_ledger_rejects_changed_workspace_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            path = Path(directory) / "ops.json"
            open_workspace_operations_ledger(root, path).append(
                record_id="record-1", kind="USAGE_RECORDED", payload={}
            )
            workspace = ResearchWorkspace.load(root)
            workspace._seal_transition("TEST_FOLLOWUP", actor="test", subject_ids=(), details={})
            workspace.save()
            with self.assertRaises(OperationsLedgerError):
                open_workspace_operations_ledger(root, path)

    def test_ledger_cannot_be_reused_by_another_workspace_with_identical_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root_a = Path(directory) / "workspace-a"
            root_b = Path(directory) / "workspace-b"
            write_full_workspace_bundle(root_a)
            shutil.copytree(root_a, root_b)
            self.assertEqual(
                (root_a / "research-trace.json").read_bytes(),
                (root_b / "research-trace.json").read_bytes(),
            )
            self.assertNotEqual(workspace_replay_digest(root_a), workspace_replay_digest(root_b))
            ledger_path = Path(directory) / "ops.json"
            open_workspace_operations_ledger(root_a, ledger_path).append(
                record_id="record-1", kind="USAGE_RECORDED", payload={"units": 1}
            )
            with self.assertRaises(OperationsLedgerError):
                open_workspace_operations_ledger(root_b, ledger_path)


if __name__ == "__main__":
    unittest.main()
