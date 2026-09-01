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
A5_CONTRACT = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A5-problem-intelligence-v0-release/acceptance-contract.md"
A5_BINDING = ROOT / "acceptance/human/A5-problem-intelligence-v0-release/binding.md"


class SourceLevelReleaseDecisionTests(unittest.TestCase):
    def load(self) -> dict:
        return json.loads(A5_EVIDENCE.read_text(encoding="utf-8"))

    def test_release_decision_pins_the_accepted_q1_artifacts(self) -> None:
        evidence = self.load()
        policy = CalibrationDisclosurePolicy.from_dict(
            json.loads(Q1_POLICY.read_text(encoding="utf-8"))
        )
        self.assertFalse(policy.public_release_allowed)
        self.assertEqual("EV-Q1-ACCEPTED-3", evidence["consumed_evidence"][0])
        self.assertEqual(
            hashlib.sha256(Q1_EVIDENCE.read_bytes()).hexdigest(),
            evidence["source_identity"]["q1_evidence_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(Q1_POLICY.read_bytes()).hexdigest(),
            evidence["source_identity"]["q1_policy_fixture_sha256"],
        )
        self.assertEqual(policy.policy_digest_sha256, evidence["source_identity"]["q1_policy_digest_sha256"])
        self.assertEqual(
            "d7ac4010b960bacfb601a0670a0c1c45ef7da0be049839fd551b8a69d5b79bc7",
            evidence["source_identity"]["q1_implementation_sha256"],
        )
        self.assertEqual(
            "fbd26cced684b3ffe9489d18aeb7fd687e394490209106f73c75cc767fa0e846",
            evidence["source_identity"]["q1_protected_test_sha256"],
        )

    def test_release_evidence_has_only_the_locked_schema_and_artifacts(self) -> None:
        evidence = self.load()
        self.assertEqual(
            {
                "evidence_id",
                "task_id",
                "consumed_evidence",
                "source_identity",
                "release_scope",
                "release_decision",
                "delivery_requirements",
                "acceptance_record",
                "proposed_state",
                "unverified_items",
            },
            set(evidence),
        )
        self.assertEqual("EV-A5-ACCEPTED-2", evidence["evidence_id"])
        self.assertEqual("A5", evidence["task_id"])
        self.assertEqual("ACCEPTED", evidence["proposed_state"])
        expected_runs = {
            "machine_acceptance_run": ("machine/static", "machine_acceptance_result_sha256"),
            "human_acceptance_result": ("human", "human_acceptance_result_sha256"),
            "release_review_run": ("release", "release_review_result_sha256"),
        }
        contract_hash = hashlib.sha256(A5_CONTRACT.read_bytes()).hexdigest()
        binding_hash = hashlib.sha256(A5_BINDING.read_bytes()).hexdigest()
        for key, (expected_lane, result_hash_key) in expected_runs.items():
            referenced = ROOT / evidence["acceptance_record"][key]
            self.assertTrue(referenced.is_file(), key)
            self.assertEqual(
                hashlib.sha256(referenced.read_bytes()).hexdigest(),
                evidence["acceptance_record"][result_hash_key],
                key,
            )
            result = referenced.read_text(encoding="utf-8")
            self.assertIn("- Task ID: A5-problem-intelligence-v0-release", result)
            self.assertIn(f"- Lane: {expected_lane}", result)
            self.assertIn("- Status: PASS", result)
            self.assertIn(
                "- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/"
                "acceptance-fragments/A5-problem-intelligence-v0-release/acceptance-contract.md",
                result,
            )
            self.assertIn(f"- Contract SHA-256: {contract_hash}", result)
            if expected_lane == "human":
                self.assertIn(f"- Binding SHA-256: {binding_hash}", result)

    def test_release_scope_is_limited_to_repository_source_delivery(self) -> None:
        evidence = self.load()
        self.assertEqual("ACCEPTED_SOURCE_SCOPE", evidence["release_decision"]["status"])
        self.assertTrue(evidence["release_decision"]["github_source_delivery_authorized"])
        self.assertFalse(evidence["release_decision"]["mathematical_result_publication_authorized"])
        self.assertFalse(evidence["release_decision"]["q1_public_release_allowed"])
        self.assertEqual("union-closed", evidence["release_scope"]["topic_id"])
        self.assertEqual(3, evidence["release_scope"]["fixed_case_count"])
        self.assertEqual(
            [
                "accepted repository source, tests, SSOT records, and acceptance evidence",
                "GitHub main ref delivery after the A5 decision commit",
            ],
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

    def test_delivery_claim_requires_a_remote_ref_readback(self) -> None:
        evidence = self.load()
        self.assertEqual(
            "git ls-remote origin refs/heads/main must equal the final local HEAD after push",
            evidence["delivery_requirements"]["remote_ref_readback"],
        )
        self.assertFalse(evidence["delivery_requirements"]["pre_push_delivery_claim"])


if __name__ == "__main__":
    unittest.main()
