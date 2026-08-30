from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
ROUND4 = ROOT / "experiments" / "frankl_q6_round4"


def _load_auditor() -> ModuleType:
    path = ROUND4 / "audit_archive.py"
    spec = importlib.util.spec_from_file_location("matharc_q6_round4_archive", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Round4ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()

    def test_checked_in_archive_is_intact_but_full_replay_is_unavailable(self) -> None:
        report = self.auditor.audit_archive(ROUND4)
        self.assertEqual(report["archive_status"], "ARCHIVE_INTEGRITY_PASS")
        self.assertEqual(report["full_cold_replay_status"], "UNAVAILABLE")
        self.assertFalse(report["current_theorem_acceptance"])
        self.assertEqual(
            report["missing_rebuild_sources"],
            [
                "verifier/verify_q6_exact6_card.cpp",
                "verifier/verify_q6_exact7_pair.cpp",
                "verifier/verify_q6_k7_full_cases.py",
            ],
        )
        self.assertEqual(len(report["missing_or_invalid_component_results"]), 8)

    def test_full_replay_inputs_require_every_declared_source_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aggregate = root / "aggregate.json"
            aggregate.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "all_checks_passed": True,
                        "conclusion": {"full_frankl_conjecture": "INCONCLUSIVE"},
                    }
                ),
                encoding="utf-8",
            )
            expected_digest = hashlib.sha256(aggregate.read_bytes()).hexdigest()
            (root / "source.py").write_text("print('source')\n", encoding="utf-8")
            result = root / "result.json"
            result.write_text('{"all_checks_passed": true}\n', encoding="utf-8")
            (root / "archive_manifest.json").write_text(
                json.dumps(
                    {
                        "schema": "matharc.frankl-q6-round4-archive.1",
                        "aggregate_record": {
                            "path": "aggregate.json",
                            "sha256": expected_digest,
                        },
                        "required_rebuild_sources": ["source.py"],
                        "required_component_results": ["result.json"],
                        "claim_boundary": "test fixture",
                    }
                ),
                encoding="utf-8",
            )
            complete = self.auditor.audit_archive(root)
            self.assertEqual(
                complete["full_cold_replay_status"],
                "INPUTS_PRESENT_NOT_EXECUTED",
            )

            result.unlink()
            incomplete = self.auditor.audit_archive(root)
            self.assertEqual(incomplete["full_cold_replay_status"], "UNAVAILABLE")

    def test_changed_aggregate_fails_archive_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "archive_manifest.json").write_bytes(
                (ROUND4 / "archive_manifest.json").read_bytes()
            )
            target = root / "results" / "q6-round4-final.json"
            target.parent.mkdir()
            target.write_text("{}\n", encoding="utf-8")
            report = self.auditor.audit_archive(root)
            self.assertEqual(report["archive_status"], "ARCHIVE_INTEGRITY_FAIL")


if __name__ == "__main__":
    unittest.main()
