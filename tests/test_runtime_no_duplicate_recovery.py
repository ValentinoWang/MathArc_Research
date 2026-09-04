import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.recovery import build_recovery_plan
from matharc.v02.runtime.run_store import RuntimeStore, RuntimeStoreError
from matharc.v02.runtime.synthesis import synthesize_candidate


class RuntimeNoDuplicateRecoveryTests(unittest.TestCase):
    def test_recovery_and_all_import_ledgers_are_idempotent_without_skipping_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RuntimeStore(Path(tmp) / "runtime")
            store.create_run({"runtime_run_id": "r", "workspace_id": "w", "trace_id": "t", "status": "RUNNING"})
            candidate = synthesize_candidate({"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r",
                                              "generation_id": "g1", "payload": {"x": 1}})
            imported_candidate = store.import_candidate(candidate.envelope)
            self.assertEqual(store.import_candidate(candidate.envelope), imported_candidate)

            execution = {"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1",
                         "execution_id": "exec-1", "status": "SUCCEEDED"}
            imported_execution = store.import_execution_result(execution)
            self.assertEqual(store.import_execution_result(execution), imported_execution)
            source = {"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1"}
            imported_cost = store.import_cost("cost-1", 0.25, source)
            self.assertEqual(store.import_cost("cost-1", 0.25, source), imported_cost)

            commit = store.record_generation_commit({"runtime_run_id": "r", "generation_id": "g1",
                                                      "snapshot_digest": "snap", "complete": True,
                                                      "closed": True, "status": "COMPLETED"})
            self.assertEqual(store.record_generation_commit(commit), commit)
            first_plan = build_recovery_plan(store, expected={"snapshot_digest": "snap"})
            second_plan = build_recovery_plan(store, expected={"snapshot_digest": "snap"})
            self.assertEqual(first_plan, second_plan)
            self.assertEqual(first_plan.next_generation_id, "g2")
            self.assertEqual(first_plan.idempotency_key, "r+g1")
            self.assertEqual(len(store.state["candidates"]), 1)
            self.assertEqual(len(store.state["executions"]), 1)
            self.assertEqual(len(store.state["costs"]), 1)
            self.assertEqual(len(store.state["commits"]), 1)

            changed = dict(execution, status="FAILED", error="source drift")
            with self.assertRaises(RuntimeStoreError):
                store.import_execution_result(changed)


if __name__ == "__main__":
    unittest.main()
