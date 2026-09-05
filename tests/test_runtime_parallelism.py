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

    def test_declared_budget_is_admitted_before_worker_start_and_worker_receipt_is_advisory(self):
        started = []
        snapshot = GenerationInputSnapshot.from_inputs(workspace_id="w", trace_id="t", runtime_run_id="r",
            generation_id="g", trace={}, contract={}, agenda={}, worker_specs=(), tool_registry={}, source_payload={})

        def worker(task):
            started.append(task["id"])
            return {"cost_usd": 999, "input_tokens": 999, "wall_seconds": 999}

        result = BoundedScheduler(max_concurrency=2, budget={"max_cost": 1}).schedule(
            [{"id": "too-large", "budget": {"max_cost": 2}}, {"id": "allowed", "budget": {"max_cost": .5}}],
            snapshot, worker)
        self.assertEqual(result[0].status, "budget_exceeded")
        self.assertEqual(started, ["allowed"])
        self.assertEqual(result[1].resource_receipt.cost_usd, 0)

    def test_snapshot_runtime_identity_wins_over_legacy_run_id_override(self):
        snapshot = GenerationInputSnapshot.from_inputs(workspace_id="w", trace_id="t", runtime_run_id="r",
            generation_id="g", trace={}, contract={}, agenda={}, worker_specs=(), tool_registry={}, source_payload={})
        result = BoundedScheduler().schedule([{"id": "member"}], snapshot, lambda task: "ok", run_id="other")
        self.assertEqual(result[0].idempotency_key, "r:g:member")


if __name__ == "__main__":
    unittest.main()
