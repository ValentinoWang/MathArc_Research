import unittest
from matharc.v02.runtime.synthesis import synthesize_candidate
from matharc.v02.runtime.verification import *

class EvidenceInvalidationTests(unittest.TestCase):
    def test_identity_drift_marks_evidence_stale(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"x":1}}, claim_ids=("C",))
        _, receipt = independent_replay(c, verifier_id="v", implementation_id="impl", replay=lambda _: True)
        e = convert_receipt_to_evidence(c, receipt); ledger = EvidenceInvalidator(); ledger.register(e, c)
        changed = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"x":2}}, claim_ids=("C",))
        self.assertFalse(ledger.check(e, changed)); self.assertEqual(e.status.value, "STALE")

    def test_payload_drift_marks_evidence_stale(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"x":1}}, claim_ids=("C",))
        _, receipt = independent_replay(c, verifier_id="v", implementation_id="impl", replay=lambda _: True)
        e = convert_receipt_to_evidence(c, receipt); ledger = EvidenceInvalidator(); ledger.register(e, c)
        c.payload["x"] = 2
        self.assertFalse(ledger.check(e, c)); self.assertEqual(e.status.value, "STALE")

if __name__ == "__main__": unittest.main()
