from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from matharc.v02.dogfood_archives import DogfoodArchiveError, DogfoodArchiveRunner
from matharc.v02.schema import digest_json


ROOT = Path(__file__).parents[1]
S1_FIXTURES = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/s1-fixtures"
T2_FIXTURE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures/three-real-archives.json"


class DogfoodArchiveTests(unittest.TestCase):
    def test_three_real_archives_persist_replay_budget_and_nonpromotion_boundaries(self) -> None:
        contract = json.loads(T2_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual("t2-dogfood-archive-contract", contract["fixture_kind"])
        self.assertEqual("union-closed", contract["topic_id"])
        self.assertEqual(3, len(contract["cases"]))
        with tempfile.TemporaryDirectory() as directory:
            runner = DogfoodArchiveRunner(directory, S1_FIXTURES)
            result = runner.run()
            self.assertTrue((Path(directory) / "dogfood-archives.json").is_file())
            self.assertTrue(result["archive_blocked"])
            self.assertTrue(result["blocking_manual_ids"])
            self.assertTrue(result["no_claim_or_trace_created"])
            self.assertEqual(result["budget_digest_sha256"], __import__("hashlib").sha256(
                json.dumps(result["budget_snapshot"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest())

            cases = {case["problem_id"]: case for case in result["cases"]}
            frankl = cases["P-FRANKL-Q6"]
            self.assertEqual("APPLIED", frankl["topic_status"])
            self.assertEqual("REPLAYED", frankl["replay_status"])
            self.assertEqual("OPEN_REPORTED", frankl["status"]["validated_status"])
            self.assertFalse(frankl["promotion_allowed"])

            collision = cases["P-ARXIV-2601-22401-COLLISION"]
            self.assertEqual("RESOLVED_REPORTED", collision["status"]["validated_status"])
            self.assertEqual("HIGH_RISK_EVENT", collision["manual_reason"])
            self.assertEqual("DUPLICATE", collision["replay_status"])
            self.assertEqual("PENDING_HUMAN_AUDIT", collision["novelty"]["authorization_status"])
            self.assertFalse(collision["novelty"]["complete_research_budget"])
            self.assertFalse(collision["novelty"]["public_qualitative_conclusion"])
            provenance = collision["provenance"]
            self.assertEqual({"OPEN_REPORTED", "RESOLVED_REPORTED"}, {item["reported_status"] for item in provenance})
            self.assertEqual("problem-database-current", next(item for item in provenance if item["reported_status"] == "RESOLVED_REPORTED")["source_kind"])
            self.assertEqual("problem-database-history", next(item for item in provenance if item["reported_status"] == "OPEN_REPORTED")["source_kind"])

            residual = cases["P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS"]
            self.assertEqual("MANUAL_REVIEW", residual["topic_status"])
            self.assertEqual("BUDGET_EXHAUSTED", residual["manual_reason"])
            self.assertEqual("OPEN_REPORTED", residual["status"]["reported_status"])
            self.assertEqual("STALE", residual["status"]["validated_status"])
            self.assertFalse(residual["promotion_allowed"])

            for case in result["cases"]:
                self.assertFalse(case["claim_created"])
                self.assertFalse(case["trace_created"])
                self.assertTrue(case["provenance"])
                for source in case["provenance"]:
                    self.assertTrue(source["canonical_uri"])
                    self.assertTrue(source["pinned_version"])
                    self.assertTrue(source["locator"])
                    self.assertEqual(64, len(source["content_sha256"]))
            self.assertFalse((Path(directory) / "claims.json").exists())
            self.assertFalse((Path(directory) / "research-trace.json").exists())

            restarted = DogfoodArchiveRunner(directory, S1_FIXTURES).run()
            self.assertTrue(restarted["replayed"])
            self.assertEqual(result["budget_digest_sha256"], restarted["budget_digest_sha256"])
            self.assertEqual(result["blocking_manual_ids"], restarted["blocking_manual_ids"])
            (Path(directory) / "topic-observation" / "topic-observation-state.json").unlink()
            with self.assertRaisesRegex(DogfoodArchiveError, "state is missing"):
                DogfoodArchiveRunner(directory, S1_FIXTURES).run()

        with tempfile.TemporaryDirectory() as directory:
            DogfoodArchiveRunner(directory, S1_FIXTURES).run()
            state_path = Path(directory) / "topic-observation" / "topic-observation-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["manual_queue"] = []
            state_path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(DogfoodArchiveError, "manual queue does not match"):
                DogfoodArchiveRunner(directory, S1_FIXTURES).run()

    def test_unknown_case_missing_provenance_and_tampered_archive_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = Path(directory) / "fixtures"
            fixture_root.mkdir()
            for path in S1_FIXTURES.glob("*.json"):
                (fixture_root / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            contract_root = Path(directory) / "t2-fixtures"
            contract_root.mkdir()
            shutil.copy2(T2_FIXTURE, contract_root / T2_FIXTURE.name)
            shutil.copytree(T2_FIXTURE.parent / "sources", contract_root / "sources")
            bad = json.loads((fixture_root / "frankl-q6.json").read_text(encoding="utf-8"))
            bad["problem_id"] = "P-UNKNOWN"
            (fixture_root / "frankl-q6.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(DogfoodArchiveError, "digest mismatch"):
                DogfoodArchiveRunner(Path(directory) / "run-unknown", fixture_root).run()

            (fixture_root / "frankl-q6.json").write_text((S1_FIXTURES / "frankl-q6.json").read_text(encoding="utf-8"), encoding="utf-8")
            bad = json.loads((fixture_root / "frankl-q6.json").read_text(encoding="utf-8"))
            bad["problem_id"] = "P-FRANKL-Q6"
            del bad["source_assertions"][0]["source_path"]
            (fixture_root / "frankl-q6.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(DogfoodArchiveError, "digest mismatch"):
                DogfoodArchiveRunner(Path(directory) / "run-missing", fixture_root).run()

        with tempfile.TemporaryDirectory() as directory:
            runner = DogfoodArchiveRunner(directory, S1_FIXTURES)
            runner.run()
            archive = Path(directory) / "dogfood-archives.json"
            payload = json.loads(archive.read_text(encoding="utf-8"))
            payload["budget_snapshot"] = copy.deepcopy(payload["budget_snapshot"])
            payload["budget_snapshot"]["limits"]["cost_usd"] = 1.0
            archive.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(DogfoodArchiveError, "budget snapshot"):
                DogfoodArchiveRunner(directory, S1_FIXTURES).run()

    def test_recomputed_budget_digests_cannot_accept_budget_snapshot_drift(self) -> None:
        def archive_digest(payload: dict) -> str:
            return digest_json({key: value for key, value in payload.items() if key not in {"archive_digest_sha256", "replayed"}})

        altered_snapshots = []
        output_tokens = {"limits": {"wall_seconds": None, "input_tokens": 1, "output_tokens": None, "cost_usd": None}, "spent": {"wall_seconds": 0.0, "input_tokens": 1, "output_tokens": 1, "cost_usd": 0.0, "tool_calls": 0, "model_calls": 1}, "divergent_usage_reports": [], "exhausted": True}
        altered_snapshots.append(output_tokens)
        model_calls = copy.deepcopy(output_tokens)
        model_calls["spent"]["output_tokens"] = 0
        model_calls["spent"]["model_calls"] = 2
        altered_snapshots.append(model_calls)

        with tempfile.TemporaryDirectory() as directory:
            DogfoodArchiveRunner(directory, S1_FIXTURES).run()
            archive = Path(directory) / "dogfood-archives.json"
            original = json.loads(archive.read_text(encoding="utf-8"))
            for snapshot in altered_snapshots:
                with self.subTest(snapshot=snapshot):
                    payload = copy.deepcopy(original)
                    payload["budget_snapshot"] = snapshot
                    payload["budget_digest_sha256"] = digest_json(snapshot)
                    payload["archive_digest_sha256"] = archive_digest(payload)
                    archive.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(DogfoodArchiveError, "budget snapshot identity"):
                        DogfoodArchiveRunner(directory, S1_FIXTURES).run()

        with tempfile.TemporaryDirectory() as directory:
            fixture_root = Path(directory) / "s1-fixtures"
            fixture_root.mkdir()
            for path in S1_FIXTURES.glob("*.json"):
                shutil.copy2(path, fixture_root / path.name)
            contract_root = Path(directory) / "t2-fixtures"
            contract_root.mkdir()
            shutil.copy2(T2_FIXTURE, contract_root / T2_FIXTURE.name)
            shutil.copytree(T2_FIXTURE.parent / "sources", contract_root / "sources")
            runner = DogfoodArchiveRunner(Path(directory) / "run", fixture_root)
            runner.run()
            source = contract_root / "sources" / "engineering-progress.md"
            source.write_text(source.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(DogfoodArchiveError, "digest mismatch"):
                DogfoodArchiveRunner(Path(directory) / "run", fixture_root).run()
            source.unlink()
            with self.assertRaisesRegex(DogfoodArchiveError, "missing source artifact"):
                DogfoodArchiveRunner(Path(directory) / "run", fixture_root).run()

        with tempfile.TemporaryDirectory() as directory:
            fixture_root = Path(directory) / "s1-fixtures"
            fixture_root.mkdir()
            for path in S1_FIXTURES.glob("*.json"):
                shutil.copy2(path, fixture_root / path.name)
            contract_root = Path(directory) / "t2-fixtures"
            contract_root.mkdir()
            shutil.copy2(T2_FIXTURE, contract_root / T2_FIXTURE.name)
            shutil.copytree(T2_FIXTURE.parent / "sources", contract_root / "sources")
            run_root = Path(directory) / "run"
            DogfoodArchiveRunner(run_root, fixture_root).run()
            fixture = json.loads((fixture_root / "frankl-q6.json").read_text(encoding="utf-8"))
            fixture["statement"] = fixture["statement"] + " altered"
            (fixture_root / "frankl-q6.json").write_text(json.dumps(fixture), encoding="utf-8")
            with self.assertRaisesRegex(DogfoodArchiveError, "S1 fixture digest mismatch"):
                DogfoodArchiveRunner(run_root, fixture_root).run()
            shutil.copy2(S1_FIXTURES / "frankl-q6.json", fixture_root / "frankl-q6.json")
            contract = json.loads((contract_root / T2_FIXTURE.name).read_text(encoding="utf-8"))
            contract["cases"][0]["expected_problem_status"] = "RESOLVED_REPORTED"
            (contract_root / T2_FIXTURE.name).write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DogfoodArchiveError, "contract or source identity drift"):
                DogfoodArchiveRunner(run_root, fixture_root).run()


if __name__ == "__main__":
    unittest.main()
