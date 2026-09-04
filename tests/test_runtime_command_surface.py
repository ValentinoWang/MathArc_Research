import unittest

from matharc.v02.runtime.service import ACTION_CLASSES, ConsoleRuntimeService, SIMULATED_WRITES, UnknownActionError


class RuntimeCommandSurfaceTests(unittest.TestCase):
    def test_exactly_57_registered_actions(self):
        self.assertEqual(len(ACTION_CLASSES), 57)

    def test_unknown_and_live_simulated_actions_fail(self):
        with self.assertRaises(UnknownActionError):
            ConsoleRuntimeService(".").register_action("shell", idempotency_key="x")
        with self.assertRaises(PermissionError):
            ConsoleRuntimeService(".").register_action(next(iter(SIMULATED_WRITES)), idempotency_key="x")

    def test_lifecycle_receipt_is_idempotent_and_rejects_process_inputs(self):
        service = ConsoleRuntimeService(".")
        service.create_run("run-1")
        first = service.runtime_action("run-1", "start", action_id="act-1")
        second = service.runtime_action("run-1", "start", action_id="act-1")
        self.assertEqual(first.to_dict(), second.to_dict())
        with self.assertRaisesRegex(ValueError, "command"):
            service.runtime_action("run-1", "pause", action_id="act-2", payload={"command": "sh"})


if __name__ == "__main__":
    unittest.main()
