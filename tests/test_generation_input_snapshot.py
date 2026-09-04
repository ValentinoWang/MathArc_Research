import unittest

from matharc.v02.runtime.generation import GenerationInputSnapshot


class GenerationInputSnapshotTests(unittest.TestCase):
    def test_snapshot_freezes_all_input_digests(self):
        source = {"trace": 1}
        snapshot = GenerationInputSnapshot.from_inputs(
            workspace_id="w", trace_id="t", runtime_run_id="r", generation_id="g",
            trace=source, contract={"version": 1}, agenda=["a"], worker_specs=(), tool_registry={}
        )
        source["trace"] = 2
        self.assertNotEqual(snapshot.trace_digest, "")
        self.assertEqual(GenerationInputSnapshot.from_dict(snapshot.to_dict()), snapshot)
        with self.assertRaises(Exception):
            GenerationInputSnapshot.from_dict({**snapshot.to_dict(), "unknown": 1})


if __name__ == "__main__":
    unittest.main()
