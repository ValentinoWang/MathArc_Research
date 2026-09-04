import unittest
from matharc.v02.runtime.synthesis import synthesize_candidate

class CandidateIdentityTests(unittest.TestCase):
    def test_material_inputs_change_identity(self):
        base = {"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"x":1}}
        self.assertNotEqual(synthesize_candidate(base).candidate_id, synthesize_candidate({**base, "payload":{"x":2}}).candidate_id)

if __name__ == "__main__": unittest.main()
