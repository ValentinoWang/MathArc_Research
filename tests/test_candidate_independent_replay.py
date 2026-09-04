import unittest
from matharc.v02.runtime.synthesis import synthesize_candidate
from matharc.v02.runtime.verification import ReplayPlan, VerificationError, independent_replay, VerificationStatus

class CandidateIndependentReplayTests(unittest.TestCase):
    def test_same_implementation_is_rejected(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}})
        with self.assertRaises(VerificationError): ReplayPlan.for_candidate(c, verifier_id="impl", implementation_id="impl")
    def test_clean_replay_passes(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}})
        _, receipt = independent_replay(c, verifier_id="v", implementation_id="impl", replay=lambda _: True)
        self.assertEqual(receipt.status, VerificationStatus.PASS)

if __name__ == "__main__": unittest.main()
