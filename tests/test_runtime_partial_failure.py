import time
import unittest

from matharc.v02.runtime.contracts import ExecutionStatus, ResearchWorkerSpec, WorkerExecutionResult
from matharc.v02.runtime.generation import GenerationClosePolicy, GenerationInputSnapshot
from matharc.v02.runtime.reducer import GenerationReducer
from matharc.v02.runtime.scheduler import BoundedScheduler


def _snapshot() -> GenerationInputSnapshot:
    workers = tuple(ResearchWorkerSpec(worker_id=name) for name in ("required", "optional", "slow"))
    return GenerationInputSnapshot.from_inputs(
        workspace_id="w", trace_id="t", runtime_run_id="r", generation_id="g1",
        trace={}, contract={}, agenda={}, worker_specs=workers, tool_registry={}
    )


class RuntimePartialFailureTests(unittest.TestCase):
    def test_failed_member_and_missing_required_role_cannot_be_complete(self):
        reducer = GenerationReducer(
            _snapshot(),
            close_policy=GenerationClosePolicy(minimum_completed=1, required_worker_ids=("required",)),
        )
        success = WorkerExecutionResult("w", "t", "r", "g1", "optional", "ok", ExecutionStatus.SUCCEEDED, "ok")
        failed = WorkerExecutionResult("w", "t", "r", "g1", "slow", "bad", ExecutionStatus.FAILED, "bad",
                                       failure_class="WORKER_ERROR")
        commit = reducer.commit([failed, success])

        self.assertEqual(commit.status, "PARTIAL")
        self.assertTrue(commit.closed)
        self.assertEqual(commit.accepted_result_ids, ("ok",))
        self.assertEqual(commit.failed_result_ids, ("bad",))
        self.assertNotEqual(commit.status, "COMPLETED")

    def test_timeout_without_a_success_is_failed_even_when_close_policy_expires(self):
        reducer = GenerationReducer(
            _snapshot(),
            close_policy=GenerationClosePolicy(minimum_completed=1, timeout_seconds=1),
        )
        timed_out = WorkerExecutionResult("w", "t", "r", "g1", "slow", "timeout", ExecutionStatus.TIMED_OUT,
                                          "", failure_class="TIMEOUT", elapsed_seconds=2)
        commit = reducer.commit([timed_out], elapsed_seconds=2)

        self.assertEqual(commit.status, "FAILED")
        self.assertTrue(commit.closed)
        self.assertEqual(commit.failed_result_ids, ("timeout",))

    def test_scheduler_retries_only_within_declared_limit(self):
        attempts = 0

        def flaky(_task):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("transient")
            return {"ok": True}

        snapshot = _snapshot()
        result = BoundedScheduler(max_concurrency=1, max_retries=1).schedule(
            [{"member_id": "optional"}], snapshot, flaky, run_id="retry-run"
        )
        self.assertEqual(attempts, 2)
        self.assertEqual(result[0].status, "completed")
        self.assertEqual(result[0].attempts, 2)

    def test_scheduler_timeout_is_recorded_as_failure_receipt(self):
        def slow(_task):
            time.sleep(0.05)
            return {"ok": True}

        result = BoundedScheduler(max_concurrency=1, timeout_seconds=0.005).schedule(
            [{"member_id": "slow"}], _snapshot(), slow, run_id="timeout-run"
        )
        self.assertEqual(result[0].status, "timeout")
        self.assertEqual(result[0].error, "worker timed out")


if __name__ == "__main__":
    unittest.main()
