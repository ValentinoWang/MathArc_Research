from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.service import ConsoleRuntimeService

ROOT = Path(__file__).resolve().parents[1]


class RuntimeOpsReleaseTests(unittest.TestCase):
    def test_release_checklist_is_not_a_production_claim(self) -> None:
        text = (ROOT / "acceptance/runtime-pilot/production-checklist.md").read_text(encoding="utf-8")
        self.assertIn("NOT READY", text)
        self.assertIn("not executed by this pilot", text)
        self.assertIn("human acceptance", text.lower())

    def test_lifecycle_release_receipts_are_idempotent_and_bounded(self) -> None:
        service = ConsoleRuntimeService(ROOT)
        created = service.create_run("release-pilot-run")
        self.assertEqual(created["status"], "CREATED")
        started = service.runtime_action("release-pilot-run", "start", action_id="release-start")
        replay = service.runtime_action("release-pilot-run", "start", action_id="release-start")
        self.assertEqual(started.to_dict(), replay.to_dict())
        self.assertEqual(started.status.value, "COMPLETED")
        with self.assertRaises(ValueError):
            service.runtime_action("release-pilot-run", "stop", action_id="release-stop", payload={"environment": {"SECRET": "x"}})

    def test_plan_machine_commands_are_python_unittest_commands(self) -> None:
        plan = json.loads((ROOT / "benchmarks/runtime-pilot-plan.json").read_text(encoding="utf-8"))
        self.assertTrue(all("unittest" in command for command in plan["machine_commands"]))
        self.assertTrue(plan["operations"]["release_identity_required"])

    def test_restore_and_rollback_are_executable_cli_operations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "store"
            from matharc.v02.runtime.run_store import RuntimeStore
            from matharc.v02.runtime.ops import backup_runtime_store
            RuntimeStore(source).create_run({"runtime_run_id": "rr", "release_id": "rel", "workspace_id": "w", "trace_id": "t", "generation_id": "g"})
            backup = backup_runtime_store(source, root / "backup")
            for command, destination in (("restore", root / "restored"), ("rollback", root / "rolled-back")):
                completed = subprocess.run([sys.executable, "-m", "matharc.v02.runtime.ops", command, "--backup", str(backup), "--destination", str(destination), "--runtime-run-id", "rr", "--release-id", "rel"], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertTrue(destination.is_dir())


if __name__ == "__main__":
    unittest.main()
