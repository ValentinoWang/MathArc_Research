from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from matharc.v02.calibration_disclosure import CalibrationDisclosureError, CalibrationDisclosurePolicy


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/q1-fixtures/uncalibrated-disclosure-policy.json"
R1_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/R1.json"
R1_HISTORICAL_EVIDENCE = (
    ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/history/R1-accepted-1.json"
)
R1_FIXTURE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json"
Q1_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json"


class CalibrationDisclosureTests(unittest.TestCase):
    def load(self) -> tuple[dict, CalibrationDisclosurePolicy]:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        return payload, CalibrationDisclosurePolicy.from_dict(payload)

    def test_three_uncalibrated_records_are_digest_bound_and_non_public(self) -> None:
        payload, policy = self.load()
        self.assertEqual(payload, policy.to_dict())
        self.assertFalse(policy.public_release_allowed)
        self.assertEqual(3, len(policy.records))
        self.assertTrue(all(record.calibration_status.value == "UNCALIBRATED" for record in policy.records))
        self.assertTrue(all(record.communication_readiness.value == "NOT_READY" for record in policy.records))

    def test_policy_pins_historical_r1_evidence_and_fixture_content(self) -> None:
        _, policy = self.load()
        r1_evidence = json.loads(R1_HISTORICAL_EVIDENCE.read_text(encoding="utf-8"))
        r1_fixture = json.loads(R1_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual("EV-R1-ACCEPTED-1", r1_evidence["evidence_id"])
        self.assertEqual(
            hashlib.sha256(R1_HISTORICAL_EVIDENCE.read_bytes()).hexdigest(),
            policy.r1_evidence_sha256,
        )
        self.assertEqual(
            hashlib.sha256(R1_FIXTURE.read_bytes()).hexdigest(), policy.r1_fixture_sha256
        )
        self.assertEqual(r1_fixture["fixture_content_sha256"], policy.r1_fixture_content_sha256)
        self.assertEqual([record.case_id for record in policy.records], r1_fixture["case_ids"])

    def test_current_q1_acceptance_is_blocked_until_q1_is_reaccepted(self) -> None:
        r1_evidence = json.loads(R1_EVIDENCE.read_text(encoding="utf-8"))
        q1_evidence = json.loads(Q1_EVIDENCE.read_text(encoding="utf-8"))
        self.assertIn(
            r1_evidence["evidence_id"],
            {
                "EV-R1-REOPENED-2",
                "EV-R1-REOPENED-3",
                "EV-R1-REOPENED-4",
                "EV-R1-REOPENED-5",
                "EV-R1-ACCEPTED-2",
            },
        )
        self.assertEqual("EV-Q1-REOPENED-2", q1_evidence["evidence_id"])
        self.assertEqual("blocked", q1_evidence["acceptance_self_check"])
        self.assertEqual("BLOCKED", q1_evidence["proposed_state"])
        self.assertEqual("R1-independent-review-contract-v4", q1_evidence["invalidation"]["cause"])

    def test_science_priority_remains_separate_from_communication_readiness(self) -> None:
        _, policy = self.load()
        self.assertEqual("HIGH", policy.records[0].scientific_priority.value)
        self.assertEqual("NOT_READY", policy.records[0].communication_readiness.value)

    def test_identity_status_priority_and_disclosure_tampering_fail_closed(self) -> None:
        payload, _ = self.load()
        for mutate in (
            lambda p: p.update({"topic_id": "foreign-topic"}),
            lambda p: p.update({"r1_evidence_sha256": "0" * 64}),
            lambda p: p.update({"r1_fixture_content_sha256": "0" * 64}),
            lambda p: p["records"][0].update({"calibration_status": "CALIBRATED"}),
            lambda p: p["records"][0].update({"communication_readiness": "PUBLIC_READY"}),
            lambda p: p["records"][0].update({"scientific_priority": "NOT_READY"}),
            lambda p: p["records"][0].update({"disclosure_limits": []}),
            lambda p: p.update({"public_release_allowed": True}),
            lambda p: p["records"].pop(),
            lambda p: p.update({"unexpected": "field"}),
        ):
            candidate = copy.deepcopy(payload)
            mutate(candidate)
            with self.subTest(mutate=mutate), self.assertRaises(CalibrationDisclosureError):
                CalibrationDisclosurePolicy.from_dict(candidate)

    def test_digests_are_not_recomputable_by_a_fixture_consumer(self) -> None:
        payload, _ = self.load()
        candidate = copy.deepcopy(payload)
        candidate["records"][0]["predicted_difficulty"] = "LOW"
        with self.assertRaises(CalibrationDisclosureError):
            CalibrationDisclosurePolicy.from_dict(candidate)

    def test_is_not_a_claim_novelty_or_statistical_performance_engine(self) -> None:
        source = (ROOT / "matharc/v02/calibration_disclosure.py").read_text(encoding="utf-8")
        self.assertNotIn("ResearchTrace", source)
        self.assertNotIn("ClaimStatus", source)
        self.assertNotIn("NoveltyAudit", source)
        self.assertNotIn("http", source.lower())


if __name__ == "__main__":
    unittest.main()
