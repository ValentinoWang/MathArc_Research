"""v0.3 failure-channel semantics without laundering route/review failures.

The v0.2 FailureRecord has deliberately strong historical semantics: an exact
record refutes the claim and a non-exact record blocks it. Changing that frozen
dataclass would alter legacy trace serialization and digests, so v0.3
introduces a compatibility event layer in ResearchTrace.metadata.

Three channels are kept disjoint:
- REVIEW_GAP: review feedback; no mathematical status changes.
- ROUTE_FAILURE: one mechanism dies; the claim status is untouched.
- CLAIM_COUNTEREXAMPLE: only independently checked COUNTEREXAMPLE evidence may
  call the legacy exact FailureRecord cascade and refute the claim.

All mutations preflight their metadata append before changing mathematical
state, preventing half-written failure events.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping

from .schema import (
    EvidenceKind,
    EvidenceStatus,
    FailureClass,
    FailureRecord,
    RouteStatus,
    digest_json,
    utc_now,
)

if TYPE_CHECKING:
    from .trace import ResearchTrace


class FailureChannelError(ValueError):
    """Raised when a v0.3 failure event would cross its authority boundary."""


class FailureChannel(str, Enum):
    REVIEW_GAP = "REVIEW_GAP"
    ROUTE_FAILURE = "ROUTE_FAILURE"
    CLAIM_COUNTEREXAMPLE = "CLAIM_COUNTEREXAMPLE"


class FailureResolution(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"


def _strict_keys(cls: type[Any], payload: Mapping[str, Any]) -> None:
    allowed = {item.name for item in fields(cls)}
    unknown = set(payload) - allowed
    if unknown:
        raise FailureChannelError(
            f"unknown fields for {cls.__name__}: {sorted(unknown)}"
        )


@dataclass(slots=True, frozen=True)
class FailureChannelRecord:
    event_id: str
    channel: FailureChannel
    claim_id: str
    claim_revision: int
    description: str
    route_id: str = ""
    route_revision: int = 0
    evidence_ids: tuple[str, ...] = ()
    resolution: FailureResolution = FailureResolution.OPEN
    exact: bool = False
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.claim_id.strip():
            raise FailureChannelError("event_id and claim_id are required")
        if self.claim_revision < 0 or self.route_revision < 0:
            raise FailureChannelError("revisions cannot be negative")
        if not self.description.strip():
            raise FailureChannelError("failure-channel description is required")
        if self.channel in {
            FailureChannel.ROUTE_FAILURE,
            FailureChannel.CLAIM_COUNTEREXAMPLE,
        } and not self.route_id.strip():
            raise FailureChannelError(f"{self.channel.value} requires route_id")
        if self.channel is FailureChannel.CLAIM_COUNTEREXAMPLE and not self.exact:
            raise FailureChannelError("CLAIM_COUNTEREXAMPLE must be exact")

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "channel": self.channel.value,
            "claim_id": self.claim_id,
            "claim_revision": self.claim_revision,
            "description": self.description,
            "route_id": self.route_id,
            "route_revision": self.route_revision,
            "evidence_ids": list(self.evidence_ids),
            "resolution": self.resolution.value,
            "exact": self.exact,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FailureChannelRecord":
        _strict_keys(cls, payload)
        raw_evidence = payload.get("evidence_ids", ())
        if not isinstance(raw_evidence, (list, tuple)):
            raise FailureChannelError("evidence_ids must be a list")
        return cls(
            event_id=str(payload["event_id"]),
            channel=FailureChannel(str(payload["channel"])),
            claim_id=str(payload["claim_id"]),
            claim_revision=int(payload.get("claim_revision", 0)),
            description=str(payload["description"]),
            route_id=str(payload.get("route_id", "")),
            route_revision=int(payload.get("route_revision", 0)),
            evidence_ids=tuple(str(item) for item in raw_evidence),
            resolution=FailureResolution(str(payload.get("resolution", "OPEN"))),
            exact=bool(payload.get("exact", False)),
            created_at=str(payload.get("created_at") or utc_now()),
        )


_FAILURE_CHANNELS_KEY = "v03_failure_channels"


def iter_failure_channel_records(trace: "ResearchTrace") -> tuple[FailureChannelRecord, ...]:
    raw = trace.metadata.get(_FAILURE_CHANNELS_KEY, [])
    if not isinstance(raw, list):
        raise FailureChannelError("failure-channel metadata store is malformed")
    records: list[FailureChannelRecord] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise FailureChannelError("failure-channel entry must be an object")
        records.append(FailureChannelRecord.from_dict(item))
    return tuple(records)


def _validate_revision(trace: "ResearchTrace", record: FailureChannelRecord) -> None:
    claim = trace.claims.get(record.claim_id)
    if claim is None:
        raise FailureChannelError(f"unknown claim: {record.claim_id}")
    if claim.revision != record.claim_revision:
        raise FailureChannelError(
            f"failure event claim revision {record.claim_revision} is stale; "
            f"current={claim.revision}"
        )
    if record.route_id:
        route = trace.routes.get(record.route_id)
        if route is None:
            raise FailureChannelError(f"unknown route: {record.route_id}")
        if record.route_revision != 0:
            raise FailureChannelError(
                "route_revision must remain 0 until ResearchRoute gains a formal revision field"
            )
        if record.claim_id not in route.claim_ids:
            raise FailureChannelError(
                f"route {record.route_id} is not linked to claim {record.claim_id}"
            )


def _preflight_append(
    trace: "ResearchTrace", record: FailureChannelRecord
) -> list[dict[str, Any]]:
    if record.resolution is not FailureResolution.OPEN:
        raise FailureChannelError("new failure-channel records must start OPEN")
    existing = {item.event_id for item in iter_failure_channel_records(trace)}
    if record.event_id in existing:
        raise FailureChannelError(f"duplicate failure-channel event: {record.event_id}")
    store = trace.metadata.setdefault(_FAILURE_CHANNELS_KEY, [])
    if not isinstance(store, list):
        raise FailureChannelError("failure-channel metadata store is malformed")
    if any(item.failure_id == record.event_id for item in trace.failures):
        raise FailureChannelError(
            f"event id {record.event_id} conflicts with an existing legacy FailureRecord"
        )
    return store


def _commit_append(
    trace: "ResearchTrace",
    store: list[dict[str, Any]],
    record: FailureChannelRecord,
) -> None:
    store.append(record.to_dict())
    trace.updated_at = utc_now()


def record_review_gap(trace: "ResearchTrace", record: FailureChannelRecord) -> None:
    if record.channel is not FailureChannel.REVIEW_GAP:
        raise FailureChannelError("record_review_gap accepts REVIEW_GAP only")
    _validate_revision(trace, record)
    store = _preflight_append(trace, record)
    before = trace.claims[record.claim_id].status
    _commit_append(trace, store, record)
    if trace.claims[record.claim_id].status is not before:
        raise FailureChannelError("REVIEW_GAP must not change claim status")


def record_route_failure(trace: "ResearchTrace", record: FailureChannelRecord) -> None:
    if record.channel is not FailureChannel.ROUTE_FAILURE:
        raise FailureChannelError("record_route_failure accepts ROUTE_FAILURE only")
    _validate_revision(trace, record)
    store = _preflight_append(trace, record)
    if record.exact and not record.evidence_ids:
        raise FailureChannelError("exact ROUTE_FAILURE requires evidence")
    for evidence_id in record.evidence_ids:
        evidence = trace.evidence.get(evidence_id)
        if evidence is None or evidence.status is not EvidenceStatus.ACCEPTED:
            raise FailureChannelError(
                f"route failure evidence {evidence_id} is missing or not accepted"
            )
    claim_status = trace.claims[record.claim_id].status
    route = trace.routes[record.route_id]
    route.status = RouteStatus.FALSIFIED if record.exact else RouteStatus.BLOCKED
    route.updated_at = utc_now()
    _commit_append(trace, store, record)
    if trace.claims[record.claim_id].status is not claim_status:
        raise FailureChannelError("ROUTE_FAILURE must not change claim status")


def _independent_counterexample_evidence(trace: "ResearchTrace", evidence_id: str) -> bool:
    evidence = trace.evidence.get(evidence_id)
    return bool(
        evidence is not None
        and evidence.status is EvidenceStatus.ACCEPTED
        and evidence.kind is EvidenceKind.COUNTEREXAMPLE
        and len(evidence.digest_sha256) == 64
        and evidence.artifact_uri.strip()
        and evidence.statement_correspondence.strip()
        and evidence.replay_command.strip()
        and evidence.independence_group.strip()
        and evidence.producer.strip()
        and evidence.verifier.strip()
        and evidence.producer != evidence.verifier
    )


def record_claim_counterexample(
    trace: "ResearchTrace",
    record: FailureChannelRecord,
    *,
    failure_class: FailureClass = FailureClass.FALSE_STATEMENT,
) -> FailureRecord:
    if record.channel is not FailureChannel.CLAIM_COUNTEREXAMPLE:
        raise FailureChannelError(
            "record_claim_counterexample accepts CLAIM_COUNTEREXAMPLE only"
        )
    _validate_revision(trace, record)
    store = _preflight_append(trace, record)
    if not record.evidence_ids:
        raise FailureChannelError(
            "CLAIM_COUNTEREXAMPLE requires independently checked counterexample evidence"
        )
    bad = [
        evidence_id
        for evidence_id in record.evidence_ids
        if not _independent_counterexample_evidence(trace, evidence_id)
    ]
    if bad:
        raise FailureChannelError(
            "counterexample evidence must be ACCEPTED, replayable, independently "
            f"verified COUNTEREXAMPLE evidence; invalid={bad}"
        )
    legacy = FailureRecord(
        failure_id=record.event_id,
        claim_id=record.claim_id,
        route_id=record.route_id,
        failure_class=failure_class,
        trigger="independently verified claim counterexample",
        diagnosis=record.description,
        minimal_witness=record.evidence_ids[0],
        repair="retract or narrow the false claim before opening replacement routes",
        reusable_lesson=(
            "Only an independently checked counterexample may cross from route/review "
            "failure into claim refutation."
        ),
        evidence_ids=record.evidence_ids,
        exact=True,
    )
    result = trace.record_failure(legacy)
    _commit_append(trace, store, record)
    return result


def open_review_gaps(trace: "ResearchTrace", claim_id: str) -> tuple[FailureChannelRecord, ...]:
    claim = trace.claims.get(claim_id)
    if claim is None:
        return ()
    return tuple(
        item
        for item in iter_failure_channel_records(trace)
        if item.channel is FailureChannel.REVIEW_GAP
        and item.claim_id == claim_id
        and item.claim_revision == claim.revision
        and item.resolution is FailureResolution.OPEN
    )
