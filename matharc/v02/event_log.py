from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import canonical_json, digest_json, utc_now


GENESIS_HASH = "0" * 64

# Canonical event vocabulary for workspace transitions.  Keep this ordered so
# documentation and UI projections can bind to one stable source of truth.
EVENT_TYPES: tuple[str, ...] = (
    "WORKSPACE_CREATED",
    "CLAIM_ADDED",
    "ROUTE_ADDED",
    "OBJECT_ADDED",
    "OBJECT_VERIFIED",
    "CLAIM_OBJECTS_LINKED",
    "SOURCE_CLAIM_ADDED",
    "SOURCE_CLAIM_VERIFIED",
    "CLAIM_SOURCES_LINKED",
    "EVIDENCE_ADDED",
    "TOOL_CALL_ADDED",
    "PUBLIC_REASONING_ADDED",
    "FAILURE_RECORDED",
    "CLAIM_PROMOTED",
    "CAMPAIGN_RECORDED",
    "CAMPAIGN_COMPLETED",
    "CLAIM_PROMOTION_REJECTED",
    "CAMPAIGN_ROUND_COMPLETED",
    "REVIEW_GAP_RECORDED",
    "ROUTE_FAILURE_RECORDED",
    "CLAIM_COUNTEREXAMPLE_RECORDED",
)


@dataclass(slots=True)
class ResearchEvent:
    sequence: int
    event_id: str
    event_type: str
    actor: str
    subject_ids: tuple[str, ...]
    payload: dict[str, Any]
    previous_hash: str
    timestamp: str = field(default_factory=utc_now)
    event_hash: str = ""

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "subject_ids": list(self.subject_ids),
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
        }

    def compute_hash(self) -> str:
        return digest_json(self.unsigned_dict())

    def seal(self) -> "ResearchEvent":
        expected = self.compute_hash()
        if self.event_hash and self.event_hash != expected:
            raise ValueError(f"event {self.event_id} already has a conflicting hash")
        self.event_hash = expected
        return self

    def to_dict(self) -> dict[str, Any]:
        value = self.unsigned_dict()
        value["event_hash"] = self.event_hash or self.compute_hash()
        return value

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResearchEvent":
        allowed = {
            "sequence",
            "event_id",
            "event_type",
            "actor",
            "subject_ids",
            "payload",
            "previous_hash",
            "timestamp",
            "event_hash",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown research-event fields: {sorted(unknown)}")
        event = cls(
            sequence=int(payload["sequence"]),
            event_id=str(payload["event_id"]),
            event_type=str(payload["event_type"]),
            actor=str(payload["actor"]),
            subject_ids=tuple(str(item) for item in payload.get("subject_ids", [])),
            payload=dict(payload.get("payload") or {}),
            previous_hash=str(payload["previous_hash"]),
            timestamp=str(payload["timestamp"]),
            event_hash=str(payload.get("event_hash", "")),
        )
        if not event.event_hash:
            raise ValueError(f"event {event.event_id} is not sealed")
        if event.compute_hash() != event.event_hash:
            raise ValueError(f"event {event.event_id} hash mismatch")
        return event


class EventLedger:
    """Append-only, hash-chained ledger of public research state changes.

    The ledger is not a blockchain and makes no distributed-consensus claim.
    Its purpose is narrower: exported research traces can detect deletion,
    reordering, insertion, or mutation of an already sealed event sequence.
    """

    def __init__(self, events: Iterable[ResearchEvent] = ()) -> None:
        self._events: list[ResearchEvent] = []
        for event in events:
            self.append_existing(event)

    @property
    def events(self) -> tuple[ResearchEvent, ...]:
        return tuple(self._events)

    @property
    def head_hash(self) -> str:
        return self._events[-1].event_hash if self._events else GENESIS_HASH

    def append(
        self,
        *,
        event_id: str,
        event_type: str,
        actor: str,
        subject_ids: Iterable[str] = (),
        payload: Mapping[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ResearchEvent:
        if any(item.event_id == event_id for item in self._events):
            raise ValueError(f"duplicate event id: {event_id}")
        event = ResearchEvent(
            sequence=len(self._events),
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            subject_ids=tuple(str(item) for item in subject_ids),
            payload=dict(payload or {}),
            previous_hash=self.head_hash,
            timestamp=timestamp or utc_now(),
        ).seal()
        self._events.append(event)
        return event

    def append_existing(self, event: ResearchEvent) -> None:
        expected_sequence = len(self._events)
        expected_previous = self.head_hash
        if event.sequence != expected_sequence:
            raise ValueError(
                f"event {event.event_id} has sequence {event.sequence}; "
                f"expected {expected_sequence}"
            )
        if event.previous_hash != expected_previous:
            raise ValueError(
                f"event {event.event_id} previous hash mismatch: "
                f"{event.previous_hash} != {expected_previous}"
            )
        if event.compute_hash() != event.event_hash:
            raise ValueError(f"event {event.event_id} hash mismatch")
        if any(item.event_id == event.event_id for item in self._events):
            raise ValueError(f"duplicate event id: {event.event_id}")
        self._events.append(event)

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        previous = GENESIS_HASH
        event_ids: set[str] = set()
        for expected_sequence, event in enumerate(self._events):
            if event.sequence != expected_sequence:
                errors.append(
                    f"event {event.event_id}: sequence {event.sequence} != {expected_sequence}"
                )
            if event.previous_hash != previous:
                errors.append(f"event {event.event_id}: previous hash mismatch")
            expected_hash = event.compute_hash()
            if event.event_hash != expected_hash:
                errors.append(f"event {event.event_id}: event hash mismatch")
            if event.event_id in event_ids:
                errors.append(f"duplicate event id: {event.event_id}")
            event_ids.add(event.event_id)
            previous = event.event_hash
        return {
            "valid": not errors,
            "errors": errors,
            "event_count": len(self._events),
            "head_hash": self.head_hash,
            "ledger_digest_sha256": digest_json(self.to_dict()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "genesis_hash": GENESIS_HASH,
            "head_hash": self.head_hash,
            "events": [item.to_dict() for item in self._events],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EventLedger":
        allowed = {"schema_version", "genesis_hash", "head_hash", "events"}
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown event-ledger fields: {sorted(unknown)}")
        if str(payload.get("schema_version")) != "1.0":
            raise ValueError("unsupported event-ledger schema")
        if str(payload.get("genesis_hash")) != GENESIS_HASH:
            raise ValueError("unexpected genesis hash")
        ledger = cls(ResearchEvent.from_dict(item) for item in payload.get("events", []))
        if str(payload.get("head_hash")) != ledger.head_hash:
            raise ValueError("declared ledger head hash does not match events")
        return ledger

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    @classmethod
    def load(cls, path: str | Path) -> "EventLedger":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("event-ledger root must be an object")
        return cls.from_dict(payload)

    def public_summary(self, limit: int | None = None) -> list[dict[str, Any]]:
        events = self._events[-limit:] if limit is not None else self._events
        return [
            {
                "sequence": item.sequence,
                "event_id": item.event_id,
                "event_type": item.event_type,
                "actor": item.actor,
                "subject_ids": list(item.subject_ids),
                "timestamp": item.timestamp,
                "payload_digest_sha256": digest_json(item.payload),
                "event_hash": item.event_hash,
            }
            for item in events
        ]
