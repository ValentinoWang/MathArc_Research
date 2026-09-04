import unittest

from matharc.v02.runtime.reconnect import ReconnectManager


class RuntimeConsoleReconnectTests(unittest.TestCase):
    def test_contiguous_events_continue_from_cursor(self):
        manager = ReconnectManager("run-1", 2)
        result = manager.reconnect(run_id="run-1", after=1, events=[{"sequence": 2}, {"sequence": 3}])
        self.assertEqual([event["sequence"] for event in result.events], [2, 3])
        self.assertFalse(result.reload_required)

    def test_run_change_requires_snapshot(self):
        result = ReconnectManager("run-1", 1).reconnect(run_id="run-2", after=1, events=[])
        self.assertTrue(result.reload_required)


if __name__ == "__main__":
    unittest.main()
