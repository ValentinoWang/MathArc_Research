import unittest

from matharc.v02.runtime.contracts import ExecutionStatus, WorkerExecutionResult
from matharc.v02.runtime.generation import GenerationInputSnapshot, GenerationClosePolicy
from matharc.v02.runtime.reducer import GenerationReducer


class GenerationCommitTests(unittest.TestCase):
    def test_stable_dedup_and_closed_generation_rejects_rewrite(self):
        snapshot = GenerationInputSnapshot.from_inputs(
            workspace_id="w", trace_id="t", runtime_run_id="r", generation_id="g",
            trace={}, contract={}, agenda={}, worker_specs=(), tool_registry={}
        )
        reducer = GenerationReducer(snapshot, close_policy=GenerationClosePolicy(minimum_completed=1))
        result = WorkerExecutionResult("w", "t", "r", "g", "worker", "e", ExecutionStatus.SUCCEEDED, "digest")
        commit = reducer.commit([result, result])
        self.assertEqual(commit.accepted_result_ids, ("e",))
        self.assertEqual(commit.duplicate_result_ids, ("e",))
        self.assertEqual(reducer.commit([result]), commit)
        self.assertEqual(reducer.submit(result), "LATE_QUEUED")
        self.assertEqual(len(reducer.late_results), 1)


if __name__ == "__main__":
    unittest.main()
