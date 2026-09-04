from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from matharc.v02.runtime.contracts import ExecutionStatus, WorkerExecutionResult
from matharc.v02.runtime.generation import GenerationInputSnapshot
from matharc.v02.runtime.reducer import GenerationReducer
from matharc.v02.runtime.recovery import build_recovery_plan
from matharc.v02.runtime.run_store import RuntimeStore


def snapshot(generation_id: str) -> GenerationInputSnapshot:
    return GenerationInputSnapshot.from_inputs(
        workspace_id="pilot-workspace", trace_id="pilot-trace", runtime_run_id="pilot-run",
        generation_id=generation_id, trace={"problem": "baseline"}, contract={"v": 1},
        agenda={"generation": generation_id}, worker_specs=(), tool_registry={},
        source_payload={"problem": "baseline"},
    )


class RuntimePilotGenerationConsumptionTests(unittest.TestCase):
    def test_g2_consumes_g1_commit_and_recovery_is_deterministic(self) -> None:
        g1 = snapshot("g1")
        result = WorkerExecutionResult("pilot-workspace", "pilot-trace", "pilot-run", "g1", "worker-1", "exec-g1", ExecutionStatus.SUCCEEDED, "digest-g1")
        commit = GenerationReducer(g1).commit([result])
        self.assertTrue(commit.closed)
        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            stored = store.record_generation_commit(commit)
            plan = build_recovery_plan(store, expected={"snapshot_digest": g1.snapshot_digest})
            self.assertEqual(plan.next_generation_id, "g2")
            self.assertEqual(plan.commit_digest, stored["commit_digest"])
            self.assertEqual(plan.replay().to_dict(), plan.to_dict())

    def test_g2_reducer_rejects_g1_result_and_quarantines_late_result(self) -> None:
        reducer = GenerationReducer(snapshot("g2"))
        wrong_generation = WorkerExecutionResult("pilot-workspace", "pilot-trace", "pilot-run", "g1", "worker-1", "exec-old", ExecutionStatus.SUCCEEDED, "old")
        with self.assertRaises(Exception):
            reducer.submit(wrong_generation)
        current = WorkerExecutionResult("pilot-workspace", "pilot-trace", "pilot-run", "g2", "worker-1", "exec-g2", ExecutionStatus.SUCCEEDED, "new")
        reducer.commit([current])
        self.assertEqual(reducer.submit(current), "LATE_QUEUED")
        self.assertEqual(reducer.late_results[0].execution_id, "exec-g2")


if __name__ == "__main__":
    unittest.main()
