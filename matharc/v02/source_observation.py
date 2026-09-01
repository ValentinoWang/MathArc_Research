"""Fail-closed records for observing external source material.

Observations are deliberately separate from :mod:`source_registry`: a
downloaded or summarized source is not a verified mathematical premise.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

from .schema import canonical_json, utc_now


class ObservationStatus(str, Enum):
    PENDING = "PENDING"
    OBSERVED = "OBSERVED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"


class LicenseStatus(str, Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUS_ASSERTION_LANGUAGE = re.compile(
    r"\b(?:proved|proof|solved|novel)\b|"
    r"\b(?:open|closed)\s+(?:problem|question|conjecture)\b|"
    r"\b(?:remains?|is|was)\s+(?:provably\s+)?open\b",
    re.I,
)
_MEDIA_TYPES = frozenset(
    {
        "application/json",
        "application/pdf",
        "application/octet-stream",
        "text/html",
        "text/plain",
    }
)


def _normalize_uri_for_identity(value: str) -> str:
    """Normalize URI authority without erasing case-sensitive resource paths."""

    candidate = value.strip()
    parsed = urlsplit(candidate)
    scheme = parsed.scheme.lower()
    if parsed.netloc:
        authority = parsed.netloc
        userinfo = ""
        host_port = authority
        if "@" in host_port:
            userinfo, host_port = host_port.rsplit("@", 1)
            userinfo += "@"
        if host_port.startswith("["):
            closing = host_port.find("]")
            if closing <= 1:
                raise ValueError("canonical_uri has an invalid IPv6 authority")
            host_port = host_port[: closing + 1].lower() + host_port[closing + 1 :]
        elif ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            host_port = host.lower() + ":" + port
        else:
            host_port = host_port.lower()
        normalized_netloc = userinfo + host_port
    else:
        normalized_netloc = parsed.netloc
    return urlunsplit(
        (
            scheme,
            normalized_netloc,
            parsed.path.rstrip("/"),
            parsed.query,
            parsed.fragment,
        )
    )


@dataclass(frozen=True, slots=True)
class SourceObservation:
    """A versioned, content-addressed observation of source material."""

    observation_id: str
    canonical_uri: str
    pinned_version: str
    observed_at: str
    license_status: LicenseStatus
    license_basis: str
    content_summary: str
    summary_basis: str
    media_type: str
    content_digest_sha256: str = ""
    artifact_id: str | None = None
    status: ObservationStatus = ObservationStatus.PENDING

    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not isinstance(self.license_status, LicenseStatus):
            raise TypeError("license_status must be a LicenseStatus")
        if not isinstance(self.status, ObservationStatus):
            raise TypeError("status must be an ObservationStatus")
        if not self.observation_id.strip():
            raise ValueError("observation_id must be non-empty")
        if not self.canonical_uri.strip() or "://" not in self.canonical_uri and not self.canonical_uri.startswith("urn:"):
            raise ValueError("canonical_uri must be an absolute URI or urn")
        if not self.pinned_version.strip() or self.pinned_version.strip().lower() == "latest":
            raise ValueError("pinned_version must be concrete, not latest")
        if not self.observed_at.strip():
            raise ValueError("observed_at must be non-empty")
        try:
            datetime.fromisoformat(self.observed_at)
        except ValueError as exc:
            raise ValueError("observed_at must be an ISO-8601 timestamp") from exc
        if not self.license_basis.strip():
            raise ValueError("license_basis must be non-empty")
        if not self.content_summary.strip() or not self.summary_basis.strip():
            raise ValueError("content summary and summary basis must be non-empty")
        if self.media_type not in _MEDIA_TYPES:
            raise ValueError(f"unsupported media_type: {self.media_type}")
        if self.content_digest_sha256 and not _DIGEST_RE.fullmatch(self.content_digest_sha256):
            raise ValueError("content_digest_sha256 must be a lowercase SHA-256 digest")
        if self.status is ObservationStatus.OBSERVED and self.license_status is LicenseStatus.UNKNOWN:
            raise ValueError("unknown license cannot produce an OBSERVED record")
        if _STATUS_ASSERTION_LANGUAGE.search(self.content_summary):
            raise ValueError("content_summary must remain descriptive, not proof/status language")

    @property
    def logical_identity(self) -> str:
        return canonical_json(
            {
                "canonical_uri": _normalize_uri_for_identity(self.canonical_uri),
                "pinned_version": self.pinned_version.strip(),
            }
        )

    @property
    def idempotency_key(self) -> str:
        payload = canonical_json(
            {
                "content_digest_sha256": self.content_digest_sha256,
                "logical_identity": self.logical_identity,
            }
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def conflicts_with(self, other: "SourceObservation") -> bool:
        return self.logical_identity == other.logical_identity and (
            bool(self.content_digest_sha256)
            and bool(other.content_digest_sha256)
            and self.content_digest_sha256 != other.content_digest_sha256
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "observation_id": self.observation_id,
            "canonical_uri": self.canonical_uri,
            "pinned_version": self.pinned_version,
            "observed_at": self.observed_at,
            "license_status": self.license_status.value,
            "license_basis": self.license_basis,
            "content_summary": self.content_summary,
            "summary_basis": self.summary_basis,
            "media_type": self.media_type,
            "content_digest_sha256": self.content_digest_sha256,
            "artifact_id": self.artifact_id,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceObservation":
        allowed = {
            "schema_version", "observation_id", "canonical_uri", "pinned_version",
            "observed_at", "license_status", "license_basis", "content_summary",
            "summary_basis", "media_type", "content_digest_sha256", "artifact_id", "status",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown source-observation fields: {sorted(unknown)}")
        if str(payload.get("schema_version", "1.0")) != "1.0":
            raise ValueError("unsupported source-observation schema_version")
        return cls(
            observation_id=str(payload["observation_id"]),
            canonical_uri=str(payload["canonical_uri"]),
            pinned_version=str(payload["pinned_version"]),
            observed_at=str(payload["observed_at"]),
            license_status=LicenseStatus(str(payload["license_status"])),
            license_basis=str(payload["license_basis"]),
            content_summary=str(payload["content_summary"]),
            summary_basis=str(payload["summary_basis"]),
            media_type=str(payload["media_type"]),
            content_digest_sha256=str(payload.get("content_digest_sha256", "")),
            artifact_id=(str(payload["artifact_id"]) if payload.get("artifact_id") is not None else None),
            status=ObservationStatus(str(payload.get("status", ObservationStatus.PENDING.value))),
            schema_version="1.0",
        )


def new_observation(**kwargs: Any) -> SourceObservation:
    """Create an observation with the current UTC timestamp by default."""

    kwargs.setdefault("observed_at", utc_now())
    return SourceObservation(**kwargs)
