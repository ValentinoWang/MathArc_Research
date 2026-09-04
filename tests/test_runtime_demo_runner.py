from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.demo_runner import DEFAULT_QUESTION, run_agent_demo


class RuntimeDemoRunnerTests(unittest.TestCase):
    def test_end_to_end_loop_is_deterministic_and_writes_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = run_agent_demo(DEFAULT_QUESTION, output_dir=Path(directory) / "first")
            second = run_agent_demo(DEFAULT_QUESTION, output_dir=Path(directory) / "second")

            self.assertEqual(first.status, "VERIFIED_CERTIFICATE")
            self.assertEqual(first.to_dict()["question_digest"], second.to_dict()["question_digest"])
            self.assertEqual(first.to_dict()["run_id"], second.to_dict()["run_id"])
            self.assertEqual(first.to_dict()["stages"], second.to_dict()["stages"])
            self.assertEqual(first.to_dict()["evidence"], second.to_dict()["evidence"])
            self.assertEqual(first.to_dict()["provenance"], second.to_dict()["provenance"])

            payload = json.loads(Path(first.output_paths["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "VERIFIED_CERTIFICATE")
            self.assertEqual(payload["stages"]["decomposition"]["status"], "READY")
            self.assertEqual(payload["stages"]["tool"]["status"], "PASS")
            self.assertEqual(payload["stages"]["verification"]["status"], "PASS")
            self.assertEqual(payload["stages"]["result"]["verified_claim_id"], "C-STEP")
            self.assertFalse(payload["stages"]["result"]["promotion_allowed"])
            self.assertEqual(len(payload["evidence"]["digest_sha256"]), 64)
            self.assertFalse(payload["provenance"]["network"])
            self.assertFalse(payload["provenance"]["credentials"])
            markdown = Path(first.output_paths["markdown"]).read_text(encoding="utf-8")
            self.assertIn("Observable Loop", markdown)
            self.assertIn("Independent replay", markdown)

    def test_unknown_question_fails_closed_without_tool_or_evidence(self) -> None:
        result = run_agent_demo("Solve an unrelated problem.")
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.stages["decomposition"]["status"], "BLOCKED")
        self.assertNotIn("tool", result.stages)
        self.assertIsNone(result.evidence)

    def test_question_is_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "question is required"):
            run_agent_demo("   ")


if __name__ == "__main__":
    unittest.main()
