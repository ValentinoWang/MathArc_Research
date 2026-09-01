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


def _validate_a5_lifecycle(q1_evidence: dict, a5_evidence: dict) -> None:
    if a5_evidence["proposed_state"] == "BLOCKED":
        if (
            q1_evidence["evidence_id"] != "EV-Q1-REOPENED-3"
            or q1_evidence["acceptance_self_check"] != "blocked"
            or q1_evidence["proposed_state"] != "BLOCKED"
            or q1_evidence["acceptance_record"]["status"] != "BLOCKED_UPSTREAM_R1"
            or a5_evidence["acceptance_record"]["status"] != "BLOCKED_UPSTREAM_Q1"
            or a5_evidence["release_decision"]["status"] != "BLOCKED_UPSTREAM_Q1"
            or a5_evidence["release_decision"]["github_source_delivery_authorized"]
        ):
            raise ValueError("A5 blocked lifecycle is inconsistent with current Q1")
    elif a5_evidence["proposed_state"] == "ACCEPTED":
        remote_main = a5_evidence["source_identity"]["accepted_upstream_remote_main"]
        if (
            q1_evidence["evidence_id"] != "EV-Q1-ACCEPTED-4"
            or q1_evidence["acceptance_self_check"] != "pass"
            or q1_evidence["proposed_state"] != "ACCEPTED"
            or q1_evidence["acceptance_record"]["status"] != "ACCEPTED"
            or a5_evidence["evidence_id"] != "EV-A5-ACCEPTED-3"
            or a5_evidence["acceptance_record"]["status"] != "ACCEPTED"
            or a5_evidence["release_decision"]["status"] != "ACCEPTED_SOURCE_SCOPE"
            or not a5_evidence["release_decision"]["github_source_delivery_authorized"]
            or not isinstance(remote_main, str)
            or len(remote_main) != 40
            or any(character not in "0123456789abcdef" for character in remote_main)
            or a5_evidence["source_identity"]["implementation_base"] != remote_main
        ):
            raise ValueError("A5 accepted lifecycle is not bound to accepted Q1 and remote main")
    else:
        raise ValueError("A5 proposed_state must be BLOCKED or ACCEPTED")
    if a5_evidence["consumed_evidence"] != [q1_evidence["evidence_id"]]:
        raise ValueError("A5 consumed evidence does not match current Q1")


class SourceLevelReleaseDecisionTests(unittest.TestCase):
    def load(self) -> dict:
        return json.loads(A5_EVIDENCE.read_text(encoding="utf-8"))

    def test_release_decision_pins_the_accepted_q1_artifacts(self) -> None:
        evidence = self.load()
        q1_evidence = json.loads(Q1_EVIDENCE.read_text(encoding="utf-8"))
        policy = CalibrationDisclosurePolicy.from_dict(
            json.loads(Q1_POLICY.read_text(encoding="utf-8"))
        )
        self.assertFalse(policy.public_release_allowed)
        _validate_a5_lifecycle(q1_evidence, evidence)
        if evidence["proposed_state"] != "ACCEPTED":
            self.assertEqual("BLOCKED", evidence["proposed_state"])
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
            hashlib.sha256((ROOT / "tests/test_v02_calibration_disclosure.py").read_bytes()).hexdigest(),
            evidence["source_identity"]["q1_protected_test_sha256"],
        )

    def test_a5_acceptance_rejects_blocked_q1_even_when_downstream_labels_are_promoted(self) -> None:
        q1_evidence = json.loads(Q1_EVIDENCE.read_text(encoding="utf-8"))
        a5_evidence = self.load()
        a5_evidence["evidence_id"] = "EV-A5-ACCEPTED-3"
        a5_evidence["proposed_state"] = "ACCEPTED"
        a5_evidence["acceptance_record"]["status"] = "ACCEPTED"
        a5_evidence["release_decision"]["status"] = "ACCEPTED_SOURCE_SCOPE"
        a5_evidence["release_decision"]["github_source_delivery_authorized"] = True
        a5_evidence["source_identity"]["accepted_upstream_remote_main"] = "a" * 40
        a5_evidence["source_identity"]["implementation_base"] = "a" * 40
        with self.assertRaisesRegex(ValueError, "not bound to accepted Q1"):
            _validate_a5_lifecycle(q1_evidence, a5_evidence)

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
        if evidence["proposed_state"] != "ACCEPTED":
            self.assertEqual("EV-A5-REOPENED-3", evidence["evidence_id"])
            self.assertEqual("BLOCKED", evidence["proposed_state"])
            self.assertEqual("BLOCKED_UPSTREAM_Q1", evidence["acceptance_record"]["status"])
            return

        self.assertEqual("EV-A5-ACCEPTED-3", evidence["evidence_id"])
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
        expected_status = "ACCEPTED_SOURCE_SCOPE" if evidence["proposed_state"] == "ACCEPTED" else "BLOCKED_UPSTREAM_Q1"
        self.assertEqual(expected_status, evidence["release_decision"]["status"])
        self.assertEqual(
            evidence["proposed_state"] == "ACCEPTED",
            evidence["release_decision"]["github_source_delivery_authorized"],
        )
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
