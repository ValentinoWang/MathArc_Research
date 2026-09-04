import unittest

from matharc.v02.runtime.synthesis import synthesize_candidate
from matharc.v02.runtime.verification import (
    ScopeBindingError,
    VerificationError,
    VerificationStatus,
    VerifierReceipt,
    bind_candidate_scope,
    convert_receipt_to_evidence,
    independent_replay,
    ReplayPlan,
)


def _candidate():
    return synthesize_candidate(
        {"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1",
         "payload": {"proposition": "P", "quantifier": "forall", "scope": "finite", "objects": ["x"]}},
        claim_ids=("claim-1",),
    )


class VerificationNegativePathTests(unittest.TestCase):
    def test_tampered_payload_is_rejected_before_replay(self):
        candidate = _candidate()
        candidate.payload["proposition"] = "tampered"
        with self.assertRaises(VerificationError):
            independent_replay(candidate, verifier_id="v", implementation_id="impl", replay=lambda _: True)

    def test_scope_and_object_expansion_are_rejected(self):
        candidate = _candidate()
        with self.assertRaises(ScopeBindingError):
            bind_candidate_scope(candidate, claim_id="claim-1", proposition="P", quantifier="exists",
                                 objects=("x",), scope="finite")
        with self.assertRaises(ScopeBindingError):
            bind_candidate_scope(candidate, claim_id="claim-1", proposition="P", quantifier="forall",
                                 objects=("x", "y"), scope="finite")
        with self.assertRaises(ScopeBindingError):
            bind_candidate_scope(candidate, claim_id="claim-1", proposition="P", quantifier="forall",
                                 objects=("x",), scope="global")

    def test_non_independent_and_failed_receipts_cannot_become_evidence(self):
        candidate = _candidate()
        non_independent = VerifierReceipt(candidate.candidate_id, "replay", VerificationStatus.PASS, "worker", False)
        with self.assertRaises(VerificationError):
            convert_receipt_to_evidence(candidate, non_independent)
        failed = VerifierReceipt(candidate.candidate_id, "replay", VerificationStatus.FAIL, "verifier", True,
                                 failure_class="VERIFICATION_FAILED")
        with self.assertRaises(VerificationError):
            convert_receipt_to_evidence(candidate, failed)

    def test_same_implementation_and_dirty_environment_are_not_independent(self):
        candidate = _candidate()
        with self.assertRaises(VerificationError):
            ReplayPlan.for_candidate(candidate, verifier_id="same", implementation_id="same")
        with self.assertRaises(VerificationError):
            ReplayPlan.for_candidate(candidate, verifier_id="v", implementation_id="impl",
                                     environment={"mode": "developer", "candidate_id": candidate.candidate_id})
        with self.assertRaises(VerificationError):
            ReplayPlan.for_candidate(candidate, verifier_id="v", implementation_id="impl",
                                     environment={"mode": "clean", "candidate_id": "other"})
        with self.assertRaises(VerificationError):
            ReplayPlan.for_candidate(candidate, verifier_id="v", implementation_id="impl",
                                     environment={"mode": "clean", "network": True,
                                                  "candidate_id": candidate.candidate_id})

    def test_unknown_replay_result_fails_closed(self):
        candidate = _candidate()
        _, receipt = independent_replay(candidate, verifier_id="v", implementation_id="impl",
                                        replay=lambda _: None)
        self.assertEqual(receipt.status, VerificationStatus.RETRYABLE_FAILURE)
        with self.assertRaises(VerificationError):
            convert_receipt_to_evidence(candidate, receipt)

    def test_receipt_must_bind_candidate_digest_and_replay_result_digests(self):
        candidate = _candidate()
        forged = VerifierReceipt(candidate.candidate_id, "forged", VerificationStatus.PASS,
                                 "verifier", True, "0" * 64)
        with self.assertRaises(VerificationError):
            convert_receipt_to_evidence(candidate, forged)

        _, receipt = independent_replay(candidate, verifier_id="v", implementation_id="impl",
                                        replay=lambda _: True)
        tampered = VerifierReceipt(candidate.candidate_id, receipt.replay_digest,
                                   VerificationStatus.PASS, receipt.verifier_id, True,
                                   "not-a-digest", candidate_identity_digest=candidate.envelope.identity_digest)
        with self.assertRaises(VerificationError):
            convert_receipt_to_evidence(candidate, tampered)

        replay_tampered = VerifierReceipt(candidate.candidate_id, "f" * 64,
                                          VerificationStatus.PASS, receipt.verifier_id, True,
                                          receipt.result_digest,
                                          candidate_identity_digest=candidate.envelope.identity_digest,
                                          receipt_binding_digest=receipt.receipt_binding_digest)
        with self.assertRaises(VerificationError):
            convert_receipt_to_evidence(candidate, replay_tampered)

    def test_timeout_is_terminal_failure_and_not_promoted(self):
        candidate = _candidate()
        _, receipt = independent_replay(candidate, verifier_id="v", implementation_id="impl",
                                        replay=lambda _: (_ for _ in ()).throw(TimeoutError("slow")))
        self.assertEqual(receipt.status, VerificationStatus.TIMED_OUT)
        with self.assertRaises(VerificationError):
            convert_receipt_to_evidence(candidate, receipt)


if __name__ == "__main__":
    unittest.main()
