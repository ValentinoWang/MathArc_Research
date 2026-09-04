import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.run_store import RuntimeStore


class RuntimeLateResultTests(unittest.TestCase):
    def test_late_result_is_quarantined_without_mutating_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RuntimeStore(Path(tmp) / "runtime")
            commit = {"runtime_run_id": "r", "generation_id": "g1", "complete": True, "status": "COMPLETED"}
            original = store.record_generation_commit(commit)
            store.record_late_result({"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1", "execution_id": "late", "status": "SUCCEEDED"})
            self.assertEqual(store.state["commits"][0], original)
            self.assertEqual(store.state["late_results"][0]["disposition"], "LATE_RESULT_QUARANTINED")


if __name__ == "__main__": unittest.main()
