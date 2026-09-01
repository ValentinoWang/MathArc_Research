"""External-to-workspace difficulty predictions and per-dimension calibration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .local_store import LocalStoreError, exclusive_lock, external_root, read_json, state_digest, strict_mapping, write_json_atomic
from .schema import digest_json


DIFFICULTY_DIMENSIONS = ("statement_complexity", "evidence_gap", "verification_cost", "method_uncertainty")
CALIBRATION_MINIMUM = 20


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise LocalStoreError(f"{label} must be non-empty text")
    return value


class OrdinalLevel(str, Enum): LOW = "LOW"; MEDIUM = "MEDIUM"; HIGH = "HIGH"
class CalibrationStatus(str, Enum): UNCALIBRATED = "UNCALIBRATED"; CALIBRATED = "CALIBRATED"


def _dimensions(value: object, label: str) -> tuple[tuple[str, OrdinalLevel], ...]:
    if not isinstance(value, Mapping) or set(value) != set(DIFFICULTY_DIMENSIONS): raise LocalStoreError(f"{label} must contain exactly four named dimensions")
    return tuple((key, OrdinalLevel(value[key])) for key in DIFFICULTY_DIMENSIONS)


@dataclass(frozen=True, slots=True)
class DifficultyPrediction:
    prediction_id: str
    problem_id: str
    dimensions: tuple[tuple[str, OrdinalLevel], ...]
    evidence_refs: tuple[str, ...]
    predicted_at: str
    def __post_init__(self) -> None:
        _text(self.prediction_id, "prediction_id"); _text(self.problem_id, "problem_id"); _text(self.predicted_at, "predicted_at")
        if tuple(key for key, _ in self.dimensions) != DIFFICULTY_DIMENSIONS: raise LocalStoreError("prediction dimensions must be ordered fixed dimensions")
        if self.evidence_refs != tuple(sorted(self.evidence_refs)) or len(set(self.evidence_refs)) != len(self.evidence_refs) or any(not item.strip() for item in self.evidence_refs): raise LocalStoreError("prediction evidence refs must be unique sorted text")
    def to_dict(self) -> dict[str, Any]: return {"prediction_id": self.prediction_id, "problem_id": self.problem_id, "dimensions": dict((key, value.value) for key, value in self.dimensions), "evidence_refs": list(self.evidence_refs), "predicted_at": self.predicted_at}
    @classmethod
    def from_dict(cls, value: object) -> "DifficultyPrediction":
        data = strict_mapping(value, {"prediction_id", "problem_id", "dimensions", "evidence_refs", "predicted_at"}, "difficulty prediction")
        if not isinstance(data["evidence_refs"], list): raise LocalStoreError("prediction evidence refs must be an array")
        return cls(_text(data["prediction_id"], "prediction_id"), _text(data["problem_id"], "problem_id"), _dimensions(data["dimensions"], "prediction dimensions"), tuple(_text(item, "evidence ref") for item in data["evidence_refs"]), _text(data["predicted_at"], "predicted_at"))


@dataclass(frozen=True, slots=True)
class DifficultyOutcome:
    outcome_id: str
    prediction_id: str
    dimensions: tuple[tuple[str, OrdinalLevel], ...]
    observed_at: str
    def __post_init__(self) -> None:
        _text(self.outcome_id, "outcome_id"); _text(self.prediction_id, "prediction_id"); _text(self.observed_at, "observed_at")
        if tuple(key for key, _ in self.dimensions) != DIFFICULTY_DIMENSIONS: raise LocalStoreError("outcome dimensions must be ordered fixed dimensions")
    def to_dict(self) -> dict[str, Any]: return {"outcome_id": self.outcome_id, "prediction_id": self.prediction_id, "dimensions": dict((key, value.value) for key, value in self.dimensions), "observed_at": self.observed_at}
    @classmethod
    def from_dict(cls, value: object) -> "DifficultyOutcome":
        data = strict_mapping(value, {"outcome_id", "prediction_id", "dimensions", "observed_at"}, "difficulty outcome")
        return cls(_text(data["outcome_id"], "outcome_id"), _text(data["prediction_id"], "prediction_id"), _dimensions(data["dimensions"], "outcome dimensions"), _text(data["observed_at"], "observed_at"))


@dataclass(frozen=True, slots=True)
class CalibrationSummary:
    per_dimension_counts: tuple[tuple[str, int], ...]
    status: CalibrationStatus
    def __post_init__(self) -> None:
        if tuple(key for key, _ in self.per_dimension_counts) != DIFFICULTY_DIMENSIONS or any(not isinstance(count, int) or count < 0 for _, count in self.per_dimension_counts): raise LocalStoreError("calibration summary must use four nonnegative per-dimension counts")
        expected = CalibrationStatus.CALIBRATED if min(count for _, count in self.per_dimension_counts) >= CALIBRATION_MINIMUM else CalibrationStatus.UNCALIBRATED
        if self.status is not expected: raise LocalStoreError("calibration status does not match its sample threshold")
    def to_dict(self) -> dict[str, Any]: return {"per_dimension_counts": dict(self.per_dimension_counts), "status": self.status.value, "aggregate_score": None}


class DifficultyLedger:
    _FILENAME = "difficulty-ledger.json"
    def __init__(self, root: str) -> None: self.root = external_root(root); self.path = self.root / self._FILENAME
    def _load(self) -> tuple[list[DifficultyPrediction], list[DifficultyOutcome]]:
        if not self.path.exists(): return [], []
        data = strict_mapping(read_json(self.path, "difficulty ledger"), {"schema_version", "predictions", "outcomes", "state_digest_sha256"}, "difficulty ledger")
        if data["schema_version"] != "1.0" or data["state_digest_sha256"] != state_digest(data) or not isinstance(data["predictions"], list) or not isinstance(data["outcomes"], list): raise LocalStoreError("difficulty ledger integrity check failed")
        predictions = [DifficultyPrediction.from_dict(item) for item in data["predictions"]]; outcomes = [DifficultyOutcome.from_dict(item) for item in data["outcomes"]]
        if [item.prediction_id for item in predictions] != sorted(item.prediction_id for item in predictions) or len({item.prediction_id for item in predictions}) != len(predictions) or [item.outcome_id for item in outcomes] != sorted(item.outcome_id for item in outcomes) or len({item.outcome_id for item in outcomes}) != len(outcomes) or any(item.prediction_id not in {prediction.prediction_id for prediction in predictions} for item in outcomes) or len({item.prediction_id for item in outcomes}) != len(outcomes): raise LocalStoreError("difficulty ledger record identities are invalid")
        return predictions, outcomes
    def _save(self, predictions: list[DifficultyPrediction], outcomes: list[DifficultyOutcome]) -> None:
        payload: dict[str, Any] = {"schema_version": "1.0", "predictions": [item.to_dict() for item in sorted(predictions, key=lambda item: item.prediction_id)], "outcomes": [item.to_dict() for item in sorted(outcomes, key=lambda item: item.outcome_id)]}
        payload["state_digest_sha256"] = state_digest(payload); write_json_atomic(self.path, payload)
    def add_prediction(self, prediction: DifficultyPrediction) -> DifficultyPrediction:
        with exclusive_lock(self.root, self._FILENAME):
            predictions, outcomes = self._load(); previous = next((item for item in predictions if item.prediction_id == prediction.prediction_id), None)
            if previous is not None:
                if previous == prediction: return previous
                raise LocalStoreError("duplicate difficulty prediction id")
            predictions.append(prediction); self._save(predictions, outcomes)
        return prediction
    def record_outcome(self, outcome: DifficultyOutcome) -> DifficultyOutcome:
        with exclusive_lock(self.root, self._FILENAME):
            predictions, outcomes = self._load(); previous = next((item for item in outcomes if item.outcome_id == outcome.outcome_id), None)
            if outcome.prediction_id not in {item.prediction_id for item in predictions}: raise LocalStoreError("outcome references an unknown prediction")
            if any(item.prediction_id == outcome.prediction_id for item in outcomes): raise LocalStoreError("a prediction may have only one observed outcome")
            if previous is not None:
                if previous == outcome: return previous
                raise LocalStoreError("duplicate difficulty outcome id")
            outcomes.append(outcome); self._save(predictions, outcomes)
        return outcome
    def summary(self) -> CalibrationSummary:
        _, outcomes = self._load(); count = len(outcomes)
        return CalibrationSummary(tuple((key, count) for key in DIFFICULTY_DIMENSIONS), CalibrationStatus.CALIBRATED if count >= CALIBRATION_MINIMUM else CalibrationStatus.UNCALIBRATED)

    def records(self) -> tuple[tuple[DifficultyPrediction, ...], tuple[DifficultyOutcome, ...]]:
        predictions, outcomes = self._load()
        return tuple(predictions), tuple(outcomes)
