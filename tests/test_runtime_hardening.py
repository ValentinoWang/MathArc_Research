import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from matharc.v02.runtime.contracts import ExecutionStatus, ResearchWorkerSpec, WorkerExecutionResult
from matharc.v02.runtime.generation import GenerationClosePolicy, GenerationCommit, GenerationError, GenerationInputSnapshot
from matharc.v02.runtime.reducer import GenerationReducer
from matharc.v02.runtime.recovery import RecoveryError, RecoveryPlan, build_recovery_plan
from matharc.v02.runtime.run_store import RuntimeStore, RuntimeStoreError


def _snapshot(generation_id="g1"):
    return GenerationInputSnapshot.from_inputs(
        workspace_id="w", trace_id="t", runtime_run_id="r", generation_id=generation_id,
        trace={}, contract={}, agenda={}, worker_specs=(ResearchWorkerSpec("required"), ResearchWorkerSpec("optional")), tool_registry={}
    )


class RuntimeHardeningTests(unittest.TestCase):
    def test_closed_reducer_quarantines_extra_result(self):
        reducer = GenerationReducer(_snapshot())
        first = WorkerExecutionResult("w", "t", "r", "g1", "required", "e1", ExecutionStatus.SUCCEEDED, "d1")
        extra = WorkerExecutionResult("w", "t", "r", "g1", "required", "e2", ExecutionStatus.SUCCEEDED, "d2")
        reducer.commit([first])
        reducer.reduce([first, extra])
        self.assertEqual([r.execution_id for r in reducer.late_results], ["e1", "e2"])

    def test_partial_policy_keeps_generation_open_until_required_success(self):
        reducer = GenerationReducer(_snapshot(), close_policy=GenerationClosePolicy(
            minimum_completed=1, required_worker_ids=("required",), allow_partial=False
        ))
        optional = WorkerExecutionResult("w", "t", "r", "g1", "optional", "e1", ExecutionStatus.SUCCEEDED, "d1")
        commit = reducer.commit([optional])
        self.assertFalse(commit.closed)

    def test_partial_policy_timeout_becomes_failed_terminal(self):
        reducer = GenerationReducer(_snapshot(), close_policy=GenerationClosePolicy(
            minimum_completed=1, required_worker_ids=("required",), allow_partial=False, timeout_seconds=1
        ))
        optional = WorkerExecutionResult("w", "t", "r", "g1", "optional", "e1", ExecutionStatus.SUCCEEDED, "d1")
        commit = reducer.commit([optional], elapsed_seconds=2)
        self.assertEqual(commit.status, "FAILED")
        self.assertTrue(commit.closed)

    def test_open_generation_reduction_retains_retryable_results(self):
        reducer = GenerationReducer(_snapshot(), close_policy=GenerationClosePolicy(close_on_all_terminal=False))
        retry = WorkerExecutionResult("w", "t", "r", "g1", "required", "retry", ExecutionStatus.RETRYABLE_FAILURE, "", failure_class="TIMEOUT")
        success = WorkerExecutionResult("w", "t", "r", "g1", "required", "ok", ExecutionStatus.SUCCEEDED, "ok")
        reducer.commit([retry])
        commit = reducer.commit([success])
        self.assertEqual({r.execution_id for r in commit.results}, {"retry", "ok"})

    def test_recovery_rejects_cross_run_missing_pin_and_tampered_digest(self):
        commit = {"runtime_run_id": "r", "generation_id": "g1", "complete": True}
        with self.assertRaises(RecoveryError):
            build_recovery_plan([commit], runtime_run_id="other")
        with self.assertRaises(RecoveryError):
            build_recovery_plan([commit], expected={"snapshot_digest": "required"})
        plan = build_recovery_plan([commit])
        with self.assertRaises(RecoveryError):
            RecoveryPlan.from_dict({**plan.to_dict(), "plan_digest": "tampered"})

    def test_commit_rejects_cross_workspace_result(self):
        result = WorkerExecutionResult("other", "t", "r", "g1", "required", "e", ExecutionStatus.SUCCEEDED, "d")
        with self.assertRaises(GenerationError):
            GenerationCommit("w", "t", "r", "g1", "snap", (result,))

    def test_cost_and_late_result_ledgers_are_strict_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            source = {"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1"}
            for amount in (-1, float("nan"), float("inf")):
                with self.assertRaises(RuntimeStoreError):
                    store.import_cost(str(amount), amount, source)
            late = {**source, "execution_id": "late", "status": "SUCCEEDED"}
            self.assertEqual(store.record_late_result(late), store.record_late_result(late))
            self.assertEqual(len(store.state["late_results"]), 1)

    def test_concurrent_appends_replay_as_one_hash_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            store = RuntimeStore(root)
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda i: store.append_event("NOTE", {"i": i}), range(20)))
            self.assertEqual(len(RuntimeStore(root).events), 20)


if __name__ == "__main__":
    unittest.main()
