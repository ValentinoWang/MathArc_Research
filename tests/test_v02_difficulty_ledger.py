from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.difficulty_ledger import CALIBRATION_MINIMUM, DIFFICULTY_DIMENSIONS, CalibrationStatus, DifficultyLedger, DifficultyOutcome, DifficultyPrediction, OrdinalLevel
from matharc.v02.local_store import LocalStoreError
from matharc.v02.workspace_bundle import write_full_workspace_bundle


def dimensions(level: OrdinalLevel = OrdinalLevel.MEDIUM) -> dict[str, OrdinalLevel]: return {key: level for key in DIFFICULTY_DIMENSIONS}


class DifficultyLedgerTests(unittest.TestCase):
    def test_four_dimensions_and_uncalibrated_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = DifficultyLedger(Path(directory) / "ledger")
            for index in range(CALIBRATION_MINIMUM - 1):
                ledger.add_prediction(DifficultyPrediction(f"P-{index:02}", f"problem-{index}", tuple(dimensions().items()), (), "2026-09-01T00:00:00+00:00"))
                ledger.record_outcome(DifficultyOutcome(f"O-{index:02}", f"P-{index:02}", tuple(dimensions().items()), "2026-09-02T00:00:00+00:00"))
            self.assertEqual(ledger.summary().status, CalibrationStatus.UNCALIBRATED)
            ledger.add_prediction(DifficultyPrediction("P-20", "problem-20", tuple(dimensions().items()), (), "2026-09-01T00:00:00+00:00")); ledger.record_outcome(DifficultyOutcome("O-20", "P-20", tuple(dimensions().items()), "2026-09-02T00:00:00+00:00"))
            summary = ledger.summary(); self.assertEqual(summary.status, CalibrationStatus.CALIBRATED); self.assertNotIn("aggregate_score", {key for key, _ in summary.per_dimension_counts}); self.assertIsNone(summary.to_dict()["aggregate_score"])

    def test_rejects_unknown_dimensions_tampering_and_workspace_location(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "ledger"; ledger = DifficultyLedger(root)
            with self.assertRaises(LocalStoreError): DifficultyPrediction("P", "problem", (("wrong", OrdinalLevel.LOW),), (), "now")
            prediction = DifficultyPrediction("P", "problem", tuple(dimensions().items()), (), "now"); ledger.add_prediction(prediction)
            data = json.loads((root / "difficulty-ledger.json").read_text(encoding="utf-8")); data["predictions"][0]["problem_id"] = "tampered"; (root / "difficulty-ledger.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(LocalStoreError): ledger.summary()
            workspace = Path(directory) / "workspace"; write_full_workspace_bundle(workspace)
            with self.assertRaises(LocalStoreError): DifficultyLedger(workspace / "ledger")


if __name__ == "__main__": unittest.main()
