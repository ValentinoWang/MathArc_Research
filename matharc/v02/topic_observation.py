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
_STATE_SCHEMA_VERSION = "1.3"
_STATE_RECOVERY_CONTRACT = "topic-observation-state-recovery-v2"
_LEGACY_STATE_SCHEMA_VERSIONS = {"1.0", "1.1", "1.2"}


class TopicObservationError(ValueError):
    """Raised when durable topic-observation state is malformed or incompatible."""


class ManualQueueObservationError(TopicObservationError):
    """Raised when persisted manual-review queue state is malformed."""


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


_ITEM_EVIDENCE_BASIS_TO_STATUS = {
    "NEW_IMPORT": TopicItemStatus.IMPORTED,
    "EXISTING_OBSERVED": TopicItemStatus.IDEMPOTENT,
    "PROCESSED_INPUT_REPLAY": TopicItemStatus.DUPLICATE,
    "SEEN_OBSERVATION_KEY": TopicItemStatus.DUPLICATE,
    "PENDING_OBSERVATION": TopicItemStatus.PENDING,
    "MANUAL_QUEUE": TopicItemStatus.MANUAL_REVIEW,
}
_ITEM_EVIDENCE_FIELDS = {
    "basis",
    "input_id",
    "input_observation_id",
    "input_idempotency_key",
    "input_content_digest_sha256",
    "input_content_sha256",
    "input_content_size_bytes",
    "input_risk_flags",
    "observation_id",
    "persisted_observation_id",
    "persisted_observation_status",
    "persisted_content_digest_sha256",
    "persisted_artifact_id",
    "persisted_artifact_sha256",
    "manual_id",
    "manual_reason",
    "import_disposition",
    "prior_cursor",
    "prior_input_id",
}
_INPUT_PROJECTION_FIELDS = {
    "input_id",
    "observation",
    "content_sha256",
    "content_size_bytes",
    "risk_flags",
}


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


def _require_sha256(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TopicObservationError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _require_sha256_or_empty(value: object, name: str) -> str:
    if value == "":
        return ""
    return _require_sha256(value, name)


def _require_optional_sha256(value: object, name: str) -> None:
    if value is not None:
        _require_sha256(value, name)


def _batch_digest_from_fingerprints(
    *,
    topic_id: str,
    cursor: str,
    next_cursor: str,
    input_fingerprints: Mapping[str, str],
) -> str:
    return digest_json(
        {
            "schema_version": _SCHEMA_VERSION,
            "topic_id": topic_id,
            "cursor": cursor,
            "next_cursor": next_cursor,
            "inputs": [input_fingerprints[input_id] for input_id in sorted(input_fingerprints)],
        }
    )


def _input_projection_digest(
    *,
    topic_id: str,
    cursor: str,
    next_cursor: str,
    batch_digest_sha256: str,
    input_projections: Mapping[str, Mapping[str, Any]],
) -> str:
    return digest_json(
        {
            "schema_version": _SCHEMA_VERSION,
            "topic_id": topic_id,
            "cursor": cursor,
            "next_cursor": next_cursor,
            "batch_digest_sha256": batch_digest_sha256,
            "inputs": [
                input_projections[input_id]
                for input_id in sorted(input_projections)
            ],
        }
    )


def _canonical_input_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TopicObservationError("stored input projection is malformed")
    _require_fields(value, _INPUT_PROJECTION_FIELDS, "input projection")
    input_id = _require_nonempty(value["input_id"], "stored input projection input_id")
    observation_payload = value["observation"]
    if not isinstance(observation_payload, dict):
        raise TopicObservationError("stored input projection observation is malformed")
    try:
        observation = SourceObservation.from_dict(observation_payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise TopicObservationError("stored input projection observation is invalid") from exc
    content_sha256 = _require_sha256(
        value["content_sha256"],
        "stored input projection content digest",
    )
    content_size_bytes = value["content_size_bytes"]
    if (
        isinstance(content_size_bytes, bool)
        or not isinstance(content_size_bytes, int)
        or content_size_bytes < 0
    ):
        raise TopicObservationError("stored input projection content size is invalid")
    risk_flags = value["risk_flags"]
    if not isinstance(risk_flags, list):
        raise TopicObservationError("stored input projection risk flags are invalid")
    if any(not isinstance(flag, str) or not flag.strip() for flag in risk_flags):
        raise TopicObservationError("stored input projection risk flags are invalid")
    if risk_flags != sorted(set(risk_flags)):
        raise TopicObservationError("stored input projection risk flags must be sorted and unique")
    canonical = {
        "input_id": input_id,
        "observation": observation.to_dict(),
        "content_sha256": content_sha256,
        "content_size_bytes": content_size_bytes,
        "risk_flags": risk_flags,
    }
    if value != canonical:
        raise TopicObservationError("stored input projection is not canonical")
    return canonical


def _fingerprint_from_input_projection(
    projection: Mapping[str, Any],
) -> str:
    return digest_json(
        {
            "input_id": projection["input_id"],
            "observation": projection["observation"],
            "content_sha256": projection["content_sha256"],
            "risk_flags": projection["risk_flags"],
        }
    )


def _manual_id_for(
    *,
    topic_id: str,
    cursor: str,
    input_id: str,
    reason: ManualReviewReason,
    detail: str,
) -> str:
    identity = f"{topic_id}|{cursor}|{input_id}|{reason.value}|{detail}"
    return "manual-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


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
        return _fingerprint_from_input_projection(self.input_projection)

    @property
    def input_projection(self) -> dict[str, Any]:
        """Return the canonical, non-secret identity needed to replay this input."""

        return {
            "input_id": self.input_id,
            "observation": self.observation.to_dict(),
            "content_sha256": hashlib.sha256(self.content).hexdigest(),
            "content_size_bytes": len(self.content),
            "risk_flags": list(self.risk_flags),
        }

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
        return _batch_digest_from_fingerprints(
            topic_id=self.topic_id,
            cursor=self.cursor,
            next_cursor=self.next_cursor,
            input_fingerprints={
                item.input_id: item.fingerprint_sha256 for item in self.inputs
            },
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
        if self.status is not TopicItemStatus.MANUAL_REVIEW and self.manual_id is not None:
            raise TopicObservationError("non-manual result must not carry manual_id")

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
        return _require_nonempty(self._load_state()["next_cursor"], "next_cursor")

    def run(self, batch: TopicObservationBatch) -> TopicBatchResult:
        if not isinstance(batch, TopicObservationBatch):
            raise TypeError("batch must be a TopicObservationBatch")
        if batch.topic_id != self.topic_id:
            raise TopicObservationError("batch topic_id does not match runner topic_id")
        with self._writer_lock():
            self.literature = LiteratureBase(self.root / "literature", budget=self.budget)
            state = self._load_state()
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
                self._record_manual_event(state, manual)
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
                self._record_manual_event(state, manual)
                self._save_state(state)
                return TopicBatchResult(
                    self.topic_id, batch.cursor, state["next_cursor"], TopicRunStatus.CURSOR_BLOCKED,
                    (TopicItemResult("cursor", TopicItemStatus.MANUAL_REVIEW, "cursor", manual.manual_id),),
                )

            results: list[TopicItemResult] = []
            disposition_evidence: dict[str, dict[str, Any]] = {}
            for item in batch.inputs:
                item_result, evidence = self._process_input(state, batch, item)
                results.append(item_result)
                disposition_evidence[item.input_id] = evidence
            status = TopicRunStatus.MANUAL_REVIEW if any(
                item.status is TopicItemStatus.MANUAL_REVIEW for item in results
            ) else TopicRunStatus.APPLIED
            batch_result = TopicBatchResult(
                self.topic_id, batch.cursor, batch.next_cursor, status, tuple(results)
            )
            input_projections = {
                item.input_id: item.input_projection for item in batch.inputs
            }
            batch_digest_sha256 = batch.batch_digest_sha256
            batches[batch.cursor] = {
                "batch_digest_sha256": batch_digest_sha256,
                "result_digest_sha256": digest_json(batch_result.to_dict()),
                "input_fingerprints": {
                    item.input_id: item.fingerprint_sha256 for item in batch.inputs
                },
                "input_projection_digest_sha256": _input_projection_digest(
                    topic_id=batch.topic_id,
                    cursor=batch.cursor,
                    next_cursor=batch.next_cursor,
                    batch_digest_sha256=batch_digest_sha256,
                    input_projections=input_projections,
                ),
                "input_projections": input_projections,
                "input_observation_ids": {
                    item.input_id: item.observation_id for item in results
                },
                "disposition_evidence": disposition_evidence,
                "result": batch_result.to_dict(),
            }
            state["next_cursor"] = batch.next_cursor
            self._save_state(state)
            return batch_result

    def _process_input(
        self,
        state: dict[str, Any],
        batch: TopicObservationBatch,
        item: TopicObservationInput,
    ) -> tuple[TopicItemResult, dict[str, Any]]:
        prior = state["processed_input_ids"].get(item.input_id)
        if prior is not None:
            if prior == item.fingerprint_sha256:
                result = TopicItemResult(item.input_id, TopicItemStatus.DUPLICATE, item.observation.observation_id)
                return result, self._item_evidence(
                    item,
                    result,
                    "PROCESSED_INPUT_REPLAY",
                    persisted=self._persisted_observation_for_input(item),
                    prior_cursor=self._prior_input_cursor(state, item.input_id, item.fingerprint_sha256),
                    prior_input_id=item.input_id,
                )
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.INPUT_ID_CONFLICT,
                detail="An input_id was reused with different source-observation content.",
            )
            result = TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, item.observation.observation_id, manual.manual_id)
            return result, self._item_evidence(
                item,
                result,
                "MANUAL_QUEUE",
                persisted=self._persisted_observation_for_input(item),
                manual_id=manual.manual_id,
                manual_reason=ManualReviewReason.INPUT_ID_CONFLICT,
            )
        if item.is_high_risk:
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.HIGH_RISK_EVENT,
                detail="High-risk flags require human review: " + ", ".join(item.risk_flags),
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            result = TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, item.observation.observation_id, manual.manual_id)
            return result, self._item_evidence(
                item,
                result,
                "MANUAL_QUEUE",
                persisted=self._persisted_observation_for_input(item),
                manual_id=manual.manual_id,
                manual_reason=ManualReviewReason.HIGH_RISK_EVENT,
            )
        if self.budget is not None and self.budget.exhausted():
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.BUDGET_EXHAUSTED,
                detail="The configured import budget is exhausted before topic observation.",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            result = TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, item.observation.observation_id, manual.manual_id)
            return result, self._item_evidence(
                item,
                result,
                "MANUAL_QUEUE",
                persisted=self._persisted_observation_for_input(item),
                manual_id=manual.manual_id,
                manual_reason=ManualReviewReason.BUDGET_EXHAUSTED,
            )
        if item.observation.idempotency_key in state["seen_observation_keys"]:
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            result = TopicItemResult(item.input_id, TopicItemStatus.DUPLICATE, item.observation.observation_id)
            return result, self._item_evidence(
                item,
                result,
                "SEEN_OBSERVATION_KEY",
                persisted=self._persisted_observation_for_input(item),
            )

        imported = self.literature.import_bytes(item.observation, item.content)
        if imported.disposition in {ImportDisposition.IMPORTED, ImportDisposition.IDEMPOTENT}:
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            state["seen_observation_keys"].append(item.observation.idempotency_key)
            state["seen_observation_keys"].sort()
            status = TopicItemStatus.IMPORTED if imported.disposition is ImportDisposition.IMPORTED else TopicItemStatus.IDEMPOTENT
            result = TopicItemResult(item.input_id, status, imported.observation.observation_id)
            return result, self._item_evidence(
                item,
                result,
                "NEW_IMPORT" if status is TopicItemStatus.IMPORTED else "EXISTING_OBSERVED",
                persisted=imported.observation,
                import_disposition=imported.disposition,
            )
        if imported.disposition is ImportDisposition.CONFLICT or imported.observation.status is ObservationStatus.CONFLICT:
            manual = self._add_manual(
                state,
                cursor=batch.cursor,
                input_id=item.input_id,
                reason=ManualReviewReason.LITERATURE_CONFLICT,
                detail=f"Literature import conflict: {imported.reason or 'unspecified conflict outcome'}",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            result = TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, imported.observation.observation_id, manual.manual_id)
            return result, self._item_evidence(
                item,
                result,
                "MANUAL_QUEUE",
                persisted=imported.observation,
                manual_id=manual.manual_id,
                manual_reason=ManualReviewReason.LITERATURE_CONFLICT,
                import_disposition=imported.disposition,
            )
        if imported.disposition is ImportDisposition.REJECTED or imported.reason.startswith("artifact persistence failed:"):
            manual = self._add_manual(
                state,
                cursor=batch.cursor,
                input_id=item.input_id,
                reason=ManualReviewReason.LITERATURE_IMPORT_FAILURE,
                detail=f"Literature import failure: {imported.reason or 'unspecified rejected outcome'}",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            result = TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, imported.observation.observation_id, manual.manual_id)
            return result, self._item_evidence(
                item,
                result,
                "MANUAL_QUEUE",
                persisted=self._persisted_observation_for_input(item),
                manual_id=manual.manual_id,
                manual_reason=ManualReviewReason.LITERATURE_IMPORT_FAILURE,
                import_disposition=imported.disposition,
            )
        if self.budget is not None and self.budget.exhausted():
            manual = self._add_manual(
                state, cursor=batch.cursor, input_id=item.input_id,
                reason=ManualReviewReason.BUDGET_EXHAUSTED,
                detail="The literature base stopped import because the configured budget is exhausted.",
            )
            state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
            result = TopicItemResult(item.input_id, TopicItemStatus.MANUAL_REVIEW, imported.observation.observation_id, manual.manual_id)
            return result, self._item_evidence(
                item,
                result,
                "MANUAL_QUEUE",
                persisted=imported.observation,
                manual_id=manual.manual_id,
                manual_reason=ManualReviewReason.BUDGET_EXHAUSTED,
                import_disposition=imported.disposition,
            )
        state["processed_input_ids"][item.input_id] = item.fingerprint_sha256
        result = TopicItemResult(item.input_id, TopicItemStatus.PENDING, imported.observation.observation_id)
        return result, self._item_evidence(
            item,
            result,
            "PENDING_OBSERVATION",
            persisted=imported.observation,
            import_disposition=imported.disposition,
        )

    def _item_evidence(
        self,
        item: TopicObservationInput,
        result: TopicItemResult,
        basis: str,
        *,
        persisted: SourceObservation | None = None,
        manual_id: str | None = None,
        manual_reason: ManualReviewReason | None = None,
        import_disposition: ImportDisposition | None = None,
        prior_cursor: str | None = None,
        prior_input_id: str | None = None,
    ) -> dict[str, Any]:
        persisted_status = "ABSENT"
        persisted_observation_id = None
        persisted_content_digest = None
        persisted_artifact_id = None
        persisted_artifact_sha256 = None
        if persisted is not None:
            persisted_status = persisted.status.value
            persisted_observation_id = persisted.observation_id
            persisted_content_digest = persisted.content_digest_sha256
            if persisted.status is ObservationStatus.OBSERVED:
                if persisted.artifact_id is None:
                    raise TopicObservationError("observed literature evidence has no artifact")
                try:
                    artifact = self.literature.artifacts.get(persisted.artifact_id)
                except KeyError as exc:
                    raise TopicObservationError("observed literature evidence has no persisted artifact") from exc
                persisted_artifact_id = artifact.artifact_id
                persisted_artifact_sha256 = artifact.sha256
        return {
            "basis": basis,
            "input_id": item.input_id,
            "input_observation_id": item.observation.observation_id,
            "input_idempotency_key": item.observation.idempotency_key,
            "input_content_digest_sha256": item.observation.content_digest_sha256,
            "input_content_sha256": hashlib.sha256(item.content).hexdigest(),
            "input_content_size_bytes": len(item.content),
            "input_risk_flags": list(item.risk_flags),
            "observation_id": result.observation_id,
            "persisted_observation_id": persisted_observation_id,
            "persisted_observation_status": persisted_status,
            "persisted_content_digest_sha256": persisted_content_digest,
            "persisted_artifact_id": persisted_artifact_id,
            "persisted_artifact_sha256": persisted_artifact_sha256,
            "manual_id": manual_id,
            "manual_reason": manual_reason.value if manual_reason is not None else None,
            "prior_cursor": prior_cursor,
            "prior_input_id": prior_input_id,
            "import_disposition": import_disposition.value if import_disposition is not None else None,
        }

    def _persisted_observation_for_input(
        self,
        item: TopicObservationInput,
    ) -> SourceObservation | None:
        candidates = [
            observation
            for observation in self.literature.observations
            if observation.observation_id == item.observation.observation_id
            or observation.idempotency_key == item.observation.idempotency_key
        ]
        if not candidates:
            return None
        status_order = {
            ObservationStatus.OBSERVED: 0,
            ObservationStatus.PENDING: 1,
            ObservationStatus.CONFLICT: 2,
            ObservationStatus.REJECTED: 3,
        }
        return min(
            candidates,
            key=lambda observation: (
                status_order[observation.status],
                observation.observation_id,
            ),
        )

    @staticmethod
    def _prior_input_cursor(
        state: Mapping[str, Any],
        input_id: str,
        fingerprint: str,
    ) -> str | None:
        matches = [
            cursor
            for cursor, stored in state["batches"].items()
            if isinstance(stored, dict)
            and stored.get("input_fingerprints", {}).get(input_id) == fingerprint
        ]
        return sorted(matches)[0] if matches else None

    @staticmethod
    def _record_manual_event(
        state: dict[str, Any],
        manual: ManualReviewItem,
    ) -> None:
        existing = {item["manual_id"] for item in state["manual_events"]}
        if manual.manual_id not in existing:
            state["manual_events"].append(
                {
                    "event_type": "CURSOR_CONFLICT",
                    "manual_id": manual.manual_id,
                }
            )
            state["manual_events"].sort(key=lambda item: item["manual_id"])

    def _add_manual(
        self,
        state: dict[str, Any],
        *,
        cursor: str,
        input_id: str,
        reason: ManualReviewReason,
        detail: str,
    ) -> ManualReviewItem:
        manual = ManualReviewItem(
            manual_id=_manual_id_for(
                topic_id=self.topic_id,
                cursor=cursor,
                input_id=input_id,
                reason=reason,
                detail=detail,
            ),
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
            "schema_version": _STATE_SCHEMA_VERSION,
            "recovery_contract": _STATE_RECOVERY_CONTRACT,
            "topic_id": self.topic_id,
            "next_cursor": self.initial_cursor,
            "batches": {},
            "processed_input_ids": {},
            "seen_observation_keys": [],
            "manual_queue": [],
            "manual_events": [],
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
        schema_version = payload.get("schema_version")
        if schema_version in _LEGACY_STATE_SCHEMA_VERSIONS:
            raise TopicObservationError(
                f"topic observation state schema_version {schema_version!r} is legacy; "
                f"recovery contract {_STATE_RECOVERY_CONTRACT!r} requires preserving the "
                "legacy state and replaying its authoritative source batches into a new "
                "state root"
            )
        if schema_version != _STATE_SCHEMA_VERSION:
            raise TopicObservationError(
                f"unsupported topic observation state schema_version {schema_version!r}; "
                f"recovery contract {_STATE_RECOVERY_CONTRACT!r} requires an explicit "
                "operator migration"
            )
        expected = {
            "schema_version",
            "recovery_contract",
            "topic_id",
            "next_cursor",
            "batches",
            "processed_input_ids",
            "seen_observation_keys",
            "manual_queue",
            "manual_events",
        }
        _require_fields(payload, expected, "topic-observation-state")
        if payload["recovery_contract"] != _STATE_RECOVERY_CONTRACT:
            raise TopicObservationError(
                "topic observation state recovery contract does not match the current "
                "state schema"
            )
        if payload["topic_id"] != self.topic_id:
            raise TopicObservationError("topic observation state does not match runner")
        if not isinstance(payload["next_cursor"], str) or not payload["next_cursor"]:
            raise TopicObservationError("topic observation state has invalid next_cursor")
        if not isinstance(payload["batches"], dict) or not isinstance(payload["processed_input_ids"], dict):
            raise TopicObservationError("topic observation state has invalid mappings")
        if not isinstance(payload["seen_observation_keys"], list):
            raise TopicObservationError("topic observation state has invalid collections")
        for key in payload["seen_observation_keys"]:
            _require_sha256(key, "seen observation key")
        if payload["seen_observation_keys"] != sorted(set(payload["seen_observation_keys"])):
            raise TopicObservationError("seen_observation_keys must be sorted and unique")
        for input_id, fingerprint in payload["processed_input_ids"].items():
            _require_nonempty(input_id, "processed input id")
            _require_sha256(fingerprint, "processed input fingerprint")

        manual_queue = self._load_manual_queue(payload["manual_queue"])
        manual_events = self._load_manual_events(payload["manual_events"])
        literature_by_id = {
            observation.observation_id: observation
            for observation in self.literature.observations
        }

        validated_batches: dict[str, TopicBatchResult] = {}
        batch_input_ids: set[str] = set()
        referenced_manual_ids: set[str] = set()
        derived_seen_observation_keys: set[str] = set()
        for cursor, stored in payload["batches"].items():
            _require_nonempty(cursor, "stored cursor")
            if not isinstance(stored, dict) or set(stored) != {
                "batch_digest_sha256",
                "result_digest_sha256",
                "input_fingerprints",
                "input_projection_digest_sha256",
                "input_projections",
                "input_observation_ids",
                "disposition_evidence",
                "result",
            }:
                raise TopicObservationError("stored batch is malformed")
            _require_sha256(stored["batch_digest_sha256"], "stored batch digest")
            _require_sha256(stored["result_digest_sha256"], "stored batch result digest")
            input_fingerprints = stored["input_fingerprints"]
            if not isinstance(input_fingerprints, dict) or not input_fingerprints:
                raise TopicObservationError("stored batch input fingerprints are malformed")
            for input_id, fingerprint in input_fingerprints.items():
                _require_nonempty(input_id, "stored batch input id")
                _require_sha256(fingerprint, "stored batch input fingerprint")
            input_projections = stored["input_projections"]
            if not isinstance(input_projections, dict) or set(input_projections) != set(input_fingerprints):
                raise TopicObservationError("stored batch input projections are malformed")
            canonical_projections: dict[str, dict[str, Any]] = {}
            for input_id, projection in input_projections.items():
                _require_nonempty(input_id, "stored batch projection input id")
                canonical_projection = _canonical_input_projection(projection)
                if canonical_projection["input_id"] != input_id:
                    raise TopicObservationError("stored batch input projection id conflicts with its mapping")
                if _fingerprint_from_input_projection(canonical_projection) != input_fingerprints[input_id]:
                    raise TopicObservationError("stored batch input projection fingerprint mismatch")
                canonical_projections[input_id] = canonical_projection
            _require_sha256(
                stored["input_projection_digest_sha256"],
                "stored batch input projection digest",
            )
            input_observation_ids = stored["input_observation_ids"]
            if not isinstance(input_observation_ids, dict) or set(input_observation_ids) != set(input_fingerprints):
                raise TopicObservationError("stored batch input observations are malformed")
            for input_id, observation_id in input_observation_ids.items():
                _require_nonempty(input_id, "stored batch observation input id")
                _require_nonempty(observation_id, "stored batch observation id")
            disposition_evidence = stored["disposition_evidence"]
            if not isinstance(disposition_evidence, dict) or set(disposition_evidence) != set(input_fingerprints):
                raise TopicObservationError("stored batch disposition evidence is malformed")
            for input_id, evidence in disposition_evidence.items():
                if not isinstance(evidence, dict):
                    raise TopicObservationError("stored batch disposition evidence is malformed")
                _require_fields(evidence, _ITEM_EVIDENCE_FIELDS, "topic-item evidence")
            if not isinstance(stored["result"], dict):
                raise TopicObservationError("stored batch result is malformed")
            if stored["result_digest_sha256"] != digest_json(stored["result"]):
                raise TopicObservationError("stored batch result digest mismatch")
            result = TopicBatchResult.from_dict(stored["result"])
            if result.replayed:
                raise TopicObservationError("stored batch result cannot be marked replayed")
            if result.topic_id != payload["topic_id"]:
                raise TopicObservationError("stored batch result topic_id conflicts with state")
            if result.cursor != cursor:
                raise TopicObservationError("stored batch result cursor conflicts with state")
            if result.cursor == result.next_cursor:
                raise TopicObservationError("stored batch result must advance its cursor")
            expected_status = (
                TopicRunStatus.MANUAL_REVIEW
                if any(item.status is TopicItemStatus.MANUAL_REVIEW for item in result.item_results)
                else TopicRunStatus.APPLIED
            )
            if result.status is not expected_status:
                raise TopicObservationError("stored batch result status does not match item statuses")
            result_by_input_id = {item.input_id: item for item in result.item_results}
            for item in result.item_results:
                if item.status is TopicItemStatus.MANUAL_REVIEW:
                    matching_manuals = [
                        manual
                        for manual in manual_queue
                        if manual.manual_id == item.manual_id
                        and manual.topic_id == result.topic_id
                        and manual.cursor == result.cursor
                        and manual.input_id == item.input_id
                    ]
                    if len(matching_manuals) != 1:
                        raise ManualQueueObservationError(
                            "stored manual review result does not match exactly one manual queue entry"
                        )
                    referenced_manual_ids.add(matching_manuals[0].manual_id)
            result_input_ids = tuple(item.input_id for item in result.item_results)
            expected_input_ids = tuple(sorted(input_fingerprints))
            if result_input_ids != expected_input_ids:
                raise TopicObservationError("stored batch result items do not match batch inputs")
            if any(
                item.observation_id != input_observation_ids[item.input_id]
                for item in result.item_results
            ):
                raise TopicObservationError("stored batch result observations do not match batch inputs")
            for input_id, fingerprint in input_fingerprints.items():
                persisted_fingerprint = payload["processed_input_ids"].get(input_id)
                if persisted_fingerprint is None:
                    raise TopicObservationError("stored batch input is missing from processed state")
                if persisted_fingerprint != fingerprint:
                    item_result = next(item for item in result.item_results if item.input_id == input_id)
                    if not (
                        item_result.status is TopicItemStatus.MANUAL_REVIEW
                        and any(
                            manual.manual_id == item_result.manual_id
                            and manual.input_id == input_id
                            and manual.reason is ManualReviewReason.INPUT_ID_CONFLICT
                            for manual in manual_queue
                        )
                    ):
                        raise TopicObservationError("stored batch input fingerprint conflicts with processed state")
            for input_id, evidence in disposition_evidence.items():
                self._validate_item_evidence(
                    evidence,
                    result_by_input_id[input_id],
                    input_fingerprints[input_id],
                    input_observation_ids[input_id],
                    canonical_projections[input_id],
                    cursor=cursor,
                    all_stored_batches=payload["batches"],
                    processed_input_ids=payload["processed_input_ids"],
                    manual_queue=manual_queue,
                    literature_by_id=literature_by_id,
                    seen_observation_keys=set(payload["seen_observation_keys"]),
                )
                if evidence["basis"] in {"NEW_IMPORT", "EXISTING_OBSERVED"}:
                    derived_seen_observation_keys.add(evidence["input_idempotency_key"])
            expected_batch_digest = _batch_digest_from_fingerprints(
                topic_id=result.topic_id,
                cursor=result.cursor,
                next_cursor=result.next_cursor,
                input_fingerprints=input_fingerprints,
            )
            if stored["batch_digest_sha256"] != expected_batch_digest:
                raise TopicObservationError("stored batch digest does not match its inputs")
            expected_projection_digest = _input_projection_digest(
                topic_id=result.topic_id,
                cursor=result.cursor,
                next_cursor=result.next_cursor,
                batch_digest_sha256=stored["batch_digest_sha256"],
                input_projections=canonical_projections,
            )
            if stored["input_projection_digest_sha256"] != expected_projection_digest:
                raise TopicObservationError("stored input projection digest does not match its batch")
            validated_batches[cursor] = result
            batch_input_ids.update(input_fingerprints)

        event_ids: set[str] = set()
        for event in manual_events:
            manual_id = event["manual_id"]
            if manual_id in event_ids:
                raise ManualQueueObservationError("manual event manual_ids must be unique")
            event_ids.add(manual_id)
            matching_manuals = [manual for manual in manual_queue if manual.manual_id == manual_id]
            if len(matching_manuals) != 1:
                raise ManualQueueObservationError(
                    "manual event does not match exactly one manual queue entry"
                )
            manual = matching_manuals[0]
            if (
                event["event_type"] != "CURSOR_CONFLICT"
                or manual.reason is not ManualReviewReason.CURSOR_CONFLICT
                or manual.input_id != "cursor"
                or manual.topic_id != payload["topic_id"]
            ):
                raise ManualQueueObservationError("manual event does not describe a cursor conflict")
            if manual_id in referenced_manual_ids:
                raise ManualQueueObservationError("manual queue entry is referenced more than once")
            referenced_manual_ids.add(manual_id)

        queue_ids = {manual.manual_id for manual in manual_queue}
        if referenced_manual_ids != queue_ids:
            raise ManualQueueObservationError("manual queue contains an orphaned entry")
        if derived_seen_observation_keys != set(payload["seen_observation_keys"]):
            raise TopicObservationError("seen observation keys do not match persisted item evidence")
        if batch_input_ids != set(payload["processed_input_ids"]):
            raise TopicObservationError("stored batch inputs do not match processed state")
        cursor = self.initial_cursor
        visited: set[str] = set()
        while cursor in validated_batches:
            if cursor in visited:
                raise TopicObservationError("stored batch cursor chain contains a cycle")
            visited.add(cursor)
            cursor = validated_batches[cursor].next_cursor
        if cursor != payload["next_cursor"] or visited != set(validated_batches):
            raise TopicObservationError("stored batch cursor chain conflicts with state")
        return payload

    def _validate_item_evidence(
        self,
        evidence: Mapping[str, Any],
        result: TopicItemResult,
        fingerprint: str,
        persisted_result_observation_id: str,
        input_projection: Mapping[str, Any],
        *,
        cursor: str,
        all_stored_batches: Mapping[str, Any],
        processed_input_ids: Mapping[str, str],
        manual_queue: list[ManualReviewItem],
        literature_by_id: Mapping[str, SourceObservation],
        seen_observation_keys: set[str],
    ) -> None:
        basis = evidence["basis"]
        _require_nonempty(basis, "stored topic-item evidence basis")
        if basis not in _ITEM_EVIDENCE_BASIS_TO_STATUS:
            raise TopicObservationError("stored topic-item evidence has an unknown basis")
        expected_status = _ITEM_EVIDENCE_BASIS_TO_STATUS[basis]
        if result.status is not expected_status:
            raise TopicObservationError(
                "stored topic-item disposition conflicts with persisted evidence"
            )
        if evidence["input_id"] != result.input_id:
            raise TopicObservationError("stored topic-item evidence input_id conflicts with result")
        if evidence["observation_id"] != result.observation_id:
            raise TopicObservationError("stored topic-item evidence observation_id conflicts with result")
        if persisted_result_observation_id != result.observation_id:
            raise TopicObservationError("stored result observation id conflicts with item evidence")
        projection_observation = SourceObservation.from_dict(input_projection["observation"])
        if evidence["input_observation_id"] != projection_observation.observation_id:
            raise TopicObservationError("stored input observation id conflicts with input projection")
        if evidence["input_idempotency_key"] != projection_observation.idempotency_key:
            raise TopicObservationError("stored input idempotency key conflicts with input projection")
        if evidence["input_content_digest_sha256"] != projection_observation.content_digest_sha256:
            raise TopicObservationError("stored input content digest conflicts with input projection")
        if evidence["input_content_sha256"] != input_projection["content_sha256"]:
            raise TopicObservationError("stored input content digest conflicts with input projection bytes")
        if evidence["input_content_size_bytes"] != input_projection["content_size_bytes"]:
            raise TopicObservationError("stored input content size conflicts with input projection")
        if evidence["input_risk_flags"] != input_projection["risk_flags"]:
            raise TopicObservationError("stored input risk flags conflict with input projection")
        _require_nonempty(evidence["input_observation_id"], "stored input observation id")
        _require_sha256(evidence["input_idempotency_key"], "stored input idempotency key")
        _require_sha256_or_empty(
            evidence["input_content_digest_sha256"],
            "stored input content digest",
        )
        _require_sha256(evidence["input_content_sha256"], "stored input bytes digest")
        if (
            isinstance(evidence["input_content_size_bytes"], bool)
            or not isinstance(evidence["input_content_size_bytes"], int)
            or evidence["input_content_size_bytes"] < 0
        ):
            raise TopicObservationError("stored input content size is invalid")
        if not isinstance(evidence["input_risk_flags"], list):
            raise TopicObservationError("stored input risk flags are invalid")
        _require_nonempty(evidence["observation_id"], "stored result observation id")
        if evidence["persisted_content_digest_sha256"] is not None:
            _require_sha256_or_empty(
                evidence["persisted_content_digest_sha256"],
                "stored persisted content digest",
            )
        _require_optional_sha256(
            evidence["persisted_artifact_sha256"],
            "stored persisted artifact digest",
        )
        persisted_status = evidence["persisted_observation_status"]
        _require_nonempty(persisted_status, "stored persisted observation status")
        valid_persisted_statuses = {"ABSENT"} | {status.value for status in ObservationStatus}
        if persisted_status not in valid_persisted_statuses:
            raise TopicObservationError("stored persisted observation status is invalid")
        persisted_id = evidence["persisted_observation_id"]
        if persisted_id is not None:
            _require_nonempty(persisted_id, "stored persisted observation id")
            if evidence["persisted_artifact_id"] is not None:
                _require_nonempty(evidence["persisted_artifact_id"], "stored persisted artifact id")
            persisted = literature_by_id.get(persisted_id)
            if persisted is None:
                raise TopicObservationError("stored item evidence references an unknown literature observation")
            if persisted.status.value != persisted_status:
                raise TopicObservationError("stored item evidence observation status conflicts with literature")
            if persisted.content_digest_sha256 != evidence["persisted_content_digest_sha256"]:
                raise TopicObservationError("stored item evidence content digest conflicts with literature")
            if persisted.status is ObservationStatus.OBSERVED:
                if evidence["persisted_artifact_id"] != persisted.artifact_id:
                    raise TopicObservationError("stored item evidence artifact id conflicts with literature")
                if evidence["persisted_artifact_sha256"] is None:
                    raise TopicObservationError("stored observed item evidence has no artifact digest")
                try:
                    artifact = self.literature.artifacts.get(persisted.artifact_id or "")
                except KeyError as exc:
                    raise TopicObservationError("stored item evidence artifact is not persisted") from exc
                if artifact.sha256 != evidence["persisted_artifact_sha256"]:
                    raise TopicObservationError("stored item evidence artifact digest conflicts with artifact store")
                if artifact.sha256 != persisted.content_digest_sha256:
                    raise TopicObservationError("stored literature artifact conflicts with observation")
            elif evidence["persisted_artifact_id"] is not None or evidence["persisted_artifact_sha256"] is not None:
                raise TopicObservationError("non-observed item evidence must not carry an artifact")
        else:
            if persisted_status != "ABSENT":
                raise TopicObservationError("absent item evidence has a persisted observation status")
            if evidence["persisted_content_digest_sha256"] is not None or evidence["persisted_artifact_id"] is not None or evidence["persisted_artifact_sha256"] is not None:
                raise TopicObservationError("absent item evidence carries persisted source fields")
            if evidence["observation_id"] in literature_by_id:
                raise TopicObservationError("absent item evidence hides a persisted observation")

        import_disposition = evidence["import_disposition"]
        if import_disposition is not None:
            try:
                ImportDisposition(import_disposition)
            except (TypeError, ValueError) as exc:
                raise TopicObservationError("stored item evidence import disposition is invalid") from exc
        if basis != "MANUAL_QUEUE" and result.observation_id != projection_observation.observation_id:
            raise TopicObservationError(
                "stored result observation identity conflicts with input projection"
            )
        if basis in {"NEW_IMPORT", "EXISTING_OBSERVED"}:
            if evidence["persisted_observation_id"] is None or persisted_status != ObservationStatus.OBSERVED.value:
                raise TopicObservationError("successful item evidence must reference an observed literature record")
            if evidence["persisted_observation_id"] != evidence["observation_id"]:
                raise TopicObservationError("successful item evidence observation identity conflicts")
            if evidence["input_idempotency_key"] != literature_by_id[evidence["persisted_observation_id"]].idempotency_key:
                raise TopicObservationError("successful item evidence idempotency key conflicts")
            if import_disposition != (
                ImportDisposition.IMPORTED.value
                if basis == "NEW_IMPORT"
                else ImportDisposition.IDEMPOTENT.value
            ):
                raise TopicObservationError("successful item evidence import disposition conflicts")
        elif basis == "SEEN_OBSERVATION_KEY":
            if evidence["persisted_observation_id"] is None or persisted_status != ObservationStatus.OBSERVED.value:
                raise TopicObservationError("duplicate item evidence must reference an observed literature record")
            if evidence["input_idempotency_key"] not in seen_observation_keys:
                raise TopicObservationError("duplicate item evidence is not present in seen observation state")
            if literature_by_id[evidence["persisted_observation_id"]].idempotency_key != evidence["input_idempotency_key"]:
                raise TopicObservationError("duplicate item evidence idempotency key conflicts")
            if import_disposition is not None:
                raise TopicObservationError("topic duplicate evidence must not claim an import disposition")
        elif basis == "PENDING_OBSERVATION":
            if persisted_status != ObservationStatus.PENDING.value or evidence["persisted_observation_id"] is None:
                raise TopicObservationError("pending item evidence must reference a pending literature record")
            if import_disposition != ImportDisposition.PENDING.value:
                raise TopicObservationError("pending item evidence import disposition conflicts")
            if literature_by_id[evidence["persisted_observation_id"]].idempotency_key != evidence["input_idempotency_key"]:
                raise TopicObservationError("pending item evidence idempotency key conflicts")
        elif basis == "PROCESSED_INPUT_REPLAY":
            if import_disposition is not None:
                raise TopicObservationError("processed duplicate evidence must not claim an import disposition")
            prior_cursor = evidence["prior_cursor"]
            if prior_cursor is None or prior_cursor == cursor or evidence["prior_input_id"] != result.input_id:
                raise TopicObservationError("processed duplicate evidence has no valid prior input")
            prior_batch = all_stored_batches.get(prior_cursor)
            if not isinstance(prior_batch, dict):
                raise TopicObservationError("processed duplicate evidence references an unknown prior batch")
            if prior_batch.get("input_fingerprints", {}).get(result.input_id) != fingerprint:
                raise TopicObservationError("processed duplicate evidence fingerprint conflicts")
            prior_evidence = prior_batch.get("disposition_evidence", {}).get(result.input_id)
            if not isinstance(prior_evidence, dict):
                raise TopicObservationError("processed duplicate evidence prior record is missing")
            for field in (
                "input_idempotency_key",
                "persisted_observation_id",
                "persisted_observation_status",
                "persisted_content_digest_sha256",
                "persisted_artifact_id",
                "persisted_artifact_sha256",
            ):
                if evidence[field] != prior_evidence.get(field):
                    raise TopicObservationError("processed duplicate evidence does not match prior evidence")
        elif basis == "MANUAL_QUEUE":
            if evidence["manual_id"] is None or evidence["prior_cursor"] is not None or evidence["prior_input_id"] is not None:
                raise TopicObservationError("manual item evidence has invalid linkage fields")
            matching_manuals = [
                manual
                for manual in manual_queue
                if manual.manual_id == evidence["manual_id"]
                and manual.topic_id == self.topic_id
                and manual.cursor == cursor
                and manual.input_id == result.input_id
            ]
            if len(matching_manuals) != 1:
                raise ManualQueueObservationError(
                    "stored manual item evidence does not match exactly one manual queue entry"
                )
            manual = matching_manuals[0]
            if evidence["manual_reason"] != manual.reason.value:
                raise ManualQueueObservationError("stored manual item evidence reason conflicts with queue")
            if manual.reason is ManualReviewReason.HIGH_RISK_EVENT:
                if not input_projection["risk_flags"]:
                    raise TopicObservationError(
                        "high-risk manual disposition conflicts with input projection"
                    )
                if result.observation_id != projection_observation.observation_id:
                    raise TopicObservationError(
                        "high-risk manual result observation conflicts with input projection"
                    )
            elif manual.reason is ManualReviewReason.LITERATURE_CONFLICT:
                if persisted_id is None or persisted_status != ObservationStatus.CONFLICT.value:
                    raise TopicObservationError(
                        "literature conflict manual disposition lacks conflict evidence"
                    )
                conflict_digest = hashlib.sha256(
                    f"{projection_observation.logical_identity}|{projection_observation.content_digest_sha256}".encode(
                        "utf-8"
                    )
                ).hexdigest()
                expected_conflict_id = (
                    f"{projection_observation.observation_id}-conflict-{conflict_digest}"
                )
                if result.observation_id != expected_conflict_id:
                    raise TopicObservationError(
                        "literature conflict result observation conflicts with input projection"
                    )
                if result.observation_id != persisted_id:
                    raise TopicObservationError(
                        "literature conflict result does not match persisted conflict evidence"
                    )
            elif manual.reason is ManualReviewReason.INPUT_ID_CONFLICT:
                prior_fingerprint = processed_input_ids.get(result.input_id)
                if prior_fingerprint is None or prior_fingerprint == fingerprint:
                    raise TopicObservationError(
                        "input-id conflict manual disposition lacks a prior fingerprint conflict"
                    )
                if result.observation_id != projection_observation.observation_id:
                    raise TopicObservationError(
                        "input-id conflict result observation conflicts with input projection"
                    )
            elif manual.reason is ManualReviewReason.BUDGET_EXHAUSTED:
                if persisted_id is not None and import_disposition != ImportDisposition.PENDING.value:
                    raise TopicObservationError(
                        "budget manual disposition lacks budget-blocked import evidence"
                    )
                if persisted_id is not None and result.observation_id != persisted_id:
                    raise TopicObservationError(
                        "budget manual result does not match persisted evidence"
                    )
                if persisted_id is None and result.observation_id != projection_observation.observation_id:
                    raise TopicObservationError(
                        "budget manual result observation conflicts with input projection"
                    )
            elif result.observation_id != projection_observation.observation_id:
                raise TopicObservationError(
                    "stored manual result observation identity conflicts with input projection"
                )
            if (
                manual.reason is ManualReviewReason.LITERATURE_IMPORT_FAILURE
                and persisted_id is not None
                and result.observation_id != persisted_id
            ):
                raise TopicObservationError(
                    "literature failure result does not match persisted evidence"
                )
            if manual.reason in {
                ManualReviewReason.HIGH_RISK_EVENT,
                ManualReviewReason.BUDGET_EXHAUSTED,
                ManualReviewReason.INPUT_ID_CONFLICT,
            } and import_disposition is not None:
                raise TopicObservationError("manual item evidence import disposition is not derivable")
            if manual.reason is ManualReviewReason.LITERATURE_CONFLICT and import_disposition != ImportDisposition.CONFLICT.value:
                raise TopicObservationError("literature conflict evidence import disposition conflicts")
            if manual.reason is ManualReviewReason.LITERATURE_IMPORT_FAILURE and import_disposition not in {
                ImportDisposition.REJECTED.value,
                ImportDisposition.PENDING.value,
            }:
                raise TopicObservationError("literature failure evidence import disposition conflicts")
        else:
            raise TopicObservationError("stored topic-item evidence has no validation rule")

        if result.status is TopicItemStatus.MANUAL_REVIEW:
            if evidence["manual_id"] != result.manual_id:
                raise ManualQueueObservationError("stored manual result and item evidence disagree")
        elif any(evidence[field] is not None for field in ("manual_id", "manual_reason")):
            raise TopicObservationError("non-manual item evidence must not carry manual linkage")

    @staticmethod
    def _load_manual_events(value: object) -> list[dict[str, str]]:
        try:
            if not isinstance(value, list):
                raise TopicObservationError("topic observation state has invalid manual events")
            events: list[dict[str, str]] = []
            for item in value:
                if not isinstance(item, dict):
                    raise TopicObservationError("manual event is malformed")
                _require_fields(item, {"event_type", "manual_id"}, "manual event")
                if item["event_type"] != "CURSOR_CONFLICT":
                    raise TopicObservationError("manual event has an unsupported type")
                _require_nonempty(item["manual_id"], "manual event manual_id")
                events.append({"event_type": item["event_type"], "manual_id": item["manual_id"]})
            event_ids = [item["manual_id"] for item in events]
            if len(event_ids) != len(set(event_ids)):
                raise TopicObservationError("manual event manual_ids must be unique")
            return events
        except ManualQueueObservationError:
            raise
        except (KeyError, TypeError, ValueError, TopicObservationError) as exc:
            raise ManualQueueObservationError(str(exc)) from exc

    @staticmethod
    def _load_manual_queue(value: object) -> list[ManualReviewItem]:
        try:
            if not isinstance(value, list):
                raise TopicObservationError("topic observation state has invalid manual queue")
            manual_queue: list[ManualReviewItem] = []
            for item in value:
                if not isinstance(item, dict):
                    raise TopicObservationError("manual queue entry is malformed")
                manual_queue.append(ManualReviewItem.from_dict(item))
            manual_ids = [item.manual_id for item in manual_queue]
            if len(manual_ids) != len(set(manual_ids)):
                raise TopicObservationError("manual queue manual_ids must be unique")
            for manual in manual_queue:
                if manual.manual_id != _manual_id_for(
                    topic_id=manual.topic_id,
                    cursor=manual.cursor,
                    input_id=manual.input_id,
                    reason=manual.reason,
                    detail=manual.detail,
                ):
                    raise TopicObservationError("manual queue manual_id does not match its fields")
            return manual_queue
        except ManualQueueObservationError:
            raise
        except (KeyError, TypeError, ValueError, TopicObservationError) as exc:
            raise ManualQueueObservationError(str(exc)) from exc

    def _save_state(self, state: Mapping[str, Any]) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(canonical_json(state) + "\n", encoding="utf-8")
        os.replace(temporary, self.state_path)
