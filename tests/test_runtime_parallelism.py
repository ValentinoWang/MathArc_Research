import threading
import time
import unittest
from matharc.v02.runtime.scheduler import BoundedScheduler, GenerationInputSnapshot


class RuntimeParallelismTests(unittest.TestCase):
    def test_bounded_scheduler_overlaps_and_isolates_workspaces(self):
        active = 0
        peak = 0
        lock = threading.Lock()

        def worker(task, snapshot, workspace, execution_id):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            (workspace / "result.txt").write_text(execution_id)
            time.sleep(0.05)
            with lock:
                active -= 1
            return execution_id

        tasks = [{"id": str(i), "member_id": str(i)} for i in range(3)]
        snapshot = GenerationInputSnapshot.from_inputs(workspace_id="w", trace_id="t", runtime_run_id="r", generation_id="g", trace={}, contract={}, agenda={}, worker_specs=(), tool_registry={}, source_payload={"x": 1})
        result = BoundedScheduler(max_concurrency=3).schedule(tasks, snapshot, worker)
        self.assertGreaterEqual(peak, 3)
        self.assertEqual(len({item.workspace for item in result}), 3)
        self.assertEqual({item.status for item in result}, {"completed"})


if __name__ == "__main__":
    unittest.main()
