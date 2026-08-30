"""Expert-review schema, provenance and object-level authorization (v0.3-review R0).

This is the first slice of `DEV_PATH_V03_DETAIL_V3.md` R0. It follows the same
convention F0/F0.5 established in `falsification.py`: new record types live in
`ResearchTrace.metadata` rather than migrating the frozen v0.2 dataclass
schema, and the promotion authority consumes them through a single lazy,
opt-in hook (`stale_review_evidence_ids`) exactly like F2's
`promotion_route_blockers`. A trace that never uses review.py is completely
unaffected.

Two authorization layers are deliberately kept separate, matching R0's
design note: `RolePolicy` (in `authorization.py`) answers "can this role
submit a review at all"; `can_review` here answers "can this specific actor
review this specific bundle" (object-level: a route's own proposer, or the
producer of any of the claim's accepted evidence, cannot review it, and
neither can a reviewer whose declared conflict-of-interest set intersects
the bundle's contributors).

Trust boundary this module does *not* provide: `review_signature` is a
content-binding integrity hash (tamper-evidence for the record's own
fields), not a cryptographic identity signature. There is no PKI here;
identity comes only from the versioned `ReviewerRoster`. Real reviewer
authentication is out of scope for R0.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping

from .failure_channels import FailureChannelError, open_review_gaps
from .falsification import (
    FalsificationContractError,
    RouteEvaluationOutcome,
    get_kill_test_spec,
    iter_route_evaluations,
)
from .schema import (
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    RouteStatus,
    _FORBIDDEN_REASONING_KEYS,
    digest_json,
    utc_now,
)

if TYPE_CHECKING:
    from .trace import ResearchTrace


class ReviewContractError(ValueError):
    """Raised when a review schema payload is malformed or fails validation."""


class ReviewAuthorizationError(PermissionError):
    """Raised when an actor is not authorized to review a specific bundle."""


class ObligationVerdictKind(str, Enum):
    OK = "OK"
    GAP = "GAP"
    ERROR = "ERROR"
    CANNOT_JUDGE = "CANNOT_JUDGE"


class ReviewDecision(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    REJECT = "REJECT"


class ReviewLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


def _strict_keys(cls: type[Any], payload: Mapping[str, Any]) -> None:
    allowed = {item.name for item in fields(cls)}
    unknown = set(payload) - allowed
    forbidden = set(payload) & _FORBIDDEN_REASONING_KEYS
    if forbidden:
        raise ReviewContractError(
            "private token-by-token reasoning fields are forbidden on review "
            f"records: {sorted(forbidden)}"
        )
    if unknown:
        raise ReviewContractError(f"unknown fields for {cls.__name__}: {sorted(unknown)}")


def _tuple_of_str(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise ReviewContractError("expected an array of strings, not a string")
    return tuple(str(item) for item in value)


def _require_sha256(value: str, field_name: str) -> str:
    text = str(value)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text.lower()):
        raise ReviewContractError(f"{field_name} must be a SHA-256 hex digest")
    return text


def statement_digest_sha256(statement: str) -> str:
    """Digest bound into a ReviewRecord so a changed claim statement is detectable."""

    return digest_json({"statement": statement})


@dataclass(slots=True, frozen=True)
class ReviewerProfile:
    reviewer_id: str
    name: str
    affiliation: str
    independence_group: str
    conflict_of_interest_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reviewer_id.strip():
            raise ReviewContractError("reviewer_id must be non-empty")
        if not self.independence_group.strip():
            raise ReviewContractError("independence_group must be non-empty")

    def semantic_dict(self) -> dict[str, Any]:
        return {
            "reviewer_id": self.reviewer_id,
            "name": self.name,
            "affiliation": self.affiliation,
            "independence_group": self.independence_group,
            "conflict_of_interest_ids": sorted(self.conflict_of_interest_ids),
        }

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.semantic_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self.semantic_dict(), "conflict_of_interest_ids": list(self.conflict_of_interest_ids)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReviewerProfile":
        _strict_keys(cls, payload)
        return cls(
            reviewer_id=str(payload["reviewer_id"]),
            name=str(payload.get("name", "")),
            affiliation=str(payload.get("affiliation", "")),
            independence_group=str(payload["independence_group"]),
            conflict_of_interest_ids=_tuple_of_str(payload.get("conflict_of_interest_ids")),
        )


@dataclass(slots=True, frozen=True)
class ReviewerRoster:
    roster_version: str
    reviewers: tuple[ReviewerProfile, ...]

    def __post_init__(self) -> None:
        if not self.roster_version.strip():
            raise ReviewContractError("roster_version must be non-empty")
        ids = [item.reviewer_id for item in self.reviewers]
        if len(ids) != len(set(ids)):
            raise ReviewContractError("roster contains duplicate reviewer_id values")

    def get(self, reviewer_id: str) -> ReviewerProfile | None:
        for item in self.reviewers:
            if item.reviewer_id == reviewer_id:
                return item
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "roster_version": self.roster_version,
            "reviewers": [item.to_dict() for item in self.reviewers],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReviewerRoster":
        _strict_keys(cls, payload)
        raw_reviewers = payload.get("reviewers", ())
        if isinstance(raw_reviewers, Mapping):
            raise ReviewContractError("reviewers must be an array")
        return cls(
            roster_version=str(payload["roster_version"]),
            reviewers=tuple(ReviewerProfile.from_dict(item) for item in raw_reviewers),
        )


@dataclass(slots=True, frozen=True)
class ObligationVerdict:
    obligation_id: str
    verdict: ObligationVerdictKind
    note: str = ""

    def __post_init__(self) -> None:
        if not self.obligation_id.strip():
            raise ReviewContractError("obligation_id must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "verdict": self.verdict.value,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObligationVerdict":
        _strict_keys(cls, payload)
        return cls(
            obligation_id=str(payload["obligation_id"]),
            verdict=ObligationVerdictKind(str(payload["verdict"])),
            note=str(payload.get("note", "")),
        )


_REVIEW_SIGNATURE_FIELD = "review_signature"


@dataclass(slots=True, frozen=True)
class ReviewRecord:
    review_id: str
    claim_id: str
    claim_revision: int
    statement_digest: str
    bundle_digest: str
    reviewer_id: str
    reviewer_profile_digest: str
    roster_version: str
    review_policy_version: str
    statement_correspondence: str
    verdicts: tuple[ObligationVerdict, ...]
    overall_decision: ReviewDecision
    conflict_declaration: tuple[str, ...] = ()
    review_signature: str = ""
    lifecycle_status: ReviewLifecycleStatus = ReviewLifecycleStatus.ACTIVE
    revoked_reason: str = ""
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.review_id.strip() or not self.claim_id.strip():
            raise ReviewContractError("review_id and claim_id are required")
        if self.claim_revision < 0:
            raise ReviewContractError("claim_revision cannot be negative")
        _require_sha256(self.statement_digest, "statement_digest")
        _require_sha256(self.bundle_digest, "bundle_digest")
        _require_sha256(self.reviewer_profile_digest, "reviewer_profile_digest")
        if not self.roster_version.strip() or not self.review_policy_version.strip():
            raise ReviewContractError("roster_version and review_policy_version are required")
        if not self.statement_correspondence.strip():
            # This is the exact field IMPROVEMENT_PLAN_V03 identifies as the
            # largest laundering channel in the whole system: a reviewer must
            # explicitly say the formal statement matches the informal claim,
            # not leave the field to default-true-by-omission.
            raise ReviewContractError(
                "statement_correspondence must be an explicit reviewer judgement, "
                "not left empty"
            )
        if not self.verdicts:
            raise ReviewContractError("a review record must carry at least one obligation verdict")
        obligation_ids = [item.obligation_id for item in self.verdicts]
        if len(obligation_ids) != len(set(obligation_ids)):
            raise ReviewContractError("duplicate obligation_id in verdicts")
        if self.overall_decision is ReviewDecision.APPROVE:
            non_ok = [item.obligation_id for item in self.verdicts if item.verdict is not ObligationVerdictKind.OK]
            if non_ok:
                raise ReviewContractError(
                    f"APPROVE requires every obligation verdict to be OK; non-OK: {non_ok}"
                )
        expected_signature = self.expected_signature()
        if self.review_signature and self.review_signature != expected_signature:
            raise ReviewContractError("review_signature does not match the bound record content")

    def _signed_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "claim_id": self.claim_id,
            "claim_revision": self.claim_revision,
            "statement_digest": self.statement_digest,
            "bundle_digest": self.bundle_digest,
            "reviewer_id": self.reviewer_id,
            "reviewer_profile_digest": self.reviewer_profile_digest,
            "roster_version": self.roster_version,
            "review_policy_version": self.review_policy_version,
            "statement_correspondence": self.statement_correspondence,
            "verdicts": [item.to_dict() for item in self.verdicts],
            "overall_decision": self.overall_decision.value,
            "conflict_declaration": sorted(self.conflict_declaration),
        }

    def expected_signature(self) -> str:
        """The content-binding integrity digest this record's fields imply.

        Not a cryptographic reviewer identity signature -- see module
        docstring. A caller who leaves `review_signature` unset gets it
        auto-derived (`with_signature`); a caller who supplies one gets it
        checked for tampering.
        """

        return digest_json(self._signed_dict())

    def with_signature(self) -> "ReviewRecord":
        if self.review_signature:
            return self
        return _replace(self, review_signature=self.expected_signature())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._signed_dict(),
            _REVIEW_SIGNATURE_FIELD: self.review_signature,
            "lifecycle_status": self.lifecycle_status.value,
            "revoked_reason": self.revoked_reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReviewRecord":
        _strict_keys(cls, payload)
        raw_verdicts = payload.get("verdicts", ())
        if isinstance(raw_verdicts, Mapping):
            raise ReviewContractError("verdicts must be an array")
        return cls(
            review_id=str(payload["review_id"]),
            claim_id=str(payload["claim_id"]),
            claim_revision=int(payload.get("claim_revision", 0)),
            statement_digest=str(payload["statement_digest"]),
            bundle_digest=str(payload["bundle_digest"]),
            reviewer_id=str(payload["reviewer_id"]),
            reviewer_profile_digest=str(payload["reviewer_profile_digest"]),
            roster_version=str(payload["roster_version"]),
            review_policy_version=str(payload["review_policy_version"]),
            statement_correspondence=str(payload["statement_correspondence"]),
            verdicts=tuple(ObligationVerdict.from_dict(item) for item in raw_verdicts),
            overall_decision=ReviewDecision(str(payload["overall_decision"])),
            conflict_declaration=_tuple_of_str(payload.get("conflict_declaration")),
            review_signature=str(payload.get(_REVIEW_SIGNATURE_FIELD, "")),
            lifecycle_status=ReviewLifecycleStatus(
                str(payload.get("lifecycle_status", ReviewLifecycleStatus.ACTIVE.value))
            ),
            revoked_reason=str(payload.get("revoked_reason", "")),
            created_at=str(payload.get("created_at") or utc_now()),
        )


def _replace(record: ReviewRecord, **changes: Any) -> ReviewRecord:
    import dataclasses

    return dataclasses.replace(record, **changes)


_ROSTER_KEY = "v03_reviewer_roster"
_REVIEW_RECORDS_KEY = "v03_review_records"
_REVIEW_EVIDENCE_LINK_KEY = "v03_review_evidence_links"


def set_reviewer_roster(trace: "ResearchTrace", roster: ReviewerRoster) -> None:
    """Install a roster under its roster_version. A version is pinned on
    first use, exactly like a KillTestSpec digest: re-installing the same
    roster_version with identical content is a no-op, but re-installing it
    with *different* content is rejected. Without this, an already-accepted
    ReviewRecord's binding (roster_version + reviewer_profile_digest) could
    be silently reinterpreted against swapped-in roster content after the
    fact, with no re-validation ever happening -- `stale_review_evidence_ids`
    only checks lifecycle status and claim revision, not roster drift."""

    store = trace.metadata.setdefault(_ROSTER_KEY, {})
    if not isinstance(store, dict):
        raise ReviewContractError("reviewer roster metadata store is malformed")
    existing = store.get(roster.roster_version)
    new_payload = roster.to_dict()
    if existing is not None and existing != new_payload:
        raise ReviewContractError(
            f"roster_version {roster.roster_version} is already pinned to different "
            "content; use a new roster_version instead of redefining an existing one"
        )
    store[roster.roster_version] = new_payload
    trace.updated_at = utc_now()


def get_reviewer_roster(trace: "ResearchTrace", roster_version: str) -> ReviewerRoster | None:
    store = trace.metadata.get(_ROSTER_KEY, {})
    if not isinstance(store, Mapping):
        return None
    raw = store.get(roster_version)
    if not isinstance(raw, Mapping):
        return None
    return ReviewerRoster.from_dict(raw)


def _bundle_contributor_ids(trace: "ResearchTrace", claim_id: str) -> set[str]:
    claim = trace.claims.get(claim_id)
    if claim is None:
        raise ReviewContractError(f"unknown claim: {claim_id}")
    contributors: set[str] = set()
    if claim.owner:
        contributors.add(claim.owner)
    for route_id in claim.route_ids:
        route = trace.routes.get(route_id)
        if route is not None and route.created_by:
            contributors.add(route.created_by)
    for evidence_id in claim.evidence_ids:
        evidence = trace.evidence.get(evidence_id)
        if evidence is not None and evidence.producer:
            contributors.add(evidence.producer)
    return contributors


def can_review(
    trace: "ResearchTrace",
    reviewer: ReviewerProfile,
    claim_id: str,
) -> tuple[bool, str]:
    """Object-level authorization: can this specific reviewer review this
    specific claim's bundle? This is independent of, and in addition to,
    `RolePolicy` (which only knows whether the *role* "reviewer" may submit
    reviews at all)."""

    contributors = _bundle_contributor_ids(trace, claim_id)
    if reviewer.reviewer_id in contributors:
        return False, f"reviewer {reviewer.reviewer_id} contributed to this bundle"
    overlap = set(reviewer.conflict_of_interest_ids) & contributors
    if overlap:
        return False, f"reviewer conflict-of-interest overlaps bundle contributors: {sorted(overlap)}"
    return True, ""


def submit_review(trace: "ResearchTrace", record: ReviewRecord) -> ReviewRecord:
    """Validate and record a ReviewRecord. Raises ReviewContractError for a
    malformed/stale binding and ReviewAuthorizationError for an
    object-level conflict. Never mutates claim status -- R0 only records the
    review; feeding APPROVE into promotion is a separate, explicit step
    (`review_to_evidence`), and feeding REQUEST_CHANGES/REJECT into the
    three-channel failure semantics is R5's job."""

    claim = trace.claims.get(record.claim_id)
    if claim is None:
        raise ReviewContractError(f"unknown claim: {record.claim_id}")
    if record.claim_revision != claim.revision:
        raise ReviewContractError(
            f"review claim_revision {record.claim_revision} is stale; current={claim.revision}"
        )
    expected_statement_digest = statement_digest_sha256(claim.statement)
    if record.statement_digest != expected_statement_digest:
        raise ReviewContractError("review statement_digest does not match the claim's current statement")

    roster = get_reviewer_roster(trace, record.roster_version)
    if roster is None:
        raise ReviewContractError(f"unknown roster_version: {record.roster_version}")
    reviewer = roster.get(record.reviewer_id)
    if reviewer is None:
        raise ReviewAuthorizationError(
            f"reviewer {record.reviewer_id} is not in roster {record.roster_version}"
        )
    if reviewer.digest_sha256 != record.reviewer_profile_digest:
        raise ReviewContractError("reviewer_profile_digest does not match the roster's profile")

    allowed, reason = can_review(trace, reviewer, record.claim_id)
    if not allowed:
        raise ReviewAuthorizationError(reason)

    if record.review_signature != record.expected_signature():
        raise ReviewContractError("review_signature does not match the bound record content")

    existing = _all_review_records(trace)
    if any(item.review_id == record.review_id for item in existing):
        raise ReviewContractError(f"duplicate review id: {record.review_id}")

    store = trace.metadata.setdefault(_REVIEW_RECORDS_KEY, [])
    if not isinstance(store, list):
        raise ReviewContractError("review record metadata store is malformed")
    store.append(record.to_dict())
    trace.updated_at = utc_now()
    return record


def _all_review_records(trace: "ResearchTrace") -> tuple[ReviewRecord, ...]:
    values = trace.metadata.get(_REVIEW_RECORDS_KEY, [])
    if not isinstance(values, list):
        raise ReviewContractError("review record metadata store is malformed")
    return tuple(ReviewRecord.from_dict(item) for item in values)


def get_review(trace: "ResearchTrace", review_id: str) -> ReviewRecord | None:
    for item in _all_review_records(trace):
        if item.review_id == review_id:
            return item
    return None


def reviews_for_claim(trace: "ResearchTrace", claim_id: str) -> tuple[ReviewRecord, ...]:
    return tuple(item for item in _all_review_records(trace) if item.claim_id == claim_id)


def _replace_stored_review(trace: "ResearchTrace", updated: ReviewRecord) -> None:
    store = trace.metadata.get(_REVIEW_RECORDS_KEY, [])
    if not isinstance(store, list):
        raise ReviewContractError("review record metadata store is malformed")
    for index, raw in enumerate(store):
        if isinstance(raw, Mapping) and raw.get("review_id") == updated.review_id:
            store[index] = updated.to_dict()
            trace.updated_at = utc_now()
            return
    raise ReviewContractError(f"unknown review id: {updated.review_id}")


def revoke_review(trace: "ResearchTrace", review_id: str, reason: str) -> ReviewRecord:
    record = get_review(trace, review_id)
    if record is None:
        raise ReviewContractError(f"unknown review id: {review_id}")
    updated = _replace(
        record,
        lifecycle_status=ReviewLifecycleStatus.REVOKED,
        revoked_reason=reason,
    )
    _replace_stored_review(trace, updated)
    # Eager invalidation: any evidence already derived from this review must
    # stop counting toward promotion immediately, not just at the next
    # promotion attempt.
    for evidence_id in _linked_evidence_ids(trace, review_id):
        evidence = trace.evidence.get(evidence_id)
        if evidence is not None and evidence.status is EvidenceStatus.ACCEPTED:
            evidence.status = EvidenceStatus.STALE
    trace.updated_at = utc_now()
    return updated


def _link_evidence(trace: "ResearchTrace", review_id: str, evidence_id: str) -> None:
    store = trace.metadata.setdefault(_REVIEW_EVIDENCE_LINK_KEY, {})
    if not isinstance(store, dict):
        raise ReviewContractError("review-evidence link metadata store is malformed")
    store[evidence_id] = {"review_id": review_id}


def _linked_evidence_ids(trace: "ResearchTrace", review_id: str) -> tuple[str, ...]:
    store = trace.metadata.get(_REVIEW_EVIDENCE_LINK_KEY, {})
    if not isinstance(store, Mapping):
        return ()
    return tuple(
        evidence_id
        for evidence_id, link in store.items()
        if isinstance(link, Mapping) and link.get("review_id") == review_id
    )


def is_review_derived_evidence(trace: "ResearchTrace", evidence_id: str) -> bool:
    """True iff this evidence was minted by `review_to_evidence`. Used by
    R2's obligation generator to avoid a circular obligation: a review's
    own resulting HUMAN_AUDIT evidence must not itself demand "please
    independently assess this evidence" -- that evidence's legitimacy is
    already governed by the review lifecycle (ACTIVE/REVOKED) and R4's
    statement/independence obligations, not by a second review-of-the-
    review loop nothing could ever close."""

    store = trace.metadata.get(_REVIEW_EVIDENCE_LINK_KEY, {})
    return isinstance(store, Mapping) and evidence_id in store


def review_to_evidence(
    trace: "ResearchTrace",
    review_id: str,
    *,
    evidence_id: str,
    artifact_uri: str,
) -> EvidenceRecord:
    """Convert an APPROVE review into HUMAN_AUDIT evidence for the claim it
    reviewed. This is the only path from a ReviewRecord into the promotion
    pipeline; REQUEST_CHANGES/REJECT never produce evidence (they are R5's
    ReviewGap/RouteFailure/ClaimCounterexample material instead)."""

    record = get_review(trace, review_id)
    if record is None:
        raise ReviewContractError(f"unknown review id: {review_id}")
    if record.lifecycle_status is not ReviewLifecycleStatus.ACTIVE:
        raise ReviewContractError(f"review {review_id} is not ACTIVE ({record.lifecycle_status.value})")
    if record.overall_decision is not ReviewDecision.APPROVE:
        raise ReviewContractError("only an APPROVE review can be converted to evidence")
    claim = trace.claims.get(record.claim_id)
    if claim is None:
        raise ReviewContractError(f"unknown claim: {record.claim_id}")
    if record.claim_revision != claim.revision:
        raise ReviewContractError(
            f"review is bound to claim_revision {record.claim_revision}; "
            f"current claim revision is {claim.revision}"
        )
    evidence = EvidenceRecord(
        evidence_id=evidence_id,
        claim_ids=(record.claim_id,),
        kind=EvidenceKind.HUMAN_AUDIT,
        status=EvidenceStatus.ACCEPTED,
        summary=f"Expert review {record.review_id} by {record.reviewer_id}: all obligations OK",
        artifact_uri=artifact_uri,
        digest_sha256=digest_json(record.to_dict()),
        producer=record.reviewer_id,
        verifier=record.reviewer_id,
        independence_group=f"human-review:{_reviewer_independence_group(trace, record)}",
        replay_command="",
        statement_correspondence=record.statement_correspondence,
        assumptions_checked=(),
        limitations=(
            "HUMAN_AUDIT evidence from a single ReviewRecord; independence "
            "comes from distinct reviewer independence_group values across "
            "separate reviews, not from this evidence entry alone.",
        ),
    )
    _link_evidence(trace, review_id, evidence_id)
    return evidence


def _reviewer_independence_group(trace: "ResearchTrace", record: ReviewRecord) -> str:
    roster = get_reviewer_roster(trace, record.roster_version)
    reviewer = roster.get(record.reviewer_id) if roster is not None else None
    if reviewer is None:
        raise ReviewContractError(f"reviewer {record.reviewer_id} not found in bound roster")
    return reviewer.independence_group


def stale_review_evidence_ids(trace: "ResearchTrace", claim_id: str) -> tuple[str, ...]:
    """Evidence ids, among this claim's accepted evidence, that were derived
    from a ReviewRecord that is no longer ACTIVE or whose claim_revision no
    longer matches the claim's current revision. This is F2's
    `promotion_route_blockers` pattern applied to R0: opt-in (a claim with
    no review-derived evidence is unaffected) and checked lazily at
    promotion time rather than by intercepting every mutation site."""

    claim = trace.claims.get(claim_id)
    if claim is None:
        raise ReviewContractError(f"unknown claim: {claim_id}")
    link_store = trace.metadata.get(_REVIEW_EVIDENCE_LINK_KEY, {})
    if not isinstance(link_store, Mapping):
        return ()
    stale: list[str] = []
    for evidence_id in claim.evidence_ids:
        link = link_store.get(evidence_id)
        if not isinstance(link, Mapping):
            continue
        review_id = link.get("review_id")
        if not isinstance(review_id, str):
            continue
        record = get_review(trace, review_id)
        if record is None or record.lifecycle_status is not ReviewLifecycleStatus.ACTIVE:
            stale.append(evidence_id)
            continue
        if record.claim_revision != claim.revision:
            stale.append(evidence_id)
    return tuple(stale)


# --------------------------------------------------------------------------
# R1: machine nomination pre-screen
# --------------------------------------------------------------------------

_NOMINATIONS_KEY = "v03_review_nominations"

# A route counts as "executed" for nomination purposes only when its most
# recent qualifying RouteEvaluationRecord (F0.5, current claim_revision and
# current kill-test spec digest) settled on one of these two outcomes.
# INCONCLUSIVE (including every property_random "no counterexample found"
# result -- see falsification.py) and ERROR never count: they mean the
# check did not reach a determinate conclusion, not that it passed.
_EXECUTED_OUTCOMES = frozenset({RouteEvaluationOutcome.PASS_BOUNDED, RouteEvaluationOutcome.COUNTEREXAMPLE})


class NominationError(ReviewContractError):
    """Raised when a claim fails the machine nomination pre-screen.

    `reasons` is the machine-readable list DEV_PATH_V03 R1 requires; each
    entry is independently actionable (which route, which gap) rather than
    a single combined sentence.
    """

    def __init__(self, reasons: tuple[str, ...]) -> None:
        self.reasons = reasons
        super().__init__("; ".join(reasons) if reasons else "claim is not nomination-ready")


@dataclass(slots=True, frozen=True)
class NominationRecord:
    nomination_id: str
    claim_id: str
    claim_revision: int
    route_ids: tuple[str, ...]
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nomination_id": self.nomination_id,
            "claim_id": self.claim_id,
            "claim_revision": self.claim_revision,
            "route_ids": list(self.route_ids),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NominationRecord":
        _strict_keys(cls, payload)
        return cls(
            nomination_id=str(payload["nomination_id"]),
            claim_id=str(payload["claim_id"]),
            claim_revision=int(payload.get("claim_revision", 0)),
            route_ids=_tuple_of_str(payload.get("route_ids")),
            created_at=str(payload.get("created_at") or utc_now()),
        )


def _route_is_executed(trace: "ResearchTrace", route_id: str, claim_id: str, claim_revision: int) -> bool:
    spec = get_kill_test_spec(trace, route_id)
    if spec is None:
        # A structured route with no KillTestSpec at all has not been
        # brought into the F0/F0.5 protocol yet -- not executed.
        return False
    qualifying = [
        item
        for item in iter_route_evaluations(trace)
        if item.route_id == route_id
        and item.claim_id == claim_id
        and item.claim_revision == claim_revision
        and item.kill_test_spec_digest == spec.digest_sha256
        and item.outcome in _EXECUTED_OUTCOMES
    ]
    return bool(qualifying)


def nomination_blockers(trace: "ResearchTrace", claim_id: str) -> tuple[str, ...]:
    """Machine-readable reasons a claim is not yet ready to be nominated for
    expert review. Empty means nomination-ready."""

    claim = trace.claims.get(claim_id)
    if claim is None:
        return (f"unknown claim: {claim_id}",)
    reasons: list[str] = []
    if claim.status is not ClaimStatus.CANDIDATE:
        reasons.append(f"claim {claim_id} status is {claim.status.value}, not CANDIDATE")

    active_route_ids = [
        route_id
        for route_id in claim.route_ids
        if (route := trace.routes.get(route_id)) is not None and route.status is RouteStatus.ACTIVE
    ]
    unexecuted = [
        route_id
        for route_id in active_route_ids
        if not _route_is_executed(trace, route_id, claim_id, claim.revision)
    ]
    if unexecuted:
        reasons.append(
            f"claim {claim_id} has active routes without a completed PASS_BOUNDED/"
            f"COUNTEREXAMPLE evaluation at the current revision: {unexecuted}"
        )

    try:
        open_gaps = open_review_gaps(trace, claim_id)
    except FailureChannelError:
        open_gaps = ()
    if open_gaps:
        reasons.append(
            f"claim {claim_id} has {len(open_gaps)} open ReviewGap item(s) from a prior "
            "review that have not been addressed: "
            f"{[item.event_id for item in open_gaps]}"
        )
    return tuple(reasons)


def nominate_for_review(trace: "ResearchTrace", claim_id: str) -> NominationRecord:
    """R1 machine gate. Raises NominationError (with a machine-readable
    `.reasons` list) when the claim is not ready; otherwise records and
    returns a NominationRecord.

    Note on scope: a ROUTE_FAILURE or CLAIM_COUNTEREXAMPLE event already
    takes the route out of ACTIVE (BLOCKED/FALSIFIED) or the claim out of
    CANDIDATE (REFUTED/BLOCKED) the moment it is recorded -- see
    failure_channels.py. Those two channels therefore have no separate
    "pending" state to check here beyond what the CANDIDATE-status and
    active-route checks above already enforce; a route that failed and was
    superseded by a sibling route must remain nominable once the sibling
    clears the bar, which a blanket "any past ROUTE_FAILURE ever blocks
    nomination" rule would incorrectly prevent.
    """

    reasons = nomination_blockers(trace, claim_id)
    if reasons:
        raise NominationError(reasons)
    claim = trace.claims[claim_id]
    nomination_id = f"NOM-{claim_id}-r{claim.revision}-{len(_all_nominations(trace))}"
    record = NominationRecord(
        nomination_id=nomination_id,
        claim_id=claim_id,
        claim_revision=claim.revision,
        route_ids=tuple(
            route_id
            for route_id in claim.route_ids
            if (route := trace.routes.get(route_id)) is not None and route.status is RouteStatus.ACTIVE
        ),
    )
    store = trace.metadata.setdefault(_NOMINATIONS_KEY, [])
    if not isinstance(store, list):
        raise ReviewContractError("nomination metadata store is malformed")
    store.append(record.to_dict())
    trace.updated_at = utc_now()
    return record


def _all_nominations(trace: "ResearchTrace") -> tuple[NominationRecord, ...]:
    values = trace.metadata.get(_NOMINATIONS_KEY, [])
    if not isinstance(values, list):
        raise ReviewContractError("nomination metadata store is malformed")
    return tuple(NominationRecord.from_dict(item) for item in values)


def nominations_for_claim(trace: "ResearchTrace", claim_id: str) -> tuple[NominationRecord, ...]:
    return tuple(item for item in _all_nominations(trace) if item.claim_id == claim_id)


def all_nominations(trace: "ResearchTrace") -> tuple[NominationRecord, ...]:
    """Every nomination ever recorded on this trace, across all claims."""

    return _all_nominations(trace)
