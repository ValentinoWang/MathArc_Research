"""Replayable, single-topic literature observation batches.

This module coordinates one bounded topic cursor with :class:`LiteratureBase`.
It deliberately records only source-observation outcomes and manual-review
requests.  It does not infer research status and never imports claim or trace
models.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Mapping
from contextlib import contextmanager

from .budget import BudgetLedger
from .literature_base import ImportDisposition, LiteratureBase
from .schema import canonical_json, digest_json
from .source_observation import ObservationStatus, SourceObservation


_SCHEMA_VERSION = "1.0"


class TopicObservationError(ValueError):
    """Raised when durable topic-observation state is malformed or incompatible."""


class TopicRunStatus(str, Enum):
    APPLIED = "APPLIED"
    REPLAYED = "REPLAYED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    CURSOR_BLOCKED = "CURSOR_BLOCKED"


class TopicItemStatus(str, Enum):
    IMPORTED = "IMPORTED"
    IDEMPOTENT = "IDEMPOTENT"
    DUPLICATE = "DUPLICATE"
    PENDING = "PENDING"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ManualReviewReason(str, Enum):
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    HIGH_RISK_EVENT = "HIGH_RISK_EVENT"
    CURSOR_CONFLICT = "CURSOR_CONFLICT"
    INPUT_ID_CONFLICT = "INPUT_ID_CONFLICT"
    LITERATURE_CONFLICT = "LITERATURE_CONFLICT"
    LITERATURE_IMPORT_FAILURE = "LITERATURE_IMPORT_FAILURE"


def _require_nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TopicObservationError(f"{name} must be non-empty")
    return value


def _require_fields(payload: Mapping[str, Any], expected: set[str], name: str) -> None:
    unknown = set(payload) - expected
    missing = expected - set(payload)
    if unknown:
        raise TopicObservationError(f"unknown {name} fields: {sorted(unknown)}")
    if missing:
        raise TopicObservationError(f"missing {name} fields: {sorted(missing)}")


@dataclass(frozen=True, slots=True)
class TopicObservationInput:
    """One bounded source candidate supplied by a topic synchronization run."""

    input_id: str
    observation: SourceObservation
    content: bytes
    risk_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonempty(self.input_id, "input_id")
        if not isinstance(self.observation, SourceObservation):
            raise TypeError("observation must be a SourceObservation")
        if not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        if not isinstance(self.risk_flags, tuple):
            raise TypeError("risk_flags must be a tuple")
        if any(not isinstance(flag, str) or not flag.strip() for flag in self.risk_flags):
            raise TopicObservationError("risk_flags must contain non-empty strings")
        if tuple(sorted(self.risk_flags)) != self.risk_flags or len(set(self.risk_flags)) != len(self.risk_flags):
            raise TopicObservationError("risk_flags must be sorted and unique")

    @property
    def fingerprint_sha256(self) -> str:
        return digest_json(
            {
                "input_id": self.input_id,
                "observation": self.observation.to_dict(),
                "content_sha256": hashlib.sha256(self.content).hexdigest(),
                "risk_flags": list(self.risk_flags),
            }
        )

    @property
    def is_high_risk(self) -> bool:
        return bool(self.risk_flags)


@dataclass(frozen=True, slots=True)
class TopicObservationBatch:
    """A one-topic, explicitly cursor-bounded batch of source candidates."""

    topic_id: str
    cursor: str
    next_cursor: str
    inputs: tuple[TopicObservationInput, ...]
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_nonempty(self.topic_id, "topic_id")
        _require_nonempty(self.cursor, "cursor")
        _require_nonempty(self.next_cursor, "next_cursor")
        if self.cursor == self.next_cursor:
            raise TopicObservationError("next_cursor must advance beyond cursor")
        if not isinstance(self.inputs, tuple) or not self.inputs:
            raise TopicObservationError("inputs must be a non-empty tuple")
        if any(not isinstance(item, TopicObservationInput) for item in self.inputs):
            raise TypeError("inputs must contain TopicObservationInput records")
        identifiers = tuple(item.input_id for item in self.inputs)
        if len(identifiers) != len(set(identifiers)) or tuple(sorted(identifiers)) != identifiers:
            raise TopicObservationError("input ids must be sorted and unique")
        if self.schema_version != _SCHEMA_VERSION:
            raise TopicObservationError("unsupported topic-observation batch schema_version")

    @property
    def batch_digest_sha256(self) -> str:
        return digest_json(
            {
                "schema_version": self.schema_version,
                "topic_id": self.topic_id,
                "cursor": self.cursor,
                "next_cursor": self.next_cursor,
                "inputs": [item.fingerprint_sha256 for item in self.inputs],
            }
        )


@dataclass(frozen=True, slots=True)
class ManualReviewItem:
    manual_id: str
    topic_id: str
    cursor: str
    input_id: str
    reason: ManualReviewReason
    detail: str

    def __post_init__(self) -> None:
        _require_nonempty(self.manual_id, "manual_id")
        _require_nonempty(self.topic_id, "topic_id")
        _require_nonempty(self.cursor, "cursor")
        _require_nonempty(self.input_id, "input_id")
        if not isinstance(self.reason, ManualReviewReason):
            raise TypeError("reason must be a ManualReviewReason")
        _require_nonempty(self.detail, "detail")

    def to_dict(self) -> dict[str, str]:
        return {
            "manual_id": self.manual_id,
            "topic_id": self.topic_id,
            "cursor": self.cursor,
            "input_id": self.input_id,
            "reason": self.reason.value,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ManualReviewItem":
        expected = {"manual_id", "topic_id", "cursor", "input_id", "reason", "detail"}
        _require_fields(payload, expected, "manual-review")
        return cls(
            manual_id=payload["manual_id"],
            topic_id=payload["topic_id"],
            cursor=payload["cursor"],
            input_id=payload["input_id"],
            reason=ManualReviewReason(payload["reason"]),
            detail=payload["detail"],
        )


@dataclass(frozen=True, slots=True)
class TopicItemResult:
    input_id: str
    status: TopicItemStatus
    observation_id: str
    manual_id: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.input_id, "input_id")
        if not isinstance(self.status, TopicItemStatus):
            raise TypeError("status must be a TopicItemStatus")
        _require_nonempty(self.observation_id, "observation_id")
        if self.manual_id is not None:
            _require_nonempty(self.manual_id, "manual_id")
        if self.status is TopicItemStatus.MANUAL_REVIEW and self.manual_id is None:
            raise TopicObservationError("manual review result requires manual_id")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "input_id": self.input_id,
            "status": self.status.value,
            "observation_id": self.observation_id,
            "manual_id": self.manual_id,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TopicItemResult":
        expected = {"input_id", "status", "observation_id", "manual_id"}
        _require_fields(payload, expected, "topic-item-result")
        return cls(
            input_id=payload["input_id"],
            status=TopicItemStatus(payload["status"]),
            observation_id=payload["observation_id"],
            manual_id=payload["manual_id"],
        )


@dataclass(frozen=True, slots=True)
class TopicBatchResult:
    topic_id: str
    cursor: str
    next_cursor: str
    status: TopicRunStatus
    item_results: tuple[TopicItemResult, ...]
    replayed: bool = False

    def __post_init__(self) -> None:
        _require_nonempty(self.topic_id, "topic_id")
        _require_nonempty(self.cursor, "cursor")
        _require_nonempty(self.next_cursor, "next_cursor")
        if not isinstance(self.status, TopicRunStatus):
            raise TypeError("status must be a TopicRunStatus")
        if not isinstance(self.item_results, tuple) or any(not isinstance(item, TopicItemResult) for item in self.item_results):
            raise TypeError("item_results must be a tuple of TopicItemResult")
        if not isinstance(self.replayed, bool):
            raise TypeError("replayed must be bool")

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "cursor": self.cursor,
            "next_cursor": self.next_cursor,
            "status": self.status.value,
            "item_results": [item.to_dict() for item in self.item_results],
            "replayed": self.replayed,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TopicBatchResult":
        expected = {"topic_id", "cursor", "next_cursor", "status", "item_results", "replayed"}
        _require_fields(payload, expected, "topic-batch-result")
        items = payload["item_results"]
        if not isinstance(items, list) or any(not isinstance(item, Mapping) for item in items):
            raise TopicObservationError("item_results must be an array of objects")
        return cls(
            topic_id=payload["topic_id"],
            cursor=payload["cursor"],
            next_cursor=payload["next_cursor"],
            status=TopicRunStatus(payload["status"]),
            item_results=tuple(TopicItemResult.from_dict(item) for item in items),
            replayed=payload["replayed"],
        )


class TopicObservationRunner:
    """Durably process one topic without granting status or proof authority."""

    def __init__(
        self,
        root: str | Path,
        *,
        topic_id: str,
        initial_cursor: str,
        budget: BudgetLedger | None = None,
    ) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.topic_id = _require_nonempty(topic_id, "topic_id")
        self.initial_cursor = _require_nonempty(initial_cursor, "initial_cursor")
        if budget is not None and not isinstance(budget, BudgetLedger):
            raise TypeError("budget must be a BudgetLedger or None")
        self.budget = budget
        self.state_path = self.root / "topic-observation-state.json"
        self.lock_path = self.root / ".topic-observation.lock"
        self.literature = LiteratureBase(self.root / "literature", budget=budget)

    @property
    def manual_queue(self) -> tuple[ManualReviewItem, ...]:
        state = self._load_state()
        return tuple(ManualReviewItem.from_dict(item) for item in state["manual_queue"])

    @property
    def next_cursor(self) -> str:
        return self._load_state()["next_cursor"]

    def run(self, batch: TopicObservationBatch) -> TopicBatchResult:
        if not isinstance(batch, TopicObservationBatch):
            raise TypeError("batch must be a TopicObservationBatch")
        if batch.topic_id != self.topic_id:
            raise TopicObservationError("batch topic_id does not match runner topic_id")
        with self._writer_lock():
            state = self._load_state()
            self.literature = LiteratureBase(self.root / "literature", budget=self.budget)
            batches = state["batches"]
            previous = batches.get(batch.cursor)
            if previous is not None:
                if previous["batch_digest_sha256"] == batch.batch_digest_sha256:
                    return replace(TopicBatchResult.from_dict(previous["result"]), replayed=True, status=TopicRunStatus.REPLAYED)
                manual = self._add_manual(
                    state,
                    cursor=batch.cursor,
                    input_id="cursor",
                    reason=ManualReviewReason.CURSOR_CONFLICT,
                    detail="A cursor was replayed with different batch content.",
                )
                self._save_state(state)
                return TopicBatchResult(
                    self.topic_id, batch.cursor, state["next_cursor"], TopicRunStatus.CURSOR_BLOCKED,
                    (TopicItemResult("cursor", TopicItemStatus.MANUAL_REVIEW, "cursor", manual.manual_id),),
                )
            if batch.cursor != state["next_cursor"]:
                manual = self._add_manual(
                    state,
                    cursor=batch.cursor,
                    input_id="cursor",
                    reason=ManualReviewReason.CURSOR_CONFLICT,
                    detail=f"Expected cursor {state['next_cursor']!r}, received {batch.cursor!r}.",
                )
                self._save_state(state)
                return TopicBatchResult(
                    self.topic_id, batch.cursor, state["next_cursor"], TopicRunStatus.CURSOR_BLOCKED,
                    (TopicItemResult("cursor", TopicItemStatus.MANUAL_REVIEW, "cursor", manual.manual_id),),
                )

            results: list[TopicItemResult] = []
            for item in batch.inputs:
                results.append(self._process_input(state, batch, item))
            status = TopicRunStatus.MANUAL_REVIEW if any(
                item.status is TopicItemStatus.MANUAL_REVIEW for item in results
            ) else TopicRunStatus.APPLIED
            result = TopicBatchResult(self.topic_id, batch.cursor, batch.next_cursor, status, tuple(results))
            batches[batch.cursor] = {
                "batch_digest_sha256": batch.batch_digest_sha256,
                "result": result.to_dict(),
            }
            state["next_cursor"] = batch.next_cursor
            self._save_state(state)
            return result

    def _process_input(
        self,
        state: dict[str, Any],
        batch: TopicObservationBatch,
        item: TopicObservationInput,
    ) -> TopicItemResult:
        prior = state["processed_input_ids"].get(item.input_id)
        if prior is not None:
            if prior == item.fingerprint_sha256:
                return TopicItemResult(item.input_id, TopicItemStatus.DUPLICATE, item.observation.observation_id)
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.INPUT_ID_CONFLICT,
                detail="An input_id was reused with different source-observation content.",
            )
            return TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, item.observation.observation_id, manual.manual_id)
        if item.is_high_risk:
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.HIGH_RISK_EVENT,
                detail="High-risk flags require human review: " + ", ".join(item.risk_flags),
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            return TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, item.observation.observation_id, manual.manual_id)
        if self.budget is not None and self.budget.exhausted():
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.BUDGET_EXHAUSTED,
                detail="The configured import budget is exhausted before topic observation.",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            return TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, item.observation.observation_id, manual.manual_id)
        if item.observation.idempotency_key in state["seen_observation_keys"]:
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            return TopicItemResult(item.input_id, TopicItemStatus.DUPLICATE, item.observation.observation_id)

        imported = self.literature.import_bytes(item.observation, item.content)
        if imported.disposition in {ImportDisposition.IMPORTED, ImportDisposition.IDEMPOTENT}:
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            state["seen_observation_keys"].append(item.observation.idempotency_key)
            state["seen_observation_keys"].sort()
            status = TopicItemStatus.IMPORTED if imported.disposition is ImportDisposition.IMPORTED else TopicItemStatus.IDEMPOTENT
            return TopicItemResult(item.input_id, status, imported.observation.observation_id)
        if imported.disposition is ImportDisposition.CONFLICT or imported.observation.status is ObservationStatus.CONFLICT:
            manual = self._add_manual(
                state,
                cursor=batch.cursor,
                input_id=item.input_id,
                reason=ManualReviewReason.LITERATURE_CONFLICT,
                detail=f"Literature import conflict: {imported.reason or 'unspecified conflict outcome'}",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            return TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, imported.observation.observation_id, manual.manual_id)
        if imported.disposition is ImportDisposition.REJECTED or imported.reason.startswith("artifact persistence failed:"):
            manual = self._add_manual(
                state,
                cursor=batch.cursor,
                input_id=item.input_id,
                reason=ManualReviewReason.LITERATURE_IMPORT_FAILURE,
                detail=f"Literature import failure: {imported.reason or 'unspecified rejected outcome'}",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            return TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, imported.observation.observation_id, manual.manual_id)
        if self.budget is not None and self.budget.exhausted():
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.BUDGET_EXHAUSTED,
                detail="The literature base stopped import because the configured budget is exhausted.",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            return TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, imported.observation.observation_id, manual.manual_id)
        state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
        return TopicItemResult(item.input_id, TopicItemStatus.PENDING, imported.observation.observation_id)

    def _add_manual(
        self,
        state: dict[str, Any],
        *,
        cursor: str,
        input_id: str,
        reason: ManualReviewReason,
        detail: str,
    ) -> ManualReviewItem:
        identity = f"{self.topic_id}|{cursor}|{input_id}|{reason.value}|{detail}"
        manual = ManualReviewItem(
            manual_id="manual-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24],
            topic_id=self.topic_id,
            cursor=cursor,
            input_id=input_id,
            reason=reason,
            detail=detail,
        )
        existing = {item["manual_id"]: item for item in state["manual_queue"]}
        if manual.manual_id not in existing:
            state["manual_queue"].append(manual.to_dict())
            state["manual_queue"].sort(key=lambda item: item["manual_id"])
        return manual

    @contextmanager
    def _writer_lock(self) -> Iterator[None]:
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _new_state(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "topic_id": self.topic_id,
            "next_cursor": self.initial_cursor,
            "batches": {},
            "processed_input_ids": {},
            "seen_observation_keys": [],
            "manual_queue": [],
        }

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._new_state()
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TopicObservationError("topic observation state is unreadable") from exc
        if not isinstance(payload, dict):
            raise TopicObservationError("topic observation state must be an object")
        expected = {"schema_version", "topic_id", "next_cursor", "batches", "processed_input_ids", "seen_observation_keys", "manual_queue"}
        _require_fields(payload, expected, "topic-observation-state")
        if payload["schema_version"] != _SCHEMA_VERSION or payload["topic_id"] != self.topic_id:
            raise TopicObservationError("topic observation state does not match runner")
        if not isinstance(payload["next_cursor"], str) or not payload["next_cursor"]:
            raise TopicObservationError("topic observation state has invalid next_cursor")
        if not isinstance(payload["batches"], dict) or not isinstance(payload["processed_input_ids"], dict):
            raise TopicObservationError("topic observation state has invalid mappings")
        if not isinstance(payload["seen_observation_keys"], list) or not isinstance(payload["manual_queue"], list):
            raise TopicObservationError("topic observation state has invalid collections")
        if payload["seen_observation_keys"] != sorted(set(payload["seen_observation_keys"])):
            raise TopicObservationError("seen_observation_keys must be sorted and unique")
        for cursor, stored in payload["batches"].items():
            _require_nonempty(cursor, "stored cursor")
            if not isinstance(stored, dict) or set(stored) != {"batch_digest_sha256", "result"}:
                raise TopicObservationError("stored batch is malformed")
            if not isinstance(stored["result"], dict):
                raise TopicObservationError("stored batch result is malformed")
            TopicBatchResult.from_dict(stored["result"])
        for item in payload["manual_queue"]:
            if not isinstance(item, dict):
                raise TopicObservationError("manual queue entry is malformed")
            ManualReviewItem.from_dict(item)
        return payload

    def _save_state(self, state: Mapping[str, Any]) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(canonical_json(state) + "\n", encoding="utf-8")
        os.replace(temporary, self.state_path)
