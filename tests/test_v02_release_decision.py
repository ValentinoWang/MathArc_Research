from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from matharc.v02.calibration_disclosure import CalibrationDisclosurePolicy


ROOT = Path(__file__).parents[1]
Q1_POLICY = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/q1-fixtures/uncalibrated-disclosure-policy.json"
Q1_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json"
A5_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/A5.json"
Q1_IMPLEMENTATION = ROOT / "matharc/v02/calibration_disclosure.py"
PROTECTED_TEST = ROOT / "tests/test_v02_calibration_disclosure.py"
Q1_NODE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/Q1.json"
Q1_FINAL_LEDGER = ROOT / (
    "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
    "Q1-calibration-disclosure/reviews/q1-final-reconciliation-20260901/"
    "q1-final-acceptance-ledger.json"
)
Q1_EXECUTION_CONTRACT = ROOT / (
    "agents-results/2026-08-31/problem-intelligence-plane/.ssot/"
    "execution-contracts/Q1.json"
)
Q1_FROZEN_INPUTS = ROOT / (
    "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
    "Q1-calibration-disclosure/reviews/q1-final-reconciliation-20260901/"
    "frozen-inputs-v5.json"
)
Q1_IDENTITY_REVIEW = ROOT / (
    "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
    "Q1-calibration-disclosure/reviews/q1-final-reconciliation-20260901/"
    "final-reports-v5/identity-contract-final.md"
)
Q1_POLICY_REVIEW = ROOT / (
    "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
    "Q1-calibration-disclosure/reviews/q1-final-reconciliation-20260901/"
    "final-reports-v5/policy-boundary-final.md"
)

# The blocked A5 record must remain byte-bound to the current Q1 identity.
EXPECTED_Q1_IDENTITY = {
    "implementation_base": "20d41af66b03d037b7e390ce31800fcc9d573a3e",
    "q1_evidence_sha256": "4f0dec79412813e94ba64a005ab3990b456578a71b8325fffb51a9c8a0fd5e8f",
    "q1_policy_fixture_sha256": "566533a91201ee353ef80efd13e7e039e21692b4ef5334a8a55e940cccf58064",
    "q1_policy_digest_sha256": "05f843c5c4c3956c50b211ed7e41dd4e05e2705fa74759ba8d4b4e2bb0c5748c",
    "q1_implementation_sha256": "1a56ac0e25023e7103adc4c18e9ce50157bb6f58dee57247aba22ada5a352b50",
    "q1_node_sha256": "851b6ac813282d7b5df64ec09dd548e31f0056a272ccba960d59fc2a3b373ab8",
    "q1_execution_contract_sha256": "bea478adc7da2f5f21c01990a2bcf6820ac4b469f7a131d1e9552f527dd7c31b",
    "q1_frozen_inputs_sha256": "e0f14cd0ff4074cf745d14b23013dedd2e64683379b116c9d145b4209142e1d9",
    "q1_final_ledger_sha256": "53bd3643f9dafe03aa821a8fc61678f71e804b371b09b86a3435b09430e739b4",
    "q1_identity_review_sha256": "87da2960befb8b50514cdad1d17cb569a60e4745c0d52d5478ee3558fd9f63de",
    "q1_policy_review_sha256": "91c33fdcabdf3c74ea542b336d2ecd52ff3d4d6c3e04368911c405679b078f19",
}


class SourceLevelReleaseDecisionTests(unittest.TestCase):
    def load(self) -> dict:
        return json.loads(A5_EVIDENCE.read_text(encoding="utf-8"))

    def assert_q1_identity(self, source_identity: dict) -> None:
        # The protected test is an external input to this test, so its digest
        # must be checked against evidence rather than frozen in this file.
        self.assertIn("q1_protected_test_sha256", source_identity)
        stable_identity = {
            key: value
            for key, value in source_identity.items()
            if key != "q1_protected_test_sha256"
        }
        self.assertEqual(EXPECTED_Q1_IDENTITY, stable_identity)

    def test_release_decision_pins_current_blocked_q1_artifacts(self) -> None:
        evidence = self.load()
        policy = CalibrationDisclosurePolicy.from_dict(
            json.loads(Q1_POLICY.read_text(encoding="utf-8"))
        )
        self.assertFalse(policy.public_release_allowed)
        self.assertEqual(["EV-Q1-BLOCKED-1"], evidence["consumed_evidence"])
        observed = {
            "implementation_base": "20d41af66b03d037b7e390ce31800fcc9d573a3e",
            "q1_evidence_sha256": hashlib.sha256(Q1_EVIDENCE.read_bytes()).hexdigest(),
            "q1_policy_fixture_sha256": hashlib.sha256(Q1_POLICY.read_bytes()).hexdigest(),
            "q1_policy_digest_sha256": policy.policy_digest_sha256,
            "q1_implementation_sha256": hashlib.sha256(Q1_IMPLEMENTATION.read_bytes()).hexdigest(),
            "q1_protected_test_sha256": hashlib.sha256(PROTECTED_TEST.read_bytes()).hexdigest(),
            "q1_node_sha256": hashlib.sha256(Q1_NODE.read_bytes()).hexdigest(),
            "q1_execution_contract_sha256": hashlib.sha256(
                Q1_EXECUTION_CONTRACT.read_bytes()
            ).hexdigest(),
            "q1_frozen_inputs_sha256": hashlib.sha256(Q1_FROZEN_INPUTS.read_bytes()).hexdigest(),
            "q1_final_ledger_sha256": hashlib.sha256(Q1_FINAL_LEDGER.read_bytes()).hexdigest(),
            "q1_identity_review_sha256": hashlib.sha256(
                Q1_IDENTITY_REVIEW.read_bytes()
            ).hexdigest(),
            "q1_policy_review_sha256": hashlib.sha256(Q1_POLICY_REVIEW.read_bytes()).hexdigest(),
        }
        self.assert_q1_identity(observed)
        self.assert_q1_identity(evidence["source_identity"])
        protected_test_sha256 = hashlib.sha256(PROTECTED_TEST.read_bytes()).hexdigest()
        self.assertEqual(
            protected_test_sha256,
            evidence["source_identity"]["q1_protected_test_sha256"],
        )
        self.assertEqual(
            protected_test_sha256,
            json.loads(Q1_EVIDENCE.read_text(encoding="utf-8"))["source_identity"][
                "protected_test_sha256"
            ],
        )

        node = json.loads(Q1_NODE.read_text(encoding="utf-8"))
        contract = json.loads(Q1_EXECUTION_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual("Q1", node["node_id"])
        self.assertEqual("BLOCKED", node["execution_state"])
        self.assertEqual("Q1", contract["node_id"])
        self.assertEqual(node["semantic_key"], contract["semantic_key"])
        self.assertEqual(node["hard_dependencies"], contract["hard_dependencies"])
        self.assertEqual(node["read_set"], contract["read_set"])
        self.assertEqual(node["write_set"], contract["write_set"])
        self.assertEqual(node["evidence_outputs"], contract["evidence_outputs"])

        ledger = json.loads(Q1_FINAL_LEDGER.read_text(encoding="utf-8"))
        self.assertEqual("PASS", ledger["status"])
        self.assertNotEqual(EXPECTED_Q1_IDENTITY["q1_node_sha256"], ledger["q1_node"]["sha256"])

    def test_release_decision_rejects_coordinated_q1_identity_tampering(self) -> None:
        tampered = dict(EXPECTED_Q1_IDENTITY)
        # Simulate an attacker updating both Q1 and A5's mutable pointer.
        tampered["q1_implementation_sha256"] = hashlib.sha256(b"coordinated drift").hexdigest()
        with self.assertRaises(AssertionError):
            self.assert_q1_identity(tampered)

    def test_release_evidence_has_only_current_acceptance_fields(self) -> None:
        evidence = self.load()
        self.assertEqual(
            {
                "evidence_id", "task_id", "consumed_evidence", "source_identity", "release_scope",
                "release_decision", "delivery_requirements", "acceptance_record", "proposed_state", "unverified_items",
            },
            set(evidence),
        )
        self.assertEqual("EV-A5-BLOCKED-1", evidence["evidence_id"])
        self.assertEqual("A5", evidence["task_id"])
        self.assertEqual("BLOCKED", evidence["proposed_state"])

    def test_release_scope_is_limited_to_repository_source_delivery(self) -> None:
        evidence = self.load()
        self.assertEqual("BLOCKED_UPSTREAM_Q1", evidence["release_decision"]["status"])
        self.assertFalse(evidence["release_decision"]["github_source_delivery_authorized"])
        self.assertFalse(evidence["release_decision"]["mathematical_result_publication_authorized"])
        self.assertFalse(evidence["release_decision"]["q1_public_release_allowed"])
        self.assertEqual("source", evidence["release_scope"]["evidence_level"])
        self.assertEqual("union-closed", evidence["release_scope"]["topic_id"])
        self.assertEqual(3, evidence["release_scope"]["fixed_case_count"])
        self.assertEqual(
            [],
            evidence["release_scope"]["allowed"],
        )
        self.assertEqual(
            [
                "mathematical proof or theorem acceptance",
                "live external literature retrieval or open-status confirmation",
                "novelty acceptance",
                "calibration quality, accuracy, recall, statistical performance, or generalization",
                "production, deployed-service, device, or monitoring evidence",
                "public communication of any research conclusion",
            ],
            evidence["release_scope"]["prohibited"],
        )

    def test_fresh_machine_human_and_release_records_are_byte_bound(self) -> None:
        evidence = self.load()
        for key in ("machine", "human", "release_review"):
            selected = evidence["acceptance_record"][key]
            path = ROOT / selected["result_path"]
            self.assertTrue(path.is_file(), key)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), selected["result_sha256"], key)
            self.assertEqual("INVALIDATED", selected["status"], key)

    def test_delivery_claim_requires_a_remote_ref_readback(self) -> None:
        evidence = self.load()
        self.assertEqual("git ls-remote origin refs/heads/main must equal the final local HEAD after push", evidence["delivery_requirements"]["remote_ref_readback"])
        self.assertFalse(evidence["delivery_requirements"]["pre_push_delivery_claim"])


if __name__ == "__main__":
    unittest.main()
