import unittest
from matharc.v02.runtime.scheduler import GenerationInputSnapshot


class RuntimeParallelContractTests(unittest.TestCase):
    def test_snapshot_is_frozen_and_digest_changes_with_input(self):
        snapshot = GenerationInputSnapshot.from_inputs(workspace_id="w", trace_id="t", runtime_run_id="r", generation_id="g1", trace={"value": 1}, contract={}, agenda={}, worker_specs=(), tool_registry={}, source_payload={"problem": {"value": 1}})
        other = GenerationInputSnapshot.from_inputs(workspace_id="w", trace_id="t", runtime_run_id="r", generation_id="g1", trace={"value": 2}, contract={}, agenda={}, worker_specs=(), tool_registry={}, source_payload={"problem": {"value": 2}})
        self.assertTrue(snapshot.snapshot_digest)
        self.assertNotEqual(snapshot.snapshot_digest, other.snapshot_digest)


if __name__ == "__main__":
    unittest.main()
