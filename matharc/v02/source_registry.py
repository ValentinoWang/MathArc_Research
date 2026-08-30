from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import digest_json, utc_now


class SourceClaimStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class SourceKind(str, Enum):
    PAPER = "PAPER"
    BOOK = "BOOK"
    PREPRINT = "PREPRINT"
    FORMAL_LIBRARY = "FORMAL_LIBRARY"
    DATASET = "DATASET"
    SOFTWARE = "SOFTWARE"
    PRIMARY_WEB_SOURCE = "PRIMARY_WEB_SOURCE"
    OTHER = "OTHER"


@dataclass(slots=True)
class SourceClaim:
    source_claim_id: str
    source_kind: SourceKind
    bibliographic_citation: str
    canonical_uri: str
    pinned_version: str
    locator: str
    claimed_result: str
    applicability_conditions: tuple[str, ...]
    linked_claim_ids: tuple[str, ...] = ()
    status: SourceClaimStatus = SourceClaimStatus.PENDING
    source_digest_sha256: str = ""
    verified_by: str = ""
    verification_method: str = ""
    statement_correspondence: str = ""
    limitations: tuple[str, ...] = ()
    supersedes: str | None = None
    accessed_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_claim_id": self.source_claim_id,
            "source_kind": self.source_kind.value,
            "bibliographic_citation": self.bibliographic_citation,
            "canonical_uri": self.canonical_uri,
            "pinned_version": self.pinned_version,
            "locator": self.locator,
            "claimed_result": self.claimed_result,
            "applicability_conditions": list(self.applicability_conditions),
            "linked_claim_ids": list(self.linked_claim_ids),
            "status": self.status.value,
            "source_digest_sha256": self.source_digest_sha256,
            "verified_by": self.verified_by,
            "verification_method": self.verification_method,
            "statement_correspondence": self.statement_correspondence,
            "limitations": list(self.limitations),
            "supersedes": self.supersedes,
            "accessed_at": self.accessed_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceClaim":
        allowed = {
            "source_claim_id",
            "source_kind",
            "bibliographic_citation",
            "canonical_uri",
            "pinned_version",
            "locator",
            "claimed_result",
            "applicability_conditions",
            "linked_claim_ids",
            "status",
            "source_digest_sha256",
            "verified_by",
            "verification_method",
            "statement_correspondence",
            "limitations",
            "supersedes",
            "accessed_at",
            "updated_at",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown source-claim fields: {sorted(unknown)}")
        return cls(
            source_claim_id=str(payload["source_claim_id"]),
            source_kind=SourceKind(str(payload["source_kind"])),
            bibliographic_citation=str(payload["bibliographic_citation"]),
            canonical_uri=str(payload["canonical_uri"]),
            pinned_version=str(payload["pinned_version"]),
            locator=str(payload["locator"]),
            claimed_result=str(payload["claimed_result"]),
            applicability_conditions=tuple(
                str(item) for item in payload.get("applicability_conditions", [])
            ),
            linked_claim_ids=tuple(
                str(item) for item in payload.get("linked_claim_ids", [])
            ),
            status=SourceClaimStatus(
                str(payload.get("status", SourceClaimStatus.PENDING.value))
            ),
            source_digest_sha256=str(payload.get("source_digest_sha256", "")),
            verified_by=str(payload.get("verified_by", "")),
            verification_method=str(payload.get("verification_method", "")),
            statement_correspondence=str(payload.get("statement_correspondence", "")),
            limitations=tuple(str(item) for item in payload.get("limitations", [])),
            supersedes=(
                str(payload["supersedes"])
                if payload.get("supersedes") is not None
                else None
            ),
            accessed_at=str(payload.get("accessed_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
        )


class SourceRegistry:
    """Registry for external mathematical results and open-status claims.

    An external theorem can become a usable premise only after the exact source
    version, locator, applicability conditions, source digest and statement
    correspondence have been verified.  A citation string alone is never a
    proof dependency.
    """

    def __init__(self, claims: Iterable[SourceClaim] = ()) -> None:
        self._claims: dict[str, SourceClaim] = {}
        for claim in claims:
            self.add(claim)

    @property
    def claims(self) -> tuple[SourceClaim, ...]:
        return tuple(self._claims[key] for key in sorted(self._claims))

    def get(self, source_claim_id: str) -> SourceClaim:
        try:
            return self._claims[source_claim_id]
        except KeyError as exc:
            raise KeyError(f"unknown source claim: {source_claim_id}") from exc

    def add(self, claim: SourceClaim) -> None:
        if claim.source_claim_id in self._claims:
            raise ValueError(f"duplicate source-claim id: {claim.source_claim_id}")
        if claim.supersedes is not None and claim.supersedes not in self._claims:
            raise ValueError(
                f"source claim {claim.source_claim_id} supersedes unknown record {claim.supersedes}"
            )
        if claim.status is SourceClaimStatus.VERIFIED:
            issues = self.verification_issues(claim)
            if issues:
                raise ValueError("; ".join(issues))
        self._claims[claim.source_claim_id] = claim
        if claim.supersedes is not None:
            prior = self._claims[claim.supersedes]
            prior.status = SourceClaimStatus.SUPERSEDED
            prior.updated_at = utc_now()

    def verify(
        self,
        source_claim_id: str,
        *,
        source_digest_sha256: str,
        verified_by: str,
        verification_method: str,
        statement_correspondence: str,
    ) -> SourceClaim:
        claim = self.get(source_claim_id)
        if claim.status in {SourceClaimStatus.REJECTED, SourceClaimStatus.SUPERSEDED}:
            raise ValueError(
                f"terminal source claim cannot be verified: {source_claim_id}"
            )
        claim.source_digest_sha256 = source_digest_sha256
        claim.verified_by = verified_by
        claim.verification_method = verification_method
        claim.statement_correspondence = statement_correspondence
        issues = self.verification_issues(claim)
        if issues:
            raise ValueError("; ".join(issues))
        claim.status = SourceClaimStatus.VERIFIED
        claim.updated_at = utc_now()
        return claim

    def reject(self, source_claim_id: str, reason: str) -> None:
        claim = self.get(source_claim_id)
        claim.status = SourceClaimStatus.REJECTED
        claim.limitations = tuple(dict.fromkeys((*claim.limitations, reason)))
        claim.updated_at = utc_now()

    def usable_for_claim(self, source_claim_id: str, claim_id: str) -> bool:
        claim = self.get(source_claim_id)
        return (
            claim.status is SourceClaimStatus.VERIFIED
            and claim_id in claim.linked_claim_ids
            and not self.verification_issues(claim)
        )

    def verification_issues(self, claim: SourceClaim) -> list[str]:
        issues: list[str] = []
        required = {
            "bibliographic_citation": claim.bibliographic_citation,
            "canonical_uri": claim.canonical_uri,
            "pinned_version": claim.pinned_version,
            "locator": claim.locator,
            "claimed_result": claim.claimed_result,
            "source_digest_sha256": claim.source_digest_sha256,
            "verified_by": claim.verified_by,
            "verification_method": claim.verification_method,
            "statement_correspondence": claim.statement_correspondence,
        }
        for field_name, value in required.items():
            if not value.strip():
                issues.append(f"source claim {claim.source_claim_id} lacks {field_name}")
        if claim.source_digest_sha256 and len(claim.source_digest_sha256) != 64:
            issues.append(
                f"source claim {claim.source_claim_id} has a non-SHA-256 digest"
            )
        if not claim.applicability_conditions:
            issues.append(
                f"source claim {claim.source_claim_id} lacks applicability conditions"
            )
        if not claim.linked_claim_ids:
            issues.append(f"source claim {claim.source_claim_id} is not linked to a claim")
        return issues

    def validate(self, known_claim_ids: Iterable[str] = ()) -> dict[str, Any]:
        known = set(known_claim_ids)
        errors: list[str] = []
        warnings: list[str] = []
        for claim in self._claims.values():
            missing = [claim_id for claim_id in claim.linked_claim_ids if known and claim_id not in known]
            if missing:
                errors.append(
                    f"source claim {claim.source_claim_id} links unknown claims {missing}"
                )
            issues = self.verification_issues(claim)
            if claim.status is SourceClaimStatus.VERIFIED:
                errors.extend(issues)
            elif claim.status is SourceClaimStatus.PENDING:
                warnings.extend(issues)
        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "source_claim_count": len(self._claims),
            "verified_count": sum(
                claim.status is SourceClaimStatus.VERIFIED
                for claim in self._claims.values()
            ),
            "pending_count": sum(
                claim.status is SourceClaimStatus.PENDING
                for claim in self._claims.values()
            ),
            "registry_digest_sha256": digest_json(self.to_dict()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "claims": [item.to_dict() for item in self.claims],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceRegistry":
        if set(payload) - {"schema_version", "claims"}:
            raise ValueError("unknown source-registry fields")
        if str(payload.get("schema_version")) != "1.0":
            raise ValueError("unsupported source-registry schema")
        registry = cls()
        pending = [SourceClaim.from_dict(item) for item in payload.get("claims", [])]
        while pending:
            progress = False
            for item in pending[:]:
                if item.supersedes is None or item.supersedes in registry._claims:
                    registry.add(item)
                    pending.remove(item)
                    progress = True
            if not progress:
                unresolved = {
                    item.source_claim_id: item.supersedes for item in pending
                }
                raise ValueError(f"unresolvable source supersession chain: {unresolved}")
        return registry

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    @classmethod
    def load(cls, path: str | Path) -> "SourceRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("source-registry root must be an object")
        return cls.from_dict(payload)
