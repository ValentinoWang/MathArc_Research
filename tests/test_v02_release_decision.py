from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from matharc.v02.calibration_disclosure import CalibrationDisclosurePolicy


ROOT = Path(__file__).parents[1]
Q1_POLICY = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/q1-fixtures/uncalibrated-disclosure-policy.json"
Q1_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json"
Q1_HISTORICAL_EVIDENCE = (
    ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/history/Q1-accepted-1.json"
)
A5_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/A5.json"


class SourceLevelReleaseDecisionTests(unittest.TestCase):
    def load(self) -> dict:
        return json.loads(A5_EVIDENCE.read_text(encoding="utf-8"))

    def test_release_decision_pins_historical_q1_artifacts(self) -> None:
        evidence = self.load()
        policy = CalibrationDisclosurePolicy.from_dict(
            json.loads(Q1_POLICY.read_text(encoding="utf-8"))
        )
        self.assertFalse(policy.public_release_allowed)
        self.assertEqual("EV-Q1-ACCEPTED-1", evidence["consumed_evidence"][0])
        self.assertEqual(
            hashlib.sha256(Q1_HISTORICAL_EVIDENCE.read_bytes()).hexdigest(),
            evidence["source_identity"]["q1_evidence_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(Q1_POLICY.read_bytes()).hexdigest(),
            evidence["source_identity"]["q1_policy_fixture_sha256"],
        )
        self.assertEqual(policy.policy_digest_sha256, evidence["source_identity"]["q1_policy_digest_sha256"])
        self.assertEqual(
            "b4988a67c0a13918a0ce775c01be687423822c8e069c1ebb03a09c4c9b4c6535",
            evidence["source_identity"]["q1_implementation_sha256"],
        )
        self.assertEqual(
            "0a55a78158faa4f28b47d02b983fbdbd32217155b8d8ca17e659646dd7d7ec9d",
            evidence["source_identity"]["q1_protected_test_sha256"],
        )

    def test_release_evidence_is_fail_closed_when_q1_is_reopened(self) -> None:
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
                "invalidation",
                "proposed_state",
                "unverified_items",
            },
            set(evidence),
        )
        self.assertEqual("EV-A5-REOPENED-2", evidence["evidence_id"])
        self.assertEqual("A5", evidence["task_id"])
        self.assertEqual("BLOCKED", evidence["proposed_state"])
        self.assertEqual("Q1-invalidated-by-R1-review-contract-v4", evidence["invalidation"]["cause"])

    def test_release_scope_is_limited_to_repository_source_delivery(self) -> None:
        evidence = self.load()
        self.assertEqual("BLOCKED_UPSTREAM_R1_REVIEW", evidence["release_decision"]["status"])
        self.assertFalse(evidence["release_decision"]["github_source_delivery_authorized"])
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
