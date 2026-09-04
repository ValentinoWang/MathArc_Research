import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.run_store import RuntimeStore, RuntimeStoreError


class RuntimeImportTests(unittest.TestCase):
    def test_candidate_execution_and_cost_imports_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RuntimeStore(Path(tmp) / "runtime")
            candidate = {"candidate_id": "c1", "workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1", "payload_digest": "p"}
            self.assertEqual(store.import_candidate(candidate), store.import_candidate(dict(candidate)))
            result = {"execution_id": "e1", "workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1", "worker_id": "worker", "status": "SUCCEEDED", "result_digest": "d"}
            store.import_execution_result(result)
            store.import_execution_result(dict(result))
            source = {"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1"}
            store.import_cost("cost-1", 1.5, source)
            store.import_cost("cost-1", 1.5, source)
            self.assertEqual(len(store.events), 3)
            altered = dict(candidate); altered["source_digest"] = "changed"
            with self.assertRaises(RuntimeStoreError): store.import_candidate(altered)


if __name__ == "__main__": unittest.main()
