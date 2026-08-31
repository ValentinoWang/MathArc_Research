"""Fail-closed, versioned open-problem status records.

This module deliberately does not infer mathematical or literature status.
It only determines whether a previously issued open-status certificate still
matches an immutable statement and its observed sources at a supplied time.
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from .schema import digest_json
from .artifact_store import ArtifactStore
from .source_observation import LicenseStatus, ObservationStatus, SourceObservation


_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_VERSION = "1.0"


class ProblemStatus(str, Enum):
    """Reported problem states, deliberately separate from ``ClaimStatus``."""

    UNASSESSED = "UNASSESSED"
    OPEN_REPORTED = "OPEN_REPORTED"
    RESOLVED_REPORTED = "RESOLVED_REPORTED"
    CONTESTED = "CONTESTED"
    STALE = "STALE"


class StatusInvalidation(str, Enum):
    """Reasons an open-status assertion cannot be used."""

    INVALID_INPUT = "INVALID_INPUT"
    MISSING_CERTIFICATE = "MISSING_CERTIFICATE"
    PROBLEM_ID_MISMATCH = "PROBLEM_ID_MISMATCH"
    STATEMENT_VERSION_MISMATCH = "STATEMENT_VERSION_MISMATCH"
    STATEMENT_DIGEST_MISMATCH = "STATEMENT_DIGEST_MISMATCH"
    CERTIFICATE_NOT_YET_ISSUED = "CERTIFICATE_NOT_YET_ISSUED"
    CERTIFICATE_EXPIRED = "CERTIFICATE_EXPIRED"
    SOURCE_AFTER_CERTIFICATE_ISSUED = "SOURCE_AFTER_CERTIFICATE_ISSUED"
    SNAPSHOT_PREDATES_CERTIFICATE = "SNAPSHOT_PREDATES_CERTIFICATE"
    MISSING_SOURCE = "MISSING_SOURCE"
    SOURCE_NOT_YET_OBSERVED = "SOURCE_NOT_YET_OBSERVED"
    SNAPSHOT_NOT_YET_CREATED = "SNAPSHOT_NOT_YET_CREATED"
    SOURCE_DIGEST_MISMATCH = "SOURCE_DIGEST_MISMATCH"
    SOURCE_NOT_OBSERVED = "SOURCE_NOT_OBSERVED"
    SOURCE_LICENSE_NOT_OPEN = "SOURCE_LICENSE_NOT_OPEN"
    SOURCE_ARTIFACT_MISSING = "SOURCE_ARTIFACT_MISSING"
    SOURCE_ARTIFACT_INVALID = "SOURCE_ARTIFACT_INVALID"


def _require_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _require_digest(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _parse_timestamp(value: str, field_name: str) -> datetime:
    _require_nonempty(value, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp with an offset") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp with an offset")
    return parsed


def _require_positive_version(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def _require_fields(payload: Mapping[str, Any], expected: set[str], record_name: str) -> None:
    unknown = set(payload) - expected
    if unknown:
        raise ValueError(f"unknown {record_name} fields: {sorted(unknown)}")
    missing = expected - set(payload)
    if missing:
        raise ValueError(f"missing {record_name} fields: {sorted(missing)}")


def source_observation_digest_sha256(observation: SourceObservation) -> str:
    """Return the digest of every source field relied on by a certificate."""

    if not isinstance(observation, SourceObservation):
        raise TypeError("observation must be a SourceObservation")
    return digest_json(observation.to_dict())


@dataclass(frozen=True, slots=True)
class StatementVersion:
    """An immutable version of one problem statement."""

    problem_id: str
    version: int
    statement: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_nonempty(self.problem_id, "problem_id")
        _require_positive_version(self.version, "version")
        _require_nonempty(self.statement, "statement")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported statement-version schema_version")

    @property
    def statement_version_id(self) -> str:
        return f"{self.problem_id}@{self.version}"

    @property
    def statement_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": self.schema_version,
                "problem_id": self.problem_id,
                "version": self.version,
                "statement": self.statement,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "problem_id": self.problem_id,
            "version": self.version,
            "statement": self.statement,
            "statement_digest_sha256": self.statement_digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "StatementVersion":
        expected = {"schema_version", "problem_id", "version", "statement", "statement_digest_sha256"}
        _require_fields(payload, expected, "statement-version")
        value = cls(
            problem_id=str(payload["problem_id"]),
            version=payload["version"],
            statement=str(payload["statement"]),
            schema_version=str(payload["schema_version"]),
        )
        if payload["statement_digest_sha256"] != value.statement_digest_sha256:
            raise ValueError("statement-version digest mismatch")
        return value


@dataclass(frozen=True, slots=True)
class ObservationDigestRef:
    """The exact observed-source version used when a certificate was issued."""

    observation_id: str
    observation_digest_sha256: str

    def __post_init__(self) -> None:
        _require_nonempty(self.observation_id, "observation_id")
        _require_digest(self.observation_digest_sha256, "observation_digest_sha256")

    @classmethod
    def from_observation(cls, observation: SourceObservation) -> "ObservationDigestRef":
        return cls(observation.observation_id, source_observation_digest_sha256(observation))

    def to_dict(self) -> dict[str, str]:
        return {
            "observation_id": self.observation_id,
            "observation_digest_sha256": self.observation_digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObservationDigestRef":
        expected = {"observation_id", "observation_digest_sha256"}
        _require_fields(payload, expected, "observation-digest-ref")
        return cls(
            observation_id=str(payload["observation_id"]),
            observation_digest_sha256=str(payload["observation_digest_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class OpenStatusCertificate:
    """An immutable, expiring report on a statement's observed research status."""

    certificate_id: str
    problem_id: str
    version: int
    statement_version_id: str
    statement_digest_sha256: str
    source_observations: tuple[ObservationDigestRef, ...]
    status: ProblemStatus
    limitations: tuple[str, ...]
    reviewer: str
    issued_at: str
    expires_at: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_nonempty(self.certificate_id, "certificate_id")
        _require_nonempty(self.problem_id, "problem_id")
        _require_positive_version(self.version, "version")
        _require_nonempty(self.statement_version_id, "statement_version_id")
        _require_digest(self.statement_digest_sha256, "statement_digest_sha256")
        if not isinstance(self.source_observations, tuple):
            raise TypeError("source_observations must be a tuple")
        if not self.source_observations:
            raise ValueError("source_observations must be non-empty")
        if any(not isinstance(item, ObservationDigestRef) for item in self.source_observations):
            raise TypeError("source_observations must contain ObservationDigestRef values")
        source_ids = tuple(item.observation_id for item in self.source_observations)
        if source_ids != tuple(sorted(source_ids)) or len(set(source_ids)) != len(source_ids):
            raise ValueError("source_observations must have unique observation ids in sorted order")
        if not isinstance(self.status, ProblemStatus):
            raise TypeError("status must be a ProblemStatus")
        if self.status not in {
            ProblemStatus.OPEN_REPORTED,
            ProblemStatus.RESOLVED_REPORTED,
            ProblemStatus.CONTESTED,
        }:
            raise ValueError("certificate status must be a reportable problem status")
        if not isinstance(self.limitations, tuple):
            raise TypeError("limitations must be a tuple")
        if not self.limitations or any(not isinstance(item, str) or not item.strip() for item in self.limitations):
            raise ValueError("limitations must contain non-empty strings")
        _require_nonempty(self.reviewer, "reviewer")
        issued_at = _parse_timestamp(self.issued_at, "issued_at")
        expires_at = _parse_timestamp(self.expires_at, "expires_at")
        if expires_at <= issued_at:
            raise ValueError("expires_at must be after issued_at")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported open-status-certificate schema_version")

    @property
    def certificate_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": self.schema_version,
                "certificate_id": self.certificate_id,
                "problem_id": self.problem_id,
                "version": self.version,
                "statement_version_id": self.statement_version_id,
                "statement_digest_sha256": self.statement_digest_sha256,
                "source_observations": [item.to_dict() for item in self.source_observations],
                "status": self.status.value,
                "limitations": list(self.limitations),
                "reviewer": self.reviewer,
                "issued_at": self.issued_at,
                "expires_at": self.expires_at,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "certificate_id": self.certificate_id,
            "problem_id": self.problem_id,
            "version": self.version,
            "statement_version_id": self.statement_version_id,
            "statement_digest_sha256": self.statement_digest_sha256,
            "source_observations": [item.to_dict() for item in self.source_observations],
            "status": self.status.value,
            "limitations": list(self.limitations),
            "reviewer": self.reviewer,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "certificate_digest_sha256": self.certificate_digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OpenStatusCertificate":
        expected = {
            "schema_version", "certificate_id", "problem_id", "version", "statement_version_id",
            "statement_digest_sha256", "source_observations", "status", "limitations", "reviewer", "issued_at", "expires_at",
            "certificate_digest_sha256",
        }
        _require_fields(payload, expected, "open-status-certificate")
        sources = payload["source_observations"]
        if not isinstance(sources, list):
            raise ValueError("source_observations must be a list")
        limitations = payload["limitations"]
        if not isinstance(limitations, list):
            raise ValueError("limitations must be a list")
        value = cls(
            certificate_id=str(payload["certificate_id"]),
            problem_id=str(payload["problem_id"]),
            version=payload["version"],
            statement_version_id=str(payload["statement_version_id"]),
            statement_digest_sha256=str(payload["statement_digest_sha256"]),
            source_observations=tuple(ObservationDigestRef.from_dict(item) for item in sources),
            status=ProblemStatus(str(payload["status"])),
            limitations=tuple(str(item) for item in limitations),
            reviewer=str(payload["reviewer"]),
            issued_at=str(payload["issued_at"]),
            expires_at=str(payload["expires_at"]),
            schema_version=str(payload["schema_version"]),
        )
        if payload["certificate_digest_sha256"] != value.certificate_digest_sha256:
            raise ValueError("open-status-certificate digest mismatch")
        return value


@dataclass(frozen=True, slots=True)
class ProblemDossierSnapshot:
    """An immutable dossier snapshot whose open status must be revalidated."""

    snapshot_id: str
    problem_id: str
    version: int
    statement: StatementVersion
    certificate: OpenStatusCertificate | None
    snapshot_at: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_nonempty(self.snapshot_id, "snapshot_id")
        _require_nonempty(self.problem_id, "problem_id")
        _require_positive_version(self.version, "version")
        if not isinstance(self.statement, StatementVersion):
            raise TypeError("statement must be a StatementVersion")
        if self.certificate is not None and not isinstance(self.certificate, OpenStatusCertificate):
            raise TypeError("certificate must be an OpenStatusCertificate or None")
        _parse_timestamp(self.snapshot_at, "snapshot_at")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported problem-dossier-snapshot schema_version")

    @property
    def snapshot_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": self.schema_version,
                "snapshot_id": self.snapshot_id,
                "problem_id": self.problem_id,
                "version": self.version,
                "statement": self.statement.to_dict(),
                "certificate": self.certificate.to_dict() if self.certificate else None,
                "snapshot_at": self.snapshot_at,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "problem_id": self.problem_id,
            "version": self.version,
            "statement": self.statement.to_dict(),
            "certificate": self.certificate.to_dict() if self.certificate else None,
            "snapshot_at": self.snapshot_at,
            "snapshot_digest_sha256": self.snapshot_digest_sha256,
        }

    def validate(
        self,
        observations: Mapping[str, SourceObservation],
        *,
        as_of: str,
        artifacts: ArtifactStore | None = None,
    ) -> "ProblemStatusValidation":
        return validate(self, observations, as_of=as_of, artifacts=artifacts)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProblemDossierSnapshot":
        expected = {
            "schema_version", "snapshot_id", "problem_id", "version", "statement", "certificate",
            "snapshot_at", "snapshot_digest_sha256",
        }
        _require_fields(payload, expected, "problem-dossier-snapshot")
        if not isinstance(payload["statement"], Mapping):
            raise ValueError("statement must be an object")
        certificate = payload["certificate"]
        if certificate is not None and not isinstance(certificate, Mapping):
            raise ValueError("certificate must be an object or null")
        value = cls(
            snapshot_id=str(payload["snapshot_id"]),
            problem_id=str(payload["problem_id"]),
            version=payload["version"],
            statement=StatementVersion.from_dict(payload["statement"]),
            certificate=OpenStatusCertificate.from_dict(certificate) if certificate is not None else None,
            snapshot_at=str(payload["snapshot_at"]),
            schema_version=str(payload["schema_version"]),
        )
        if payload["snapshot_digest_sha256"] != value.snapshot_digest_sha256:
            raise ValueError("problem-dossier-snapshot digest mismatch")
        return value


@dataclass(frozen=True, slots=True)
class ProblemStatusValidation:
    """The pure validation result for one snapshot at one explicit time."""

    status: ProblemStatus
    invalidations: tuple[StatusInvalidation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, ProblemStatus):
            raise TypeError("status must be a ProblemStatus")
        if not isinstance(self.invalidations, tuple):
            raise TypeError("invalidations must be a tuple")
        if any(not isinstance(item, StatusInvalidation) for item in self.invalidations):
            raise TypeError("invalidations must contain StatusInvalidation values")
        if self.status is ProblemStatus.STALE and not self.invalidations:
            raise ValueError("STALE status must explain why it is fail-closed")
        if self.status in {ProblemStatus.UNASSESSED, ProblemStatus.OPEN_REPORTED, ProblemStatus.RESOLVED_REPORTED, ProblemStatus.CONTESTED} and self.invalidations:
            raise ValueError("a non-stale status cannot have invalidations")

    @property
    def is_open(self) -> bool:
        return self.status is ProblemStatus.OPEN_REPORTED


def validate(
    snapshot: ProblemDossierSnapshot,
    observations: Mapping[str, SourceObservation],
    *,
    as_of: str,
    artifacts: ArtifactStore | None = None,
) -> ProblemStatusValidation:
    """Validate without mutating inputs; invalid input fails closed."""

    if not isinstance(snapshot, ProblemDossierSnapshot) or not isinstance(observations, Mapping):
        return ProblemStatusValidation(ProblemStatus.STALE, (StatusInvalidation.INVALID_INPUT,))
    try:
        snapshot_at = _parse_timestamp(snapshot.snapshot_at, "snapshot_at")
        now = _parse_timestamp(as_of, "as_of")
        if now < snapshot_at:
            return ProblemStatusValidation(
                ProblemStatus.STALE,
                (StatusInvalidation.SNAPSHOT_NOT_YET_CREATED,),
            )
        certificate = snapshot.certificate
        if certificate is None:
            return ProblemStatusValidation(ProblemStatus.UNASSESSED)
        issued_at = _parse_timestamp(certificate.issued_at, "issued_at")
        expires_at = _parse_timestamp(certificate.expires_at, "expires_at")
        if expires_at <= issued_at:
            return ProblemStatusValidation(ProblemStatus.STALE, (StatusInvalidation.INVALID_INPUT,))

        invalidations: list[StatusInvalidation] = []
        if snapshot.problem_id != snapshot.statement.problem_id or certificate.problem_id != snapshot.problem_id:
            invalidations.append(StatusInvalidation.PROBLEM_ID_MISMATCH)
        if certificate.statement_version_id != snapshot.statement.statement_version_id:
            invalidations.append(StatusInvalidation.STATEMENT_VERSION_MISMATCH)
        if certificate.statement_digest_sha256 != snapshot.statement.statement_digest_sha256:
            invalidations.append(StatusInvalidation.STATEMENT_DIGEST_MISMATCH)
        if now < issued_at:
            invalidations.append(StatusInvalidation.CERTIFICATE_NOT_YET_ISSUED)
        if now >= expires_at:
            invalidations.append(StatusInvalidation.CERTIFICATE_EXPIRED)
        if snapshot_at < issued_at:
            invalidations.append(StatusInvalidation.SNAPSHOT_PREDATES_CERTIFICATE)

        for reference in certificate.source_observations:
            observation = observations.get(reference.observation_id)
            if not isinstance(observation, SourceObservation):
                invalidations.append(StatusInvalidation.MISSING_SOURCE)
                continue
            observed_at = _parse_timestamp(observation.observed_at, "observed_at")
            if now < observed_at:
                invalidations.append(StatusInvalidation.SOURCE_NOT_YET_OBSERVED)
            if observed_at > issued_at:
                invalidations.append(StatusInvalidation.SOURCE_AFTER_CERTIFICATE_ISSUED)
            if source_observation_digest_sha256(observation) != reference.observation_digest_sha256:
                invalidations.append(StatusInvalidation.SOURCE_DIGEST_MISMATCH)
            if observation.status is not ObservationStatus.OBSERVED:
                invalidations.append(StatusInvalidation.SOURCE_NOT_OBSERVED)
            if observation.license_status is not LicenseStatus.OPEN:
                invalidations.append(StatusInvalidation.SOURCE_LICENSE_NOT_OPEN)
            if not observation.artifact_id or not observation.content_digest_sha256:
                invalidations.append(StatusInvalidation.SOURCE_ARTIFACT_MISSING)
            elif not _is_intact_source_artifact(observation, artifacts):
                invalidations.append(StatusInvalidation.SOURCE_ARTIFACT_INVALID)

        if invalidations:
            return ProblemStatusValidation(ProblemStatus.STALE, tuple(dict.fromkeys(invalidations)))
        return ProblemStatusValidation(certificate.status)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return ProblemStatusValidation(ProblemStatus.STALE, (StatusInvalidation.INVALID_INPUT,))


def _is_intact_source_artifact(observation: SourceObservation, artifacts: ArtifactStore | None) -> bool:
    """Require the stored bytes, not just an observation's declared artifact id."""

    if artifacts is None or observation.artifact_id is None:
        return False
    try:
        artifact = artifacts.get(observation.artifact_id)
        path = artifacts.path_for(observation.artifact_id)
        content = path.read_bytes()
    except (KeyError, OSError, ValueError):
        return False
    return (
        path.is_file()
        and artifact.sha256 == observation.content_digest_sha256
        and artifact.size_bytes == len(content)
        and artifact.media_type == observation.media_type
        and artifact.logical_role == "literature-observation"
        and artifact.producer == "matharc-literature-base"
        and hashlib.sha256(content).hexdigest() == artifact.sha256
    )
