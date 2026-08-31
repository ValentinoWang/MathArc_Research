"""Fail-closed, human-reviewed novelty audit records.

This module records literature-search coverage for a *candidate result*.  It
does not infer problem status, change claim state, or promote mathematical
conclusions.  In particular, an audit cannot grant a complete research budget
or a public qualitative conclusion until all four prescribed search routes
have completed and a human literature auditor has approved the recorded
outcome.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from .artifact_store import ArtifactStore
from .schema import digest_json
from .source_observation import LicenseStatus, ObservationStatus, SourceObservation


_SCHEMA_VERSION = "1.0"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROUTE_ORDER = (
    "FORWARD_CITATION",
    "ALIAS_AND_EQUIVALENCE",
    "STRUCTURAL_SEMANTIC",
    "REVIEW_AND_EXPERT_LEAD",
)


class SearchRoute(str, Enum):
    """The four independent routes required by the S2 audit contract."""

    FORWARD_CITATION = "FORWARD_CITATION"
    ALIAS_AND_EQUIVALENCE = "ALIAS_AND_EQUIVALENCE"
    STRUCTURAL_SEMANTIC = "STRUCTURAL_SEMANTIC"
    REVIEW_AND_EXPERT_LEAD = "REVIEW_AND_EXPERT_LEAD"


class NoveltyConclusion(str, Enum):
    """A scope-bounded audit outcome, not a mathematical claim status."""

    UNASSESSED = "UNASSESSED"
    NO_PRIOR_RESULT_FOUND = "NO_PRIOR_RESULT_FOUND"
    PRIOR_RESULT_FOUND = "PRIOR_RESULT_FOUND"
    INCONCLUSIVE = "INCONCLUSIVE"


class HumanAuditVerdict(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_FOLLOW_UP = "NEEDS_FOLLOW_UP"


class NoveltyAuditStatus(str, Enum):
    PENDING_HUMAN_AUDIT = "PENDING_HUMAN_AUDIT"
    PENDING_SOURCE_VERIFICATION = "PENDING_SOURCE_VERIFICATION"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    AUDITED = "AUDITED"
    STALE = "STALE"


class NoveltyInvalidation(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_ROUTE = "MISSING_ROUTE"
    INCOMPLETE_ROUTE = "INCOMPLETE_ROUTE"
    MISSING_HUMAN_AUDIT = "MISSING_HUMAN_AUDIT"
    HUMAN_AUDIT_NOT_APPROVED = "HUMAN_AUDIT_NOT_APPROVED"
    UNASSESSED_CONCLUSION = "UNASSESSED_CONCLUSION"
    ROUTE_NOT_INDEPENDENT = "ROUTE_NOT_INDEPENDENT"
    TEMPORAL_ORDER_VIOLATION = "TEMPORAL_ORDER_VIOLATION"
    SOURCE_SUPPORT_NOT_VERIFIED = "SOURCE_SUPPORT_NOT_VERIFIED"
    CONTRACT_ONLY_RECORD = "CONTRACT_ONLY_RECORD"


class NoveltyAuditPurpose(str, Enum):
    """Whether a record may be used to authorize a real research consumer."""

    LIVE_AUDIT = "LIVE_AUDIT"
    CONTRACT_FIXTURE = "CONTRACT_FIXTURE"


def _require_nonempty(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _require_digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_timestamp(value: object, field_name: str) -> str:
    value = _require_nonempty(value, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp with an offset") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp with an offset")
    return value


def _parse_timestamp(value: object, field_name: str) -> datetime:
    return datetime.fromisoformat(_require_timestamp(value, field_name))


def _require_fields(payload: Mapping[str, Any], expected: set[str], record_name: str) -> None:
    unknown = set(payload) - expected
    if unknown:
        raise ValueError(f"unknown {record_name} fields: {sorted(unknown)}")
    missing = expected - set(payload)
    if missing:
        raise ValueError(f"missing {record_name} fields: {sorted(missing)}")


def _require_tuple(value: object, field_name: str) -> tuple[Any, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    return value


def _require_unique(values: tuple[Any, ...], field_name: str, key: Any) -> None:
    identifiers = tuple(key(item) for item in values)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{field_name} must not contain duplicates")


def _require_sorted(values: tuple[Any, ...], field_name: str, key: Any) -> None:
    if tuple(sorted(values, key=key)) != values:
        raise ValueError(f"{field_name} must be deterministically sorted")


def _normalized_search_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _stable_source_identity(support: SourceSupport) -> tuple[str, str, str]:
    """Identify a source independently of the local audit-only source ID."""

    return (
        support.canonical_uri.strip().rstrip("/").lower(),
        support.pinned_version.strip(),
        support.source_fingerprint_sha256,
    )


@dataclass(frozen=True, slots=True)
class SourceSupport:
    """A pinned source location supporting either candidate or search result."""

    source_id: str
    canonical_uri: str
    pinned_version: str
    locator: str
    source_fingerprint_sha256: str

    def __post_init__(self) -> None:
        _require_nonempty(self.source_id, "source_id")
        uri = _require_nonempty(self.canonical_uri, "canonical_uri")
        if "://" not in uri and not uri.startswith("urn:"):
            raise ValueError("canonical_uri must be an absolute URI or urn")
        _require_nonempty(self.pinned_version, "pinned_version")
        _require_nonempty(self.locator, "locator")
        _require_digest(self.source_fingerprint_sha256, "source_fingerprint_sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "canonical_uri": self.canonical_uri,
            "pinned_version": self.pinned_version,
            "locator": self.locator,
            "source_fingerprint_sha256": self.source_fingerprint_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceSupport":
        expected = {"source_id", "canonical_uri", "pinned_version", "locator", "source_fingerprint_sha256"}
        _require_fields(payload, expected, "source-support")
        return cls(**{key: payload[key] for key in expected})


@dataclass(frozen=True, slots=True)
class CandidateResult:
    """The versioned candidate result whose novelty is being audited."""

    candidate_id: str
    candidate_fingerprint_sha256: str
    scope: str
    version: str
    source_support: tuple[SourceSupport, ...]
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_nonempty(self.candidate_id, "candidate_id")
        _require_digest(self.candidate_fingerprint_sha256, "candidate_fingerprint_sha256")
        _require_nonempty(self.scope, "scope")
        _require_nonempty(self.version, "version")
        sources = _require_tuple(self.source_support, "source_support")
        if not sources or any(not isinstance(item, SourceSupport) for item in sources):
            raise ValueError("source_support must contain SourceSupport records")
        _require_unique(sources, "source_support", lambda item: item.source_id)
        _require_sorted(sources, "source_support", lambda item: item.source_id)
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported candidate-result schema_version")

    @property
    def candidate_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": self.schema_version,
                "candidate_id": self.candidate_id,
                "candidate_fingerprint_sha256": self.candidate_fingerprint_sha256,
                "scope": self.scope,
                "version": self.version,
                "source_support": [item.to_dict() for item in self.source_support],
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "candidate_fingerprint_sha256": self.candidate_fingerprint_sha256,
            "scope": self.scope,
            "version": self.version,
            "source_support": [item.to_dict() for item in self.source_support],
            "candidate_digest_sha256": self.candidate_digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateResult":
        expected = {
            "schema_version", "candidate_id", "candidate_fingerprint_sha256", "scope", "version",
            "source_support", "candidate_digest_sha256",
        }
        _require_fields(payload, expected, "candidate-result")
        sources = payload["source_support"]
        if not isinstance(sources, list) or any(not isinstance(item, Mapping) for item in sources):
            raise ValueError("source_support must be an array of objects")
        value = cls(
            candidate_id=payload["candidate_id"],
            candidate_fingerprint_sha256=payload["candidate_fingerprint_sha256"],
            scope=payload["scope"],
            version=payload["version"],
            source_support=tuple(SourceSupport.from_dict(item) for item in sources),
            schema_version=payload["schema_version"],
        )
        if payload["candidate_digest_sha256"] != value.candidate_digest_sha256:
            raise ValueError("candidate-result digest mismatch")
        return value


@dataclass(frozen=True, slots=True)
class SearchHit:
    """A possible matching result found on one independent route."""

    hit_id: str
    result_fingerprint_sha256: str
    scope: str
    version: str
    source_support: tuple[SourceSupport, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.hit_id, "hit_id")
        _require_digest(self.result_fingerprint_sha256, "result_fingerprint_sha256")
        _require_nonempty(self.scope, "scope")
        _require_nonempty(self.version, "version")
        sources = _require_tuple(self.source_support, "source_support")
        if not sources or any(not isinstance(item, SourceSupport) for item in sources):
            raise ValueError("source_support must contain SourceSupport records")
        _require_unique(sources, "source_support", lambda item: item.source_id)
        _require_sorted(sources, "source_support", lambda item: item.source_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hit_id": self.hit_id,
            "result_fingerprint_sha256": self.result_fingerprint_sha256,
            "scope": self.scope,
            "version": self.version,
            "source_support": [item.to_dict() for item in self.source_support],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SearchHit":
        expected = {"hit_id", "result_fingerprint_sha256", "scope", "version", "source_support"}
        _require_fields(payload, expected, "search-hit")
        sources = payload["source_support"]
        if not isinstance(sources, list) or any(not isinstance(item, Mapping) for item in sources):
            raise ValueError("source_support must be an array of objects")
        return cls(
            hit_id=payload["hit_id"],
            result_fingerprint_sha256=payload["result_fingerprint_sha256"],
            scope=payload["scope"],
            version=payload["version"],
            source_support=tuple(SourceSupport.from_dict(item) for item in sources),
        )


@dataclass(frozen=True, slots=True)
class SearchRouteResult:
    """One route's scope, query terms, hits, and explicitly unresolved items."""

    route: SearchRoute
    query_scope: str
    queries: tuple[str, ...]
    hits: tuple[SearchHit, ...]
    unresolved_items: tuple[str, ...]
    searched_at: str
    completed: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.route, SearchRoute):
            raise TypeError("route must be a SearchRoute")
        _require_nonempty(self.query_scope, "query_scope")
        queries = _require_tuple(self.queries, "queries")
        if not queries or any(not isinstance(item, str) or not item.strip() for item in queries):
            raise ValueError("queries must contain non-empty strings")
        _require_unique(queries, "queries", lambda item: item)
        _require_sorted(queries, "queries", lambda item: item)
        hits = _require_tuple(self.hits, "hits")
        if any(not isinstance(item, SearchHit) for item in hits):
            raise TypeError("hits must contain SearchHit records")
        _require_unique(hits, "hits", lambda item: item.hit_id)
        _require_sorted(hits, "hits", lambda item: item.hit_id)
        unresolved = _require_tuple(self.unresolved_items, "unresolved_items")
        if any(not isinstance(item, str) or not item.strip() for item in unresolved):
            raise ValueError("unresolved_items must contain non-empty strings")
        _require_unique(unresolved, "unresolved_items", lambda item: item)
        _require_sorted(unresolved, "unresolved_items", lambda item: item)
        _require_timestamp(self.searched_at, "searched_at")
        if not isinstance(self.completed, bool):
            raise TypeError("completed must be a bool")
        if not self.completed and not unresolved:
            raise ValueError("an incomplete route must record an unresolved item")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported search-route-result schema_version")

    @property
    def route_result_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": self.schema_version,
                "route": self.route.value,
                "query_scope": self.query_scope,
                "queries": list(self.queries),
                "hits": [item.to_dict() for item in self.hits],
                "unresolved_items": list(self.unresolved_items),
                "searched_at": self.searched_at,
                "completed": self.completed,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "route": self.route.value,
            "query_scope": self.query_scope,
            "queries": list(self.queries),
            "hits": [item.to_dict() for item in self.hits],
            "unresolved_items": list(self.unresolved_items),
            "searched_at": self.searched_at,
            "completed": self.completed,
            "route_result_digest_sha256": self.route_result_digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SearchRouteResult":
        expected = {
            "schema_version", "route", "query_scope", "queries", "hits", "unresolved_items", "searched_at",
            "completed", "route_result_digest_sha256",
        }
        _require_fields(payload, expected, "search-route-result")
        queries, hits, unresolved = payload["queries"], payload["hits"], payload["unresolved_items"]
        if not isinstance(queries, list) or not isinstance(hits, list) or not isinstance(unresolved, list):
            raise ValueError("queries, hits, and unresolved_items must be arrays")
        if any(not isinstance(item, Mapping) for item in hits):
            raise ValueError("hits must be an array of objects")
        value = cls(
            route=SearchRoute(payload["route"]),
            query_scope=payload["query_scope"],
            queries=tuple(queries),
            hits=tuple(SearchHit.from_dict(item) for item in hits),
            unresolved_items=tuple(unresolved),
            searched_at=payload["searched_at"],
            completed=payload["completed"],
            schema_version=payload["schema_version"],
        )
        if payload["route_result_digest_sha256"] != value.route_result_digest_sha256:
            raise ValueError("search-route-result digest mismatch")
        return value


@dataclass(frozen=True, slots=True)
class HumanAuditEntry:
    """The required human decision over a recorded four-route audit."""

    reviewer_id: str
    reviewed_at: str
    verdict: HumanAuditVerdict
    conclusion: NoveltyConclusion
    rationale: str

    def __post_init__(self) -> None:
        _require_nonempty(self.reviewer_id, "reviewer_id")
        _require_timestamp(self.reviewed_at, "reviewed_at")
        if not isinstance(self.verdict, HumanAuditVerdict):
            raise TypeError("verdict must be a HumanAuditVerdict")
        if not isinstance(self.conclusion, NoveltyConclusion):
            raise TypeError("conclusion must be a NoveltyConclusion")
        if self.conclusion is NoveltyConclusion.UNASSESSED:
            raise ValueError("a human audit conclusion cannot be UNASSESSED")
        _require_nonempty(self.rationale, "rationale")

    def to_dict(self) -> dict[str, str]:
        return {
            "reviewer_id": self.reviewer_id,
            "reviewed_at": self.reviewed_at,
            "verdict": self.verdict.value,
            "conclusion": self.conclusion.value,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HumanAuditEntry":
        expected = {"reviewer_id", "reviewed_at", "verdict", "conclusion", "rationale"}
        _require_fields(payload, expected, "human-audit-entry")
        return cls(
            reviewer_id=payload["reviewer_id"],
            reviewed_at=payload["reviewed_at"],
            verdict=HumanAuditVerdict(payload["verdict"]),
            conclusion=NoveltyConclusion(payload["conclusion"]),
            rationale=payload["rationale"],
        )


@dataclass(frozen=True, slots=True)
class NoveltyAuditAuthorization:
    """Explicit, narrow permissions derived from a validated audit record."""

    status: NoveltyAuditStatus
    complete_research_budget: bool
    public_qualitative_conclusion: bool
    invalidations: tuple[NoveltyInvalidation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, NoveltyAuditStatus):
            raise TypeError("status must be a NoveltyAuditStatus")
        if not isinstance(self.complete_research_budget, bool) or not isinstance(self.public_qualitative_conclusion, bool):
            raise TypeError("authorization flags must be bool")
        if not isinstance(self.invalidations, tuple) or any(not isinstance(item, NoveltyInvalidation) for item in self.invalidations):
            raise TypeError("invalidations must be a tuple of NoveltyInvalidation")
        if self.status is not NoveltyAuditStatus.AUDITED and (
            self.complete_research_budget or self.public_qualitative_conclusion
        ):
            raise ValueError("only an audited record may grant budget or public conclusions")

    @property
    def allows_complete_budget(self) -> bool:
        return self.complete_research_budget

    @property
    def allows_public_qualitative_conclusion(self) -> bool:
        return self.public_qualitative_conclusion


@dataclass(frozen=True, slots=True)
class NoveltyAuditRecord:
    """An immutable candidate-result audit with separately retained route output."""

    audit_id: str
    candidate: CandidateResult
    route_results: tuple[SearchRouteResult, ...]
    conclusion: NoveltyConclusion = NoveltyConclusion.UNASSESSED
    human_audit: HumanAuditEntry | None = None
    created_at: str = ""
    sealed_at: str = ""
    purpose: NoveltyAuditPurpose = NoveltyAuditPurpose.LIVE_AUDIT
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_nonempty(self.audit_id, "audit_id")
        if not isinstance(self.candidate, CandidateResult):
            raise TypeError("candidate must be a CandidateResult")
        routes = _require_tuple(self.route_results, "route_results")
        if any(not isinstance(item, SearchRouteResult) for item in routes):
            raise TypeError("route_results must contain SearchRouteResult records")
        _require_unique(routes, "route_results", lambda item: item.route)
        _require_sorted(routes, "route_results", lambda item: _ROUTE_ORDER.index(item.route.value))
        if not isinstance(self.conclusion, NoveltyConclusion):
            raise TypeError("conclusion must be a NoveltyConclusion")
        if self.human_audit is not None and not isinstance(self.human_audit, HumanAuditEntry):
            raise TypeError("human_audit must be a HumanAuditEntry or None")
        if self.human_audit is not None and self.human_audit.conclusion is not self.conclusion:
            raise ValueError("human_audit conclusion must match the record conclusion")
        if self.human_audit is not None and self.conclusion is NoveltyConclusion.UNASSESSED:
            raise ValueError("a human audit requires a non-UNASSESSED conclusion")
        _require_timestamp(self.created_at, "created_at")
        _require_timestamp(self.sealed_at, "sealed_at")
        if not isinstance(self.purpose, NoveltyAuditPurpose):
            raise TypeError("purpose must be a NoveltyAuditPurpose")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported novelty-audit-record schema_version")
        _raise_if_invalid_independence(routes)
        _raise_if_invalid_timing(self)

    @property
    def audit_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": self.schema_version,
                "audit_id": self.audit_id,
                "candidate": self.candidate.to_dict(),
                "route_results": [item.to_dict() for item in self.route_results],
                "conclusion": self.conclusion.value,
                "human_audit": self.human_audit.to_dict() if self.human_audit else None,
                "created_at": self.created_at,
                "sealed_at": self.sealed_at,
                "purpose": self.purpose.value,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "candidate": self.candidate.to_dict(),
            "route_results": [item.to_dict() for item in self.route_results],
            "conclusion": self.conclusion.value,
            "human_audit": self.human_audit.to_dict() if self.human_audit else None,
            "created_at": self.created_at,
            "sealed_at": self.sealed_at,
            "purpose": self.purpose.value,
            "audit_digest_sha256": self.audit_digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NoveltyAuditRecord":
        expected = {
            "schema_version", "audit_id", "candidate", "route_results", "conclusion", "human_audit",
            "created_at", "sealed_at", "purpose", "audit_digest_sha256",
        }
        _require_fields(payload, expected, "novelty-audit-record")
        candidate, routes, human = payload["candidate"], payload["route_results"], payload["human_audit"]
        if not isinstance(candidate, Mapping) or not isinstance(routes, list) or any(not isinstance(item, Mapping) for item in routes):
            raise ValueError("candidate must be an object and route_results must be an array of objects")
        if human is not None and not isinstance(human, Mapping):
            raise ValueError("human_audit must be an object or null")
        value = cls(
            audit_id=payload["audit_id"],
            candidate=CandidateResult.from_dict(candidate),
            route_results=tuple(SearchRouteResult.from_dict(item) for item in routes),
            conclusion=NoveltyConclusion(payload["conclusion"]),
            human_audit=HumanAuditEntry.from_dict(human) if human is not None else None,
            created_at=payload["created_at"],
            sealed_at=payload["sealed_at"],
            purpose=NoveltyAuditPurpose(payload["purpose"]),
            schema_version=payload["schema_version"],
        )
        if payload["audit_digest_sha256"] != value.audit_digest_sha256:
            raise ValueError("novelty-audit-record digest mismatch")
        return value

    def authorization(
        self,
        *,
        observations: Mapping[str, SourceObservation] | None = None,
        artifacts: ArtifactStore | None = None,
    ) -> NoveltyAuditAuthorization:
        return authorize(self, observations=observations, artifacts=artifacts)


def authorize(
    record: NoveltyAuditRecord,
    *,
    observations: Mapping[str, SourceObservation] | None = None,
    artifacts: ArtifactStore | None = None,
) -> NoveltyAuditAuthorization:
    """Fail closed unless human-reviewed routes have live source readback."""

    if not isinstance(record, NoveltyAuditRecord):
        return NoveltyAuditAuthorization(
            NoveltyAuditStatus.STALE, False, False, (NoveltyInvalidation.INVALID_INPUT,)
        )
    try:
        observed = {result.route for result in record.route_results}
        invalidations: list[NoveltyInvalidation] = []
        expected = set(SearchRoute)
        if observed != expected:
            invalidations.append(NoveltyInvalidation.MISSING_ROUTE)
        if any(not result.completed for result in record.route_results):
            invalidations.append(NoveltyInvalidation.INCOMPLETE_ROUTE)
        if record.human_audit is None:
            invalidations.append(NoveltyInvalidation.MISSING_HUMAN_AUDIT)
        elif record.human_audit.verdict is not HumanAuditVerdict.APPROVED:
            invalidations.append(NoveltyInvalidation.HUMAN_AUDIT_NOT_APPROVED)
        if record.conclusion is NoveltyConclusion.UNASSESSED:
            invalidations.append(NoveltyInvalidation.UNASSESSED_CONCLUSION)
        if not _routes_are_independent(record.route_results):
            invalidations.append(NoveltyInvalidation.ROUTE_NOT_INDEPENDENT)
        if not _timing_is_valid(record):
            invalidations.append(NoveltyInvalidation.TEMPORAL_ORDER_VIOLATION)
        if invalidations:
            return NoveltyAuditAuthorization(
                NoveltyAuditStatus.STALE if any(
                    item in {
                        NoveltyInvalidation.ROUTE_NOT_INDEPENDENT,
                        NoveltyInvalidation.TEMPORAL_ORDER_VIOLATION,
                    }
                    for item in invalidations
                ) else NoveltyAuditStatus.PENDING_HUMAN_AUDIT,
                False,
                False,
                tuple(invalidations),
            )
        if record.purpose is NoveltyAuditPurpose.CONTRACT_FIXTURE:
            return NoveltyAuditAuthorization(
                NoveltyAuditStatus.CONTRACT_ONLY,
                False,
                False,
                (NoveltyInvalidation.CONTRACT_ONLY_RECORD,),
            )
        if not _source_support_is_verified(record, observations, artifacts):
            return NoveltyAuditAuthorization(
                NoveltyAuditStatus.PENDING_SOURCE_VERIFICATION,
                False,
                False,
                (NoveltyInvalidation.SOURCE_SUPPORT_NOT_VERIFIED,),
            )
        return NoveltyAuditAuthorization(NoveltyAuditStatus.AUDITED, True, True)
    except (AttributeError, TypeError, ValueError):
        return NoveltyAuditAuthorization(
            NoveltyAuditStatus.STALE, False, False, (NoveltyInvalidation.INVALID_INPUT,)
        )


def _routes_are_independent(routes: tuple[SearchRouteResult, ...]) -> bool:
    """Require route-specific queries/scopes and non-overlapping route sources."""

    try:
        scopes = tuple(_normalized_search_text(item.query_scope) for item in routes)
        if len(scopes) != len(set(scopes)):
            return False
        queries: set[str] = set()
        sources: set[tuple[str, str, str]] = set()
        for route in routes:
            route_queries = {_normalized_search_text(item) for item in route.queries}
            if queries & route_queries:
                return False
            queries.update(route_queries)
            route_sources = {
                _stable_source_identity(support)
                for hit in route.hits
                for support in hit.source_support
            }
            if sources & route_sources:
                return False
            sources.update(route_sources)
        return True
    except (AttributeError, TypeError, ValueError):
        return False


def _raise_if_invalid_independence(routes: tuple[SearchRouteResult, ...]) -> None:
    if not _routes_are_independent(routes):
        raise ValueError("route_results must retain independent route-specific scope, queries, and sources")


def _timing_is_valid(record: NoveltyAuditRecord) -> bool:
    try:
        created_at = _parse_timestamp(record.created_at, "created_at")
        sealed_at = _parse_timestamp(record.sealed_at, "sealed_at")
        searched_at = tuple(_parse_timestamp(item.searched_at, "searched_at") for item in record.route_results)
        if created_at > sealed_at or any(created_at > value or value > sealed_at for value in searched_at):
            return False
        if record.human_audit is not None:
            reviewed_at = _parse_timestamp(record.human_audit.reviewed_at, "reviewed_at")
            if any(value > reviewed_at for value in searched_at) or reviewed_at > sealed_at:
                return False
        return True
    except (AttributeError, TypeError, ValueError, OverflowError):
        return False


def _raise_if_invalid_timing(record: NoveltyAuditRecord) -> None:
    if not _timing_is_valid(record):
        raise ValueError("created_at, searched_at, reviewed_at, and sealed_at must be chronologically ordered")


def _source_support_bindings(record: NoveltyAuditRecord) -> tuple[tuple[SourceSupport, datetime], ...]:
    """Bind candidate support conservatively and hit support to its own route."""

    route_times = tuple(
        (route, _parse_timestamp(route.searched_at, "searched_at"))
        for route in record.route_results
    )
    if not route_times:
        raise ValueError("source verification requires at least one route search")
    earliest_search = min(searched_at for _, searched_at in route_times)
    bindings: list[tuple[SourceSupport, datetime]] = [
        (support, earliest_search) for support in record.candidate.source_support
    ]
    for route, searched_at in route_times:
        bindings.extend(
            (support, searched_at)
            for hit in route.hits
            for support in hit.source_support
        )
    return tuple(bindings)


def _source_support_is_verified(
    record: NoveltyAuditRecord,
    observations: Mapping[str, SourceObservation] | None,
    artifacts: ArtifactStore | None,
) -> bool:
    if not isinstance(observations, Mapping) or not isinstance(artifacts, ArtifactStore):
        return False
    try:
        for support, searched_at in _source_support_bindings(record):
            observation = observations.get(support.source_id)
            if not isinstance(observation, SourceObservation):
                return False
            observed_at = _parse_timestamp(observation.observed_at, "observation.observed_at")
            if (
                observation.canonical_uri != support.canonical_uri
                or observation.pinned_version != support.pinned_version
                or observation.content_digest_sha256 != support.source_fingerprint_sha256
                or observation.status is not ObservationStatus.OBSERVED
                or observation.license_status is not LicenseStatus.OPEN
                or not observation.artifact_id
                or observed_at > searched_at
            ):
                return False
            artifact = artifacts.get(observation.artifact_id)
            path = artifacts.path_for(observation.artifact_id)
            content = path.read_bytes()
            if (
                not path.is_file()
                or artifact.sha256 != support.source_fingerprint_sha256
                or artifact.sha256 != observation.content_digest_sha256
                or artifact.size_bytes != len(content)
                or artifact.media_type != observation.media_type
                or artifact.logical_role != "literature-observation"
                or artifact.producer != "matharc-literature-base"
                or hashlib.sha256(content).hexdigest() != artifact.sha256
            ):
                return False
        return True
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        return False
