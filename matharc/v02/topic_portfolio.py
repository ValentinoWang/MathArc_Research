"""Evidence-declared topic portfolio records for the console's selection plane."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .local_store import LocalStoreError, exclusive_lock, external_root, read_json, state_digest, strict_mapping, write_json_atomic
from .schema import digest_json


TOPIC_CRITERIA = (
    "statement_unambiguous",
    "deterministic_acceptance_available",
    "small_scale_enumerable",
    "general_case_unresolved_reported",
    "publishable_fallback_declared",
)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LocalStoreError(f"{label} must be non-empty text")
    return value


class TopicState(str, Enum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REJECTED = "REJECTED"


class CriterionVerdict(str, Enum):
    DECLARED = "DECLARED"
    NOT_MET = "NOT_MET"
    PENDING_REVIEW = "PENDING_REVIEW"


@dataclass(frozen=True, slots=True)
class TopicCriterion:
    criterion_id: str
    verdict: CriterionVerdict
    evidence_refs: tuple[str, ...]
    note: str

    def __post_init__(self) -> None:
        if self.criterion_id not in TOPIC_CRITERIA:
            raise LocalStoreError("unsupported topic criterion")
        if not isinstance(self.verdict, CriterionVerdict):
            raise LocalStoreError("unsupported topic criterion verdict")
        if tuple(sorted(self.evidence_refs)) != self.evidence_refs or len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise LocalStoreError("criterion evidence refs must be unique and sorted")
        if any(not item.strip() for item in self.evidence_refs):
            raise LocalStoreError("criterion evidence refs must be non-empty")
        _text(self.note, "criterion note")

    def to_dict(self) -> dict[str, Any]:
        return {"criterion_id": self.criterion_id, "verdict": self.verdict.value, "evidence_refs": list(self.evidence_refs), "note": self.note}

    @classmethod
    def from_dict(cls, value: object) -> "TopicCriterion":
        data = strict_mapping(value, {"criterion_id", "verdict", "evidence_refs", "note"}, "topic criterion")
        if not isinstance(data["evidence_refs"], list):
            raise LocalStoreError("criterion evidence refs must be an array")
        return cls(_text(data["criterion_id"], "criterion_id"), CriterionVerdict(data["verdict"]), tuple(_text(item, "criterion evidence ref") for item in data["evidence_refs"]), _text(data["note"], "criterion note"))


@dataclass(frozen=True, slots=True)
class TopicCandidate:
    topic_id: str
    name: str
    state: TopicState
    slot: int | None
    criteria: tuple[TopicCriterion, ...]
    source_observation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.topic_id, "topic_id"); _text(self.name, "topic name")
        if not isinstance(self.state, TopicState):
            raise LocalStoreError("unsupported topic state")
        if self.slot is not None and (not isinstance(self.slot, int) or isinstance(self.slot, bool) or self.slot < 1):
            raise LocalStoreError("topic slot must be a positive integer or null")
        if self.state is TopicState.ACTIVE and self.slot is None:
            raise LocalStoreError("active topic requires an allocated slot")
        if self.state is not TopicState.ACTIVE and self.slot is not None:
            raise LocalStoreError("only active topics may hold a slot")
        if tuple(item.criterion_id for item in self.criteria) != TOPIC_CRITERIA:
            raise LocalStoreError("candidate criteria must match the five fixed criteria")
        if tuple(sorted(self.source_observation_ids)) != self.source_observation_ids or len(set(self.source_observation_ids)) != len(self.source_observation_ids):
            raise LocalStoreError("source observation ids must be unique and sorted")
        if any(not item.strip() for item in self.source_observation_ids):
            raise LocalStoreError("source observation ids must be non-empty")

    @property
    def declared_criteria_count(self) -> int:
        return sum(item.verdict is CriterionVerdict.DECLARED for item in self.criteria)

    def to_dict(self) -> dict[str, Any]:
        return {"topic_id": self.topic_id, "name": self.name, "state": self.state.value, "slot": self.slot, "criteria": [item.to_dict() for item in self.criteria], "source_observation_ids": list(self.source_observation_ids)}

    @classmethod
    def from_dict(cls, value: object) -> "TopicCandidate":
        data = strict_mapping(value, {"topic_id", "name", "state", "slot", "criteria", "source_observation_ids"}, "topic candidate")
        if not isinstance(data["criteria"], list) or not isinstance(data["source_observation_ids"], list):
            raise LocalStoreError("topic candidate arrays are invalid")
        return cls(_text(data["topic_id"], "topic_id"), _text(data["name"], "topic name"), TopicState(data["state"]), data["slot"], tuple(TopicCriterion.from_dict(item) for item in data["criteria"]), tuple(_text(item, "source observation id") for item in data["source_observation_ids"]))


@dataclass(frozen=True, slots=True)
class TopicPortfolio:
    portfolio_id: str
    seat_limit: int
    candidates: tuple[TopicCandidate, ...]

    def __post_init__(self) -> None:
        _text(self.portfolio_id, "portfolio_id")
        if not isinstance(self.seat_limit, int) or isinstance(self.seat_limit, bool) or self.seat_limit < 1:
            raise LocalStoreError("seat_limit must be a positive integer")
        if tuple(item.topic_id for item in self.candidates) != tuple(sorted(item.topic_id for item in self.candidates)):
            raise LocalStoreError("candidates must be ordered by topic_id")
        if len({item.topic_id for item in self.candidates}) != len(self.candidates):
            raise LocalStoreError("candidate topic ids must be unique")
        slots = [item.slot for item in self.candidates if item.slot is not None]
        if len(set(slots)) != len(slots) or any(slot > self.seat_limit for slot in slots):
            raise LocalStoreError("topic seat allocation is invalid")

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {"portfolio_id": self.portfolio_id, "seat_limit": self.seat_limit, "candidates": [item.to_dict() for item in self.candidates]}

    @classmethod
    def from_dict(cls, value: object) -> "TopicPortfolio":
        data = strict_mapping(value, {"portfolio_id", "seat_limit", "candidates"}, "topic portfolio")
        if not isinstance(data["candidates"], list):
            raise LocalStoreError("portfolio candidates must be an array")
        return cls(_text(data["portfolio_id"], "portfolio_id"), data["seat_limit"], tuple(TopicCandidate.from_dict(item) for item in data["candidates"]))


class TopicPortfolioStore:
    """Explicit caller-controlled persistence for one portfolio snapshot."""

    _FILENAME = "topic-portfolio.json"

    def __init__(self, root: str) -> None:
        self.root = external_root(root); self.path = self.root / self._FILENAME

    def _load_payload(self) -> dict[str, Any]:
        data = strict_mapping(read_json(self.path, "topic portfolio") if self.path.exists() else {"schema_version": "1.0", "portfolio": None, "state_digest_sha256": ""}, {"schema_version", "portfolio", "state_digest_sha256"}, "topic portfolio state")
        if data["schema_version"] != "1.0": raise LocalStoreError("unsupported topic portfolio schema")
        if self.path.exists() and data["state_digest_sha256"] != state_digest(data): raise LocalStoreError("topic portfolio state digest mismatch")
        if data["portfolio"] is not None: TopicPortfolio.from_dict(data["portfolio"])
        return dict(data)

    def create(self, portfolio: TopicPortfolio) -> TopicPortfolio:
        with exclusive_lock(self.root, self._FILENAME):
            current = self._load_payload()
            if current["portfolio"] is not None:
                existing = TopicPortfolio.from_dict(current["portfolio"])
                if existing.to_dict() == portfolio.to_dict(): return existing
                raise LocalStoreError("topic portfolio already exists")
            self._write(portfolio)
        return portfolio

    def replace(self, portfolio: TopicPortfolio) -> TopicPortfolio:
        with exclusive_lock(self.root, self._FILENAME): self._write(portfolio)
        return portfolio

    def load(self) -> TopicPortfolio:
        payload = self._load_payload()["portfolio"]
        if payload is None: raise KeyError("topic portfolio is not configured")
        return TopicPortfolio.from_dict(payload)

    def _write(self, portfolio: TopicPortfolio) -> None:
        payload: dict[str, Any] = {"schema_version": "1.0", "portfolio": portfolio.to_dict()}
        payload["state_digest_sha256"] = state_digest(payload)
        write_json_atomic(self.path, payload)
