import threading
import time
import unittest
from pathlib import Path

from matharc.v02.runtime.contracts import ExecutionStatus, ResearchWorkerSpec, WorkerExecutionResult
from matharc.v02.runtime.generation import GenerationInputSnapshot
from matharc.v02.runtime.reducer import GenerationError, GenerationReducer
from matharc.v02.runtime.scheduler import BoundedScheduler


def _snapshot() -> GenerationInputSnapshot:
    workers = tuple(ResearchWorkerSpec(worker_id=name) for name in ("worker-a", "worker-b", "worker-c"))
    return GenerationInputSnapshot.from_inputs(
        workspace_id="workspace", trace_id="trace", runtime_run_id="runtime",
        generation_id="g1", trace={"question": "q"}, contract={"version": "1"},
        agenda={"step": 1}, worker_specs=workers, tool_registry={"tools": []},
        source_payload={"input": "frozen"},
    )


class RuntimeParallelGenerationTests(unittest.TestCase):
    def test_members_read_one_snapshot_and_workspaces_are_isolated(self):
        snapshot = _snapshot()
        observations = []
        active = 0
        peak = 0
        lock = threading.Lock()

        def worker(task, received_snapshot, workspace, execution_id):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
                observations.append((task["member_id"], received_snapshot.snapshot_digest,
                                     received_snapshot.generation_id, str(workspace)))
            (workspace / "member.txt").write_text(task["member_id"], encoding="utf-8")
            time.sleep(0.03)
            with lock:
                active -= 1
            return {"member_id": task["member_id"], "wall_seconds": 0.03}

        tasks = [{"member_id": name} for name in ("worker-a", "worker-b", "worker-c")]
        executions = BoundedScheduler(max_concurrency=3).schedule(tasks, snapshot, worker, run_id="run-1")

        self.assertEqual({item.status for item in executions}, {"completed"})
        self.assertGreaterEqual(peak, 2)
        self.assertEqual({item[1] for item in observations}, {snapshot.snapshot_digest})
        self.assertEqual({item[2] for item in observations}, {"g1"})
        self.assertEqual(len({item.workspace for item in executions}), 3)
        self.assertEqual({(Path(item.workspace) / "member.txt").read_text(encoding="utf-8") for item in executions},
                         {"worker-a", "worker-b", "worker-c"})

    def test_single_reducer_stably_orders_and_deduplicates_member_results(self):
        snapshot = _snapshot()
        reducer = GenerationReducer(snapshot)
        results = [
            WorkerExecutionResult("workspace", "trace", "runtime", "g1", "worker-b", "exec-b",
                                  ExecutionStatus.SUCCEEDED, "digest-b"),
            WorkerExecutionResult("workspace", "trace", "runtime", "g1", "worker-a", "exec-a",
                                  ExecutionStatus.SUCCEEDED, "digest-a"),
        ]
        commit = reducer.commit([results[0], results[1], results[0]])

        self.assertEqual(tuple(item.worker_id for item in commit.results), ("worker-a", "worker-b"))
        self.assertEqual(commit.accepted_result_ids, ("exec-a", "exec-b"))
        self.assertEqual(commit.duplicate_result_ids, ("exec-b",))
        self.assertEqual(commit.idempotency_key, "runtime+g1")
        self.assertEqual(reducer.commit(results), commit)

    def test_conflicting_same_execution_is_rejected(self):
        snapshot = _snapshot()
        reducer = GenerationReducer(snapshot)
        first = WorkerExecutionResult("workspace", "trace", "runtime", "g1", "worker-a", "exec-a",
                                      ExecutionStatus.SUCCEEDED, "digest-a")
        conflicting = WorkerExecutionResult("workspace", "trace", "runtime", "g1", "worker-a", "exec-a",
                                            ExecutionStatus.FAILED, "digest-a", failure_class="BROKEN")
        with self.assertRaises(GenerationError):
            reducer.commit([first, conflicting])


if __name__ == "__main__":
    unittest.main()
