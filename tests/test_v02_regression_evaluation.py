from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
import os
import stat
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path

from matharc.v02.regression_evaluation import RegressionSuite, RegressionValidationError
from scripts.validate_frozen_review_inputs import R1_INPUT_PROFILE, R1_REQUIRED_INPUTS, validate_frozen_inputs


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json"
R1_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/R1.json"
REVIEW_LEDGER = ROOT / (
    "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
    "R1-regression-evaluation/reviews/r1-independent-review-20260901/ledger.json"
)
EXPECTED_REVIEWERS = {"ablation-boundary": "luna-l3", "identity-contract": "sol-l4"}
EXPECTED_WRAPPERS = {
    "ablation-boundary": "/Users/vsiyo/.codex/workers/run-l3.sh",
    "identity-contract": "/Users/vsiyo/.codex/workers/run-l4.sh",
}
RUN_RECORD_FIELDS = {
    "schema_version",
    "lane",
    "reviewer_identity",
    "wrapper",
    "wrapper_sha256",
    "execution_id",
    "codex_session_id",
    "pid",
    "started_at",
    "finished_at",
    "prompt_sha256",
    "log_path",
    "log_sha256",
    "exit_code",
    "zero_write",
    "actual_changed_paths",
}


class RegressionEvaluationTests(unittest.TestCase):
    def _assert_safe_regular_file(self, path: Path, expected_parent: Path) -> Path:
        relative = path.relative_to(ROOT)
        cursor = ROOT
        for part in relative.parts:
            cursor /= part
            self.assertFalse(cursor.is_symlink(), str(cursor))
        self.assertTrue(stat.S_ISREG(path.lstat().st_mode), str(path))
        resolved = path.resolve(strict=True)
        self.assertEqual(expected_parent.resolve(strict=True), resolved.parent)
        return resolved

    def _write_synthetic_campaign(self, root: Path, campaign: str) -> tuple[Path, str, list[dict[str, object]]]:
        manifest_inputs = []
        for relative in sorted(R1_REQUIRED_INPUTS):
            candidate = root / relative
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(relative, encoding="utf-8")
            manifest_inputs.append({"path": relative, "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()})

        manifest = root / campaign / "frozen-inputs.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "review_campaign_id": Path(campaign).name,
                    "input_profile": R1_INPUT_PROFILE,
                    "frozen_head": "1" * 40,
                    "remote_head": "1" * 40,
                    "inputs": manifest_inputs,
                }
            ),
            encoding="utf-8",
        )
        manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
        reports: list[dict[str, object]] = []
        for index, lane in enumerate(("ablation-boundary", "identity-contract"), start=1):
            identity = EXPECTED_REVIEWERS[lane]
            wrapper = EXPECTED_WRAPPERS[lane]
            log = root / campaign / "logs" / f"{lane}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            session_id = f"synthetic-session-{index}"
            log.write_text(
                f"SESSION_ID={session_id}\nEXIT_CODE=0\nZERO_WRITE=true\n",
                encoding="utf-8",
            )
            run = root / campaign / "runs" / f"{lane}.json"
            run.parent.mkdir(parents=True, exist_ok=True)
            run.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "lane": lane,
                        "reviewer_identity": identity,
                        "wrapper": wrapper,
                        "wrapper_sha256": str(index) * 64,
                        "execution_id": f"synthetic-execution-{index}",
                        "codex_session_id": session_id,
                        "pid": 1000 + index,
                        "started_at": f"2026-09-01T00:00:0{index}Z",
                        "finished_at": f"2026-09-01T00:01:0{index}Z",
                        "prompt_sha256": str(index + 2) * 64,
                        "log_path": str(log.relative_to(root)),
                        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                        "exit_code": 0,
                        "zero_write": True,
                        "actual_changed_paths": [],
                    }
                ),
                encoding="utf-8",
            )
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
                    "execution_record_path": str(run.relative_to(root)),
                    "execution_record_sha256": hashlib.sha256(run.read_bytes()).hexdigest(),
                }
            )
        return manifest, manifest_sha, reports

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
            evidence["evidence_id"] == "EV-R1-ACCEPTED-4"
            or evidence["acceptance_self_check"] == "pass"
        )
        self.assertEqual(11, evidence["acceptance_contract_version"])
        self.assertEqual(evidence["acceptance_contract_version"], reviews["contract_version"])
        if not is_acceptance_claim:
            self.assertIn(
                evidence["evidence_id"],
                {"EV-R1-REOPENED-2", "EV-R1-REOPENED-3", "EV-R1-REOPENED-4", "EV-R1-REOPENED-5"},
            )
            self.assertEqual("blocked", evidence["acceptance_self_check"])
            self.assertEqual("BLOCKED_PENDING_TWO_DURABLE_PASS_REPORTS", reviews["disposition"])
            self.assertEqual(
                "NOT_A_PASS_REPAIR_REQUIRED",
                json.loads(REVIEW_LEDGER.read_text(encoding="utf-8"))["attempt_1"]["disposition"],
            )
            return

        self.assertEqual("EV-R1-ACCEPTED-4", evidence["evidence_id"])
        self.assertEqual(["EV-A4-ACCEPTED-3"], evidence["consumed_evidence"])
        self.assertEqual("ACCEPTED", evidence["proposed_state"])
        self.assertEqual("ACCEPTED", evidence["acceptance_record"]["status"])
        self.assertEqual("PASS", reviews["disposition"])
        self.assertEqual(11, reviews["contract_version"])
        ledger = json.loads(REVIEW_LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(reviews["frozen_input_manifest_sha256"], ledger["frozen_input_manifest_sha256"])
        self.assertEqual(reviews["frozen_head"], ledger["frozen_head"])
        manifest_path = ROOT / reviews["frozen_input_manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(reviews["frozen_input_manifest_sha256"], hashlib.sha256(manifest_path.read_bytes()).hexdigest())
        self.assertEqual(R1_INPUT_PROFILE, manifest["input_profile"])
        self.assertEqual(manifest["frozen_head"], manifest["remote_head"])
        self.assertEqual(reviews["frozen_head"], manifest["frozen_head"])
        self.assertEqual(R1_REQUIRED_INPUTS, frozenset(validate_frozen_inputs(ROOT, manifest_path)))
        manifest_hashes = {item["path"]: item["sha256"] for item in manifest["inputs"]}
        for path in R1_REQUIRED_INPUTS:
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), manifest_hashes[path])
        required_lanes = {"ablation-boundary", "identity-contract"}
        reports = reviews["reports"]
        self.assertEqual(required_lanes, {report["lane"] for report in reports})
        self.assertEqual(2, len(reports))
        self.assertEqual(2, len({report["reviewer_identity"] for report in reports}))
        self.assertEqual(2, len({report["wrapper"] for report in reports}))
        report_paths = []
        report_hashes = []
        report_contents = []
        execution_ids = []
        session_ids = []
        pids = []
        wrapper_identities = []
        log_identities = []
        prompt_hashes = []
        for report in reports:
            self.assertEqual("PASS", report["verdict"])
            self.assertTrue(report["zero_write"])
            path = ROOT / report["report_path"]
            expected_reports = ROOT / Path(reviews["frozen_input_manifest"]).parent / "reports"
            self.assertEqual(f"{report['lane']}.md", path.name)
            report_path = self._assert_safe_regular_file(path, expected_reports)
            report_paths.append(report_path)
            report_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            report_hashes.append(report_hash)
            self.assertEqual(report_hash, report["sha256"])
            report_contents.append((report, path.read_text(encoding="utf-8")))

            run_path = ROOT / report["execution_record_path"]
            expected_runs = ROOT / Path(reviews["frozen_input_manifest"]).parent / "runs"
            self.assertEqual(f"{report['lane']}.json", run_path.name)
            self._assert_safe_regular_file(run_path, expected_runs)
            self.assertEqual(report["execution_record_sha256"], hashlib.sha256(run_path.read_bytes()).hexdigest())
            run = json.loads(run_path.read_text(encoding="utf-8"))
            self.assertEqual(RUN_RECORD_FIELDS, set(run))
            self.assertEqual(1, run["schema_version"])
            self.assertEqual(report["lane"], run["lane"])
            self.assertEqual(report["reviewer_identity"], run["reviewer_identity"])
            self.assertEqual(report["wrapper"], run["wrapper"])
            self.assertEqual(EXPECTED_REVIEWERS[report["lane"]], run["reviewer_identity"])
            self.assertEqual(EXPECTED_WRAPPERS[report["lane"]], run["wrapper"])
            self.assertRegex(run["wrapper_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(run["prompt_sha256"], r"^[0-9a-f]{64}$")
            self.assertIsInstance(run["pid"], int)
            self.assertGreater(run["pid"], 0)
            self.assertTrue(run["execution_id"])
            self.assertTrue(run["codex_session_id"])
            started = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
            finished = datetime.fromisoformat(run["finished_at"].replace("Z", "+00:00"))
            self.assertIsNotNone(started.tzinfo)
            self.assertIsNotNone(finished.tzinfo)
            self.assertLess(started, finished)
            self.assertEqual(0, run["exit_code"])
            self.assertTrue(run["zero_write"])
            self.assertEqual([], run["actual_changed_paths"])

            log_path = ROOT / run["log_path"]
            expected_logs = ROOT / Path(reviews["frozen_input_manifest"]).parent / "logs"
            self.assertEqual(f"{report['lane']}.log", log_path.name)
            self._assert_safe_regular_file(log_path, expected_logs)
            self.assertEqual(run["log_sha256"], hashlib.sha256(log_path.read_bytes()).hexdigest())
            log = log_path.read_text(encoding="utf-8")
            self.assertIn(f"SESSION_ID={run['codex_session_id']}", log)
            self.assertIn("EXIT_CODE=0", log)
            self.assertIn("ZERO_WRITE=true", log)

            execution_ids.append(run["execution_id"])
            session_ids.append(run["codex_session_id"])
            pids.append(run["pid"])
            wrapper_identities.append((run["wrapper"], run["wrapper_sha256"]))
            log_identities.append((run["log_path"], run["log_sha256"]))
            prompt_hashes.append(run["prompt_sha256"])
        self.assertEqual(2, len(set(report_paths)))
        self.assertEqual(2, len(set(report_hashes)))
        for identities in (execution_ids, session_ids, pids, wrapper_identities, log_identities, prompt_hashes):
            self.assertEqual(2, len(set(identities)))
        for report, content in report_contents:
            for marker, value in (
                ("- Lane: `", f"- Lane: `{report['lane']}`"),
                ("- Reviewer identity: `", f"- Reviewer identity: `{report['reviewer_identity']}`"),
                ("- Wrapper: `", f"- Wrapper: `{report['wrapper']}`"),
            ):
                self.assertEqual(1, content.count(marker), marker)
                self.assertEqual(1, content.count(value), value)
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
            campaign = (
                "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
                "R1-regression-evaluation/reviews/synthetic-retry"
            )
            manifest, manifest_sha, reports = self._write_synthetic_campaign(root, campaign)

            evidence = {
                "evidence_id": "EV-R1-ACCEPTED-4",
                "acceptance_contract_version": 11,
                "acceptance_self_check": "pass",
                "consumed_evidence": ["EV-A4-ACCEPTED-3"],
                "proposed_state": "ACCEPTED",
                "acceptance_record": {"status": "ACCEPTED"},
                "source_identity": {"protected_test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                "independent_ai_reviews": {
                    "contract_version": 11,
                    "disposition": "PASS",
                    "frozen_input_manifest": str(manifest.relative_to(root)),
                    "frozen_input_manifest_sha256": manifest_sha,
                    "frozen_head": "1" * 40,
                    "reports": reports,
                },
            }
            try:
                globals()["ROOT"] = root
                globals()["R1_EVIDENCE"] = MemoryJSON(evidence)
                globals()["REVIEW_LEDGER"] = MemoryJSON(
                    {"frozen_input_manifest_sha256": manifest_sha, "frozen_head": "1" * 40}
                )
                self.test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence()

                valid_reports = copy.deepcopy(reports)
                evidence["independent_ai_reviews"]["reports"][1]["report_path"] = reports[0]["report_path"]
                evidence["independent_ai_reviews"]["reports"][1]["sha256"] = reports[0]["sha256"]
                with self.assertRaises(AssertionError):
                    self.test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence()

                evidence["independent_ai_reviews"]["reports"] = valid_reports
                reports_dir = root / campaign / "reports"
                real_reports = root / campaign / "real-reports"
                reports_dir.rename(real_reports)
                reports_dir.symlink_to(real_reports.name, target_is_directory=True)
                with self.assertRaises(AssertionError):
                    self.test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence()
            finally:
                globals()["ROOT"] = original_root
                globals()["R1_EVIDENCE"] = original_evidence
                globals()["REVIEW_LEDGER"] = original_ledger

    def test_accepted_review_gate_rejects_byte_identical_hard_linked_dual_declaration_reports(self) -> None:
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
            campaign = (
                "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
                "R1-regression-evaluation/reviews/synthetic-hard-link-replay"
            )
            manifest, manifest_sha, reports = self._write_synthetic_campaign(root, campaign)

            evidence = {
                "evidence_id": "EV-R1-ACCEPTED-4",
                "acceptance_contract_version": 11,
                "acceptance_self_check": "pass",
                "consumed_evidence": ["EV-A4-ACCEPTED-3"],
                "proposed_state": "ACCEPTED",
                "acceptance_record": {"status": "ACCEPTED"},
                "source_identity": {"protected_test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                "independent_ai_reviews": {
                    "contract_version": 11,
                    "disposition": "PASS",
                    "frozen_input_manifest": str(manifest.relative_to(root)),
                    "frozen_input_manifest_sha256": manifest_sha,
                    "frozen_head": "1" * 40,
                    "reports": reports,
                },
            }
            try:
                globals()["ROOT"] = root
                globals()["R1_EVIDENCE"] = MemoryJSON(evidence)
                globals()["REVIEW_LEDGER"] = MemoryJSON(
                    {"frozen_input_manifest_sha256": manifest_sha, "frozen_head": "1" * 40}
                )
                self.test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence()

                shared_content = "\n".join(
                    (
                        "- Lane: `ablation-boundary`",
                        "- Lane: `identity-contract`",
                        "- Reviewer identity: `synthetic-luna`",
                        "- Reviewer identity: `synthetic-sol`",
                        "- Wrapper: `/synthetic/run-l3.sh`",
                        "- Wrapper: `/synthetic/run-l4.sh`",
                        "- Review mode: zero-write",
                        f"Frozen input manifest SHA-256: {manifest_sha}",
                        "Verdict: PASS",
                        "",
                    )
                )
                source_report = root / reports[0]["report_path"]
                replay_report = root / reports[1]["report_path"]
                source_report.write_text(shared_content, encoding="utf-8")
                replay_report.unlink()
                os.link(source_report, replay_report)
                shared_sha = hashlib.sha256(source_report.read_bytes()).hexdigest()
                for report in reports:
                    report["sha256"] = shared_sha

                with self.assertRaises(AssertionError):
                    self.test_independent_review_gate_is_fail_closed_for_pending_and_accepted_evidence()
            finally:
                globals()["ROOT"] = original_root
                globals()["R1_EVIDENCE"] = original_evidence
                globals()["REVIEW_LEDGER"] = original_ledger


if __name__ == "__main__":
    unittest.main()
