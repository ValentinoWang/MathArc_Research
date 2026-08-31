from __future__ import annotations

import copy
import hashlib
import json
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path

from matharc.v02.regression_evaluation import RegressionSuite, RegressionValidationError


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json"
R1_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/R1.json"
REVIEW_LEDGER = ROOT / (
    "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
    "R1-regression-evaluation/reviews/r1-independent-review-20260901/ledger.json"
)


class RegressionEvaluationTests(unittest.TestCase):
    def load(self) -> tuple[dict, RegressionSuite]:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        return payload, RegressionSuite.from_dict(payload)

    def test_three_cases_four_routes_and_deterministic_ablation(self) -> None:
        payload, suite = self.load()
        result = suite.evaluate()
        self.assertEqual(payload["case_ids"], list(result.case_ids))
        self.assertEqual(3, len(result.cases))
        for case in result.cases:
            self.assertEqual(4, len(case.routes))
            self.assertEqual(set(payload["route_order"]), set(case.route_names))
            self.assertEqual(case, suite.evaluate().case_by_id(case.case_id))
        self.assertEqual(result.digest_sha256, suite.evaluate().digest_sha256)
        self.assertTrue(any(item.incremental_hits == () for case in result.cases for item in case.routes))

    def test_expected_outcomes_are_only_hits_misses_and_gaps(self) -> None:
        _, suite = self.load()
        result = suite.evaluate()
        allowed = {"hit", "miss", "gap"}
        for case in result.cases:
            self.assertTrue(set(case.outcome_labels) <= allowed)
            self.assertGreaterEqual(case.manual_minutes, 0)
            self.assertLessEqual(case.manual_minutes, 240)
            self.assertEqual(case.full_hit_ids, tuple(sorted(case.full_hit_ids)))
            for route in case.routes:
                self.assertEqual(route.incremental_hits, tuple(sorted(route.incremental_hits)))

    def test_tampering_identity_digest_and_ablation_fails_closed(self) -> None:
        payload, _ = self.load()
        for mutate in (
            lambda p: p.update({"a4_evidence_digest": "0" * 64}),
            lambda p: p["cases"].pop(),
            lambda p: p["cases"][0]["routes"].pop(),
            lambda p: p["cases"][0]["routes"][1].update(p["cases"][0]["routes"][0]),
            lambda p: p["cases"][0].update({"expected_status": "PROVED"}),
            lambda p: p.update({"topic_id": "foreign-topic"}),
            lambda p: p["cases"][0]["routes"][0]["queries"].__setitem__(0, "tampered query"),
            lambda p: p["cases"][0]["routes"][0]["source_ids"].__setitem__(0, "tampered-source"),
            lambda p: p["cases"][0]["routes"][0]["hits"].__setitem__(0, "tampered-hit"),
            lambda p: p["cases"][0]["routes"][0]["unresolved"].append("tampered gap"),
            lambda p: p["cases"][0].update({"manual_minutes": 13}),
            lambda p: p["cases"][0].update({"manual_minutes": -1}),
        ):
            candidate = copy.deepcopy(payload)
            mutate(candidate)
            with self.subTest(mutate=mutate), self.assertRaises(RegressionValidationError):
                RegressionSuite.from_dict(candidate)

    def test_is_passive_and_does_not_import_authorization_or_trace(self) -> None:
        source = (ROOT / "matharc/v02/regression_evaluation.py").read_text(encoding="utf-8")
        self.assertNotIn("ResearchTrace", source)
        self.assertNotIn("ClaimStatus", source)
        self.assertNotIn("authorize", source)
        self.assertNotIn("http", source.lower())

    def test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence(self) -> None:
        evidence = json.loads(R1_EVIDENCE.read_text(encoding="utf-8"))
        reviews = evidence["independent_ai_reviews"]
        self.assertEqual(
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            evidence["source_identity"]["protected_test_sha256"],
        )
        is_acceptance_claim = (
            evidence["evidence_id"] == "EV-R1-ACCEPTED-2"
            or evidence["acceptance_self_check"] == "pass"
        )
        if not is_acceptance_claim:
            self.assertIn(
                evidence["evidence_id"],
                {"EV-R1-REOPENED-2", "EV-R1-REOPENED-3", "EV-R1-REOPENED-4"},
            )
            self.assertEqual("blocked", evidence["acceptance_self_check"])
            self.assertEqual("BLOCKED_PENDING_TWO_DURABLE_PASS_REPORTS", reviews["disposition"])
            self.assertEqual(
                "NOT_A_PASS_REPAIR_REQUIRED",
                json.loads(REVIEW_LEDGER.read_text(encoding="utf-8"))["attempt_1"]["disposition"],
            )
            return

        self.assertEqual("PASS", reviews["disposition"])
        self.assertEqual(8, reviews["contract_version"])
        ledger = json.loads(REVIEW_LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(reviews["frozen_input_manifest_sha256"], ledger["frozen_input_manifest_sha256"])
        self.assertEqual(reviews["frozen_head"], ledger["frozen_head"])
        manifest_path = ROOT / reviews["frozen_input_manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(reviews["frozen_input_manifest_sha256"], hashlib.sha256(manifest_path.read_bytes()).hexdigest())
        manifest_hashes = {item["path"]: item["sha256"] for item in manifest["inputs"]}
        for path in (
            "tests/test_v02_regression_evaluation.py",
            "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/acceptance-contract.md",
            "acceptance/human/R1-regression-evaluation/binding.md",
            "acceptance/human/R1-regression-evaluation/checklist.md",
        ):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), manifest_hashes[path])
        required_lanes = {"ablation-boundary", "identity-contract"}
        reports = reviews["reports"]
        self.assertEqual(required_lanes, {report["lane"] for report in reports})
        self.assertEqual(2, len(reports))
        self.assertEqual(2, len({report["reviewer_identity"] for report in reports}))
        self.assertEqual(2, len({report["wrapper"] for report in reports}))
        for report in reports:
            self.assertEqual("PASS", report["verdict"])
            self.assertTrue(report["zero_write"])
            path = ROOT / report["report_path"]
            self.assertTrue(path.is_file(), report["report_path"])
            manifest_path = Path(reviews["frozen_input_manifest"])
            self.assertEqual(manifest_path.parent / "reports", Path(report["report_path"]).parent)
            self.assertEqual(f"{report['lane']}.md", path.name)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), report["sha256"])
            content = path.read_text(encoding="utf-8")
            self.assertIn(f"Lane: `{report['lane']}`", content)
            self.assertIn(f"Reviewer identity: `{report['reviewer_identity']}`", content)
            self.assertIn(f"Wrapper: `{report['wrapper']}`", content)
            self.assertIn("zero-write", content.lower())
            self.assertIn("Verdict: PASS", content)
            self.assertTrue(content.rstrip().endswith("Verdict: PASS"))
            self.assertIn(
                f"Frozen input manifest SHA-256: {reviews['frozen_input_manifest_sha256']}",
                content.replace("`", ""),
            )

    def test_accepted_review_gate_rejects_one_report_replayed_as_two_lanes(self) -> None:
        class MemoryJSON:
            def __init__(self, value: dict) -> None:
                self.value = value

            def read_text(self, encoding: str = "utf-8") -> str:
                return json.dumps(self.value)

        original_root = ROOT
        original_evidence = R1_EVIDENCE
        original_ledger = REVIEW_LEDGER
        with TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            protected_paths = (
                "tests/test_v02_regression_evaluation.py",
                "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/acceptance-contract.md",
                "acceptance/human/R1-regression-evaluation/binding.md",
                "acceptance/human/R1-regression-evaluation/checklist.md",
            )
            manifest_inputs = []
            for path in protected_paths:
                candidate = root / path
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_text(path, encoding="utf-8")
                manifest_inputs.append({"path": path, "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()})

            campaign = (
                "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
                "R1-regression-evaluation/reviews/synthetic-retry"
            )
            manifest = root / campaign / "frozen-inputs.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(json.dumps({"inputs": manifest_inputs}), encoding="utf-8")
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            reports = []
            for lane, identity, wrapper in (
                ("ablation-boundary", "synthetic-luna", "/synthetic/run-l3.sh"),
                ("identity-contract", "synthetic-sol", "/synthetic/run-l4.sh"),
            ):
                report = root / campaign / "reports" / f"{lane}.md"
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(
                    "\n".join(
                        (
                            f"- Lane: `{lane}`",
                            f"- Reviewer identity: `{identity}`",
                            f"- Wrapper: `{wrapper}`",
                            "- Review mode: zero-write",
                            f"Frozen input manifest SHA-256: {manifest_sha}",
                            "Verdict: PASS",
                            "",
                        )
                    ),
                    encoding="utf-8",
                )
                reports.append(
                    {
                        "lane": lane,
                        "reviewer_identity": identity,
                        "wrapper": wrapper,
                        "verdict": "PASS",
                        "zero_write": True,
                        "report_path": str(report.relative_to(root)),
                        "sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
                    }
                )

            evidence = {
                "evidence_id": "EV-R1-ACCEPTED-2",
                "acceptance_self_check": "pass",
                "source_identity": {"protected_test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                "independent_ai_reviews": {
                    "contract_version": 8,
                    "disposition": "PASS",
                    "frozen_input_manifest": str(manifest.relative_to(root)),
                    "frozen_input_manifest_sha256": manifest_sha,
                    "frozen_head": "synthetic-head",
                    "reports": reports,
                },
            }
            try:
                globals()["ROOT"] = root
                globals()["R1_EVIDENCE"] = MemoryJSON(evidence)
                globals()["REVIEW_LEDGER"] = MemoryJSON(
                    {"frozen_input_manifest_sha256": manifest_sha, "frozen_head": "synthetic-head"}
                )
                self.test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence()

                evidence["independent_ai_reviews"]["reports"][1]["report_path"] = reports[0]["report_path"]
                evidence["independent_ai_reviews"]["reports"][1]["sha256"] = reports[0]["sha256"]
                with self.assertRaises(AssertionError):
                    self.test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence()
            finally:
                globals()["ROOT"] = original_root
                globals()["R1_EVIDENCE"] = original_evidence
                globals()["REVIEW_LEDGER"] = original_ledger


if __name__ == "__main__":
    unittest.main()
