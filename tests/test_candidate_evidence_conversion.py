import unittest
from matharc.v02.runtime.synthesis import synthesize_candidate
from matharc.v02.runtime.verification import *

class CandidateEvidenceConversionTests(unittest.TestCase):
    def test_only_pass_receipt_converts(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}}, claim_ids=("C",))
        _, receipt = independent_replay(c, verifier_id="v", implementation_id="impl", replay=lambda _: True)
        self.assertEqual(convert_receipt_to_evidence(c, receipt).status.value, "ACCEPTED")
        bad = VerifierReceipt(c.candidate_id, receipt.replay_digest, VerificationStatus.FAIL, "v", True)
        with self.assertRaises(VerificationError): convert_receipt_to_evidence(c, bad)

if __name__ == "__main__": unittest.main()
