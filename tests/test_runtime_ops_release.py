from __future__ import annotations

import json
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


if __name__ == "__main__":
    unittest.main()
