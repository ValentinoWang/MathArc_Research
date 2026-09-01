"""Fail-closed Q1 records for uncalibrated difficulty and disclosure policy."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, TypeVar

from .schema import digest_json


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CASE_IDS = (
    "P-FRANKL-Q6",
    "P-ARXIV-2601-22401-COLLISION",
    "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS",
)
_R1_EVIDENCE_ID = "EV-R1-ACCEPTED-3"
_R1_EVIDENCE_DIGEST = "effd9130a75b8e603f8d54f6ef37c511bc0ebc2de635f256353ac33f507b858a"
_R1_FIXTURE_DIGEST = "9b7fb5c0e63cecde14ee658b4eac7e5b26196ee511ea8a6bbddcfa3dceec0429"
_R1_FIXTURE_CONTENT_DIGEST = "7ac8f8ef52b7cb23f77d2150b23975f9f3f0cfcdc8e12005ea5c99f925fe1b6f"
_R1_IMPLEMENTATION_BASE = "bd4ecbecd699d0ea8177ff944d62b4cbcfee6170"
_Q1_POLICY_FIXTURE_DIGEST = "566d86da2d3ab3f9a44e380f38ed11858d021a2ac029517dd8f21d8a7e82f0b0"
_Q1_POLICY_DIGEST = "0705e8af012c36afc85c5af61d9a473ec8f3d369f877450acc9587be82281252"


class CalibrationDisclosureError(ValueError):
    """Raised when a Q1 disclosure policy violates its fixed safety boundary."""


class CalibrationStatus(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"


class DifficultyBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ScientificPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CommunicationReadiness(str, Enum):
    NOT_READY = "NOT_READY"


class DisclosureLimit(str, Enum):
    NO_STATISTICAL_PERFORMANCE = "NO_STATISTICAL_PERFORMANCE"
    NO_MATHEMATICAL_PROOF = "NO_MATHEMATICAL_PROOF"
    NO_OPEN_STATUS_CONFIRMATION = "NO_OPEN_STATUS_CONFIRMATION"
    NO_NOVELTY_ACCEPTANCE = "NO_NOVELTY_ACCEPTANCE"
    NO_PUBLIC_RELEASE = "NO_PUBLIC_RELEASE"


_REQUIRED_LIMITS = tuple(sorted(item.value for item in DisclosureLimit))
_EnumValue = TypeVar("_EnumValue", bound=Enum)


def _fields(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown or missing:
        raise CalibrationDisclosureError(
            f"{label} fields mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CalibrationDisclosureError(f"{label} must be non-empty text")
    return value


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise CalibrationDisclosureError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _string_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise CalibrationDisclosureError(f"{label} must be a text array")
    result = tuple(value)
    if result != tuple(sorted(result)) or len(result) != len(set(result)):
        raise CalibrationDisclosureError(f"{label} must be unique and sorted")
    return result


def _enum(value: object, enum_type: type[_EnumValue], label: str) -> _EnumValue:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise CalibrationDisclosureError(f"{label} has an unsupported value") from exc


@dataclass(frozen=True, slots=True)
class DifficultyRecord:
    """One manually declared difficulty record; it never infers research conclusions."""

    case_id: str
    predicted_difficulty: DifficultyBand
    calibration_status: CalibrationStatus
    scientific_priority: ScientificPriority
    communication_readiness: CommunicationReadiness
    disclosure_limits: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.case_id not in _CASE_IDS:
            raise CalibrationDisclosureError("unknown Q1 case_id")
        if self.calibration_status is not CalibrationStatus.UNCALIBRATED:
            raise CalibrationDisclosureError("all current Q1 predictions must be UNCALIBRATED")
        if self.communication_readiness is not CommunicationReadiness.NOT_READY:
            raise CalibrationDisclosureError("uncalibrated predictions are not communication-ready")
        if self.disclosure_limits != _REQUIRED_LIMITS:
            raise CalibrationDisclosureError("each record must retain every required disclosure limit")

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "predicted_difficulty": self.predicted_difficulty.value,
            "calibration_status": self.calibration_status.value,
            "scientific_priority": self.scientific_priority.value,
            "communication_readiness": self.communication_readiness.value,
            "disclosure_limits": list(self.disclosure_limits),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DifficultyRecord":
        _fields(
            value,
            {
                "case_id",
                "predicted_difficulty",
                "calibration_status",
                "scientific_priority",
                "communication_readiness",
                "disclosure_limits",
            },
            "difficulty record",
        )
        return cls(
            case_id=_text(value["case_id"], "case_id"),
            predicted_difficulty=_enum(value["predicted_difficulty"], DifficultyBand, "predicted_difficulty"),
            calibration_status=_enum(value["calibration_status"], CalibrationStatus, "calibration_status"),
            scientific_priority=_enum(value["scientific_priority"], ScientificPriority, "scientific_priority"),
            communication_readiness=_enum(
                value["communication_readiness"], CommunicationReadiness, "communication_readiness"
            ),
            disclosure_limits=_string_list(value["disclosure_limits"], "disclosure_limits"),
        )


@dataclass(frozen=True, slots=True)
class CalibrationDisclosurePolicy:
    """A pinned Q1 policy that can only expose uncalibrated, non-public records."""

    policy_id: str
    topic_id: str
    r1_evidence_id: str
    r1_evidence_sha256: str
    r1_fixture_sha256: str
    r1_fixture_content_sha256: str
    r1_implementation_base: str
    records: tuple[DifficultyRecord, ...]

    def __post_init__(self) -> None:
        _text(self.policy_id, "policy_id")
        if self.topic_id != "union-closed":
            raise CalibrationDisclosureError("Q1 policy must remain bound to union-closed")
        if (
            self.r1_evidence_id != _R1_EVIDENCE_ID
            or self.r1_evidence_sha256 != _R1_EVIDENCE_DIGEST
            or self.r1_fixture_sha256 != _R1_FIXTURE_DIGEST
            or self.r1_fixture_content_sha256 != _R1_FIXTURE_CONTENT_DIGEST
            or self.r1_implementation_base != _R1_IMPLEMENTATION_BASE
        ):
            raise CalibrationDisclosureError("R1 source identity drift")
        if tuple(record.case_id for record in self.records) != _CASE_IDS:
            raise CalibrationDisclosureError("Q1 records must match the accepted R1 case order")
        if self.policy_digest_sha256 != _Q1_POLICY_DIGEST:
            raise CalibrationDisclosureError("Q1 policy canonical identity drift")

    @property
    def policy_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": "1.0",
                "policy_id": self.policy_id,
                "topic_id": self.topic_id,
                "r1_evidence_id": self.r1_evidence_id,
                "r1_evidence_sha256": self.r1_evidence_sha256,
                "r1_fixture_sha256": self.r1_fixture_sha256,
                "r1_fixture_content_sha256": self.r1_fixture_content_sha256,
                "r1_implementation_base": self.r1_implementation_base,
                "records": [record.to_dict() for record in self.records],
                "public_release_allowed": False,
            }
        )

    @property
    def public_release_allowed(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "policy_id": self.policy_id,
            "topic_id": self.topic_id,
            "r1_evidence_id": self.r1_evidence_id,
            "r1_evidence_sha256": self.r1_evidence_sha256,
            "r1_fixture_sha256": self.r1_fixture_sha256,
            "r1_fixture_content_sha256": self.r1_fixture_content_sha256,
            "r1_implementation_base": self.r1_implementation_base,
            "records": [record.to_dict() for record in self.records],
            "public_release_allowed": False,
            "policy_digest_sha256": self.policy_digest_sha256,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CalibrationDisclosurePolicy":
        _fields(
            value,
            {
                "schema_version",
                "policy_id",
                "topic_id",
                "r1_evidence_id",
                "r1_evidence_sha256",
                "r1_fixture_sha256",
                "r1_fixture_content_sha256",
                "r1_implementation_base",
                "records",
                "public_release_allowed",
                "policy_digest_sha256",
            },
            "calibration disclosure policy",
        )
        if value["schema_version"] != "1.0":
            raise CalibrationDisclosureError("unsupported calibration disclosure schema")
        if value["public_release_allowed"] is not False:
            raise CalibrationDisclosureError("Q1 may not authorize a public release")
        records = value["records"]
        if not isinstance(records, list) or any(not isinstance(item, Mapping) for item in records):
            raise CalibrationDisclosureError("records must be an array of objects")
        policy = cls(
            policy_id=_text(value["policy_id"], "policy_id"),
            topic_id=_text(value["topic_id"], "topic_id"),
            r1_evidence_id=_text(value["r1_evidence_id"], "r1_evidence_id"),
            r1_evidence_sha256=_sha256(value["r1_evidence_sha256"], "r1_evidence_sha256"),
            r1_fixture_sha256=_sha256(value["r1_fixture_sha256"], "r1_fixture_sha256"),
            r1_fixture_content_sha256=_sha256(
                value["r1_fixture_content_sha256"], "r1_fixture_content_sha256"
            ),
            r1_implementation_base=_text(value["r1_implementation_base"], "r1_implementation_base"),
            records=tuple(DifficultyRecord.from_dict(item) for item in records),
        )
        if _sha256(value["policy_digest_sha256"], "policy_digest_sha256") != policy.policy_digest_sha256:
            raise CalibrationDisclosureError("policy digest mismatch")
        return policy

    @classmethod
    def from_fixture_bytes(cls, value: bytes) -> "CalibrationDisclosurePolicy":
        """Load only the byte-pinned checked-in Q1 policy fixture."""
        if not isinstance(value, bytes):
            raise CalibrationDisclosureError("Q1 policy fixture must be bytes")
        if hashlib.sha256(value).hexdigest() != _Q1_POLICY_FIXTURE_DIGEST:
            raise CalibrationDisclosureError("Q1 policy fixture byte identity drift")
        try:
            payload = json.loads(value)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CalibrationDisclosureError("Q1 policy fixture is not valid JSON") from exc
        if not isinstance(payload, Mapping):
            raise CalibrationDisclosureError("Q1 policy fixture must be a JSON object")
        return cls.from_dict(payload)
