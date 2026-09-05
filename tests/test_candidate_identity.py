import unittest
from matharc.v02.runtime.synthesis import ExplorationCandidate, SynthesisError, synthesize_candidate

class CandidateIdentityTests(unittest.TestCase):
    def test_material_inputs_change_identity(self):
        base = {"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"x":1}}
        self.assertNotEqual(synthesize_candidate(base).candidate_id, synthesize_candidate({**base, "payload":{"x":2}}).candidate_id)

    def test_provenance_digest_round_trip_and_tamper_rejection(self):
        candidate = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r",
                                          "generation_id":"g","payload":{"x":1}}, candidate_origin="worker")
        restored = ExplorationCandidate.from_dict(candidate.to_dict())
        self.assertEqual(restored.provenance_digest, candidate.provenance_digest)
        tampered = candidate.to_dict()
        tampered["provenance"]["workspace_id"] = "other"
        with self.assertRaises(SynthesisError):
            ExplorationCandidate.from_dict(tampered)

if __name__ == "__main__": unittest.main()
