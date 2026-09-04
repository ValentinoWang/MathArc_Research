import unittest

from matharc.v02.runtime.synthesis import synthesize_candidate
from matharc.v02.runtime.verification import (
    VerificationStatus,
    convert_receipt_to_evidence,
    independent_replay,
)


class VerificationConvergenceTests(unittest.TestCase):
    def test_independent_pass_converges_to_formal_evidence(self):
        candidate = synthesize_candidate(
            {"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r", "generation_id": "g1",
             "payload": {"proposition": "P", "quantifier": "forall", "scope": "finite", "objects": ["x"]}},
            claim_ids=("claim-1",),
        )
        seen = []
        plan, receipt = independent_replay(
            candidate, verifier_id="verifier-v1", implementation_id="worker-v1",
            environment={"mode": "clean", "network": False, "candidate_id": candidate.candidate_id},
            replay=lambda payload: seen.append(payload) or {"passed": True, "certificate": "cert-1"},
        )
        evidence = convert_receipt_to_evidence(candidate, receipt, independence_group="lane-b")

        self.assertEqual(receipt.status, VerificationStatus.PASS)
        self.assertTrue(receipt.independent)
        self.assertEqual(seen[0], candidate.payload)
        self.assertEqual(plan.idempotency_key, f"{candidate.candidate_id}+{plan.replay_digest}")
        self.assertEqual(evidence.status.value, "ACCEPTED")
        self.assertEqual(evidence.claim_ids, ("claim-1",))
        self.assertEqual(evidence.verifier, "verifier-v1")
        self.assertEqual(evidence.independence_group, "lane-b")
        self.assertTrue(evidence.replay_command.startswith("replay:"))

    def test_transient_verifier_failure_retries_once_then_converges(self):
        candidate = synthesize_candidate({"workspace_id": "w", "trace_id": "t", "runtime_run_id": "r",
                                           "generation_id": "g1", "payload": {"answer": 42}})
        attempts = 0

        def replay(_payload):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("verifier unavailable")
            return True

        _, receipt = independent_replay(candidate, verifier_id="v", implementation_id="impl",
                                        replay=replay, max_retries=1)
        self.assertEqual(receipt.status, VerificationStatus.PASS)
        self.assertEqual(receipt.attempts, 2)
        self.assertEqual(attempts, 2)


if __name__ == "__main__":
    unittest.main()
