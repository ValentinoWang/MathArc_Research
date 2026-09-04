import unittest
from matharc.v02.runtime.synthesis import SynthesisError, synthesize_candidate

class CandidateSynthesisTests(unittest.TestCase):
    def test_output_is_candidate_and_not_evidence(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"value": 1}})
        self.assertEqual(c.candidate_kind, "exploration")
        self.assertNotIn("evidence_id", c.provenance)

    def test_unknown_candidate_kind_cannot_be_marked_as_proof(self):
        with self.assertRaises(SynthesisError):
            synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g"}, candidate_kind="formal")

if __name__ == "__main__": unittest.main()
