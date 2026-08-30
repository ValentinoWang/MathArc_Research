from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, TypeVar

from .schema import FailureClass, FailureRecord, digest_json, utc_now
from .trace import ResearchTrace

_FailureMemoryT = TypeVar("_FailureMemoryT", bound="FailureMemory")

_TOKEN_RE = re.compile(r"[\w]+", flags=re.UNICODE)


def _tokens(*values: str) -> frozenset[str]:
    result: set[str] = set()
    for value in values:
        result.update(token for token in _TOKEN_RE.findall(value.lower()) if len(token) > 1)
    return frozenset(result)


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


@dataclass(slots=True)
class FailureLesson:
    lesson_id: str
    source_run_id: str
    failure_id: str
    failure_class: FailureClass
    claim_statement: str
    mechanism_signature: tuple[str, ...]
    trigger: str
    diagnosis: str
    minimal_witness: str
    repair: str
    reusable_lesson: str
    exact: bool
    reused_count: int = 0
    created_at: str = field(default_factory=utc_now)

    @property
    def fingerprint(self) -> frozenset[str]:
        return _tokens(
            self.claim_statement,
            " ".join(self.mechanism_signature),
            self.trigger,
            self.diagnosis,
            self.repair,
            self.reusable_lesson,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "source_run_id": self.source_run_id,
            "failure_id": self.failure_id,
            "failure_class": self.failure_class.value,
            "claim_statement": self.claim_statement,
            "mechanism_signature": list(self.mechanism_signature),
            "trigger": self.trigger,
            "diagnosis": self.diagnosis,
            "minimal_witness": self.minimal_witness,
            "repair": self.repair,
            "reusable_lesson": self.reusable_lesson,
            "exact": self.exact,
            "reused_count": self.reused_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FailureLesson":
        return cls(
            lesson_id=str(payload["lesson_id"]),
            source_run_id=str(payload["source_run_id"]),
            failure_id=str(payload["failure_id"]),
            failure_class=FailureClass(str(payload["failure_class"])),
            claim_statement=str(payload["claim_statement"]),
            mechanism_signature=tuple(str(item) for item in payload.get("mechanism_signature", [])),
            trigger=str(payload["trigger"]),
            diagnosis=str(payload["diagnosis"]),
            minimal_witness=str(payload.get("minimal_witness", "")),
            repair=str(payload["repair"]),
            reusable_lesson=str(payload["reusable_lesson"]),
            exact=bool(payload.get("exact", False)),
            reused_count=int(payload.get("reused_count", 0)),
            created_at=str(payload.get("created_at") or utc_now()),
        )


@dataclass(slots=True)
class FailureMatch:
    lesson_id: str
    score: float
    failure_class: str
    claim_statement: str
    diagnosis: str
    repair: str
    reusable_lesson: str
    exact: bool
    source_run_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "score": round(self.score, 6),
            "failure_class": self.failure_class,
            "claim_statement": self.claim_statement,
            "diagnosis": self.diagnosis,
            "repair": self.repair,
            "reusable_lesson": self.reusable_lesson,
            "exact": self.exact,
            "source_run_id": self.source_run_id,
        }


class FailureMemory:
    """Cross-run memory for failed proof moves and their repairs.

    Retrieval is deliberately transparent: a token-level similarity score is
    combined with an explicit failure-class bonus and an exact-witness bonus.
    This keeps the memory inspectable and prevents opaque nearest-neighbour
    matches from becoming mathematical premises.
    """

    def __init__(self, lessons: Iterable[FailureLesson] = ()) -> None:
        self._lessons: dict[str, FailureLesson] = {}
        for lesson in lessons:
            self.add(lesson)

    @property
    def lessons(self) -> tuple[FailureLesson, ...]:
        return tuple(self._lessons[key] for key in sorted(self._lessons))

    def add(self, lesson: FailureLesson) -> None:
        existing = self._lessons.get(lesson.lesson_id)
        if existing is not None and existing.to_dict() != lesson.to_dict():
            raise ValueError(f"conflicting failure lesson id: {lesson.lesson_id}")
        self._lessons[lesson.lesson_id] = lesson

    def ingest_trace(self, trace: ResearchTrace) -> int:
        added = 0
        for failure in trace.failures:
            claim = trace.claims[failure.claim_id]
            route = trace.routes[failure.route_id]
            lesson = FailureLesson(
                lesson_id=f"{trace.run_id}:{failure.failure_id}",
                source_run_id=trace.run_id,
                failure_id=failure.failure_id,
                failure_class=failure.failure_class,
                claim_statement=claim.statement,
                mechanism_signature=route.mechanism_signature,
                trigger=failure.trigger,
                diagnosis=failure.diagnosis,
                minimal_witness=failure.minimal_witness,
                repair=failure.repair,
                reusable_lesson=failure.reusable_lesson,
                exact=failure.exact,
                reused_count=failure.reused_count,
                created_at=failure.created_at,
            )
            if lesson.lesson_id not in self._lessons:
                added += 1
            self.add(lesson)
        return added

    def query(
        self,
        statement: str,
        *,
        mechanism_signature: Iterable[str] = (),
        failure_class: FailureClass | None = None,
        top_k: int = 5,
        minimum_score: float = 0.08,
    ) -> list[FailureMatch]:
        query_tokens = _tokens(statement, " ".join(mechanism_signature))
        matches: list[FailureMatch] = []
        for lesson in self._lessons.values():
            lexical = _jaccard(query_tokens, lesson.fingerprint)
            class_bonus = 0.18 if failure_class is lesson.failure_class else 0.0
            exact_bonus = 0.04 if lesson.exact else 0.0
            reuse_bonus = min(0.08, lesson.reused_count * 0.01)
            score = min(1.0, 0.70 * lexical + class_bonus + exact_bonus + reuse_bonus)
            if score < minimum_score:
                continue
            matches.append(
                FailureMatch(
                    lesson_id=lesson.lesson_id,
                    score=score,
                    failure_class=lesson.failure_class.value,
                    claim_statement=lesson.claim_statement,
                    diagnosis=lesson.diagnosis,
                    repair=lesson.repair,
                    reusable_lesson=lesson.reusable_lesson,
                    exact=lesson.exact,
                    source_run_id=lesson.source_run_id,
                )
            )
        matches.sort(key=lambda item: (-item.score, item.lesson_id))
        return matches[: max(0, top_k)]

    def mark_reused(self, lesson_id: str) -> None:
        try:
            self._lessons[lesson_id].reused_count += 1
        except KeyError as exc:
            raise KeyError(f"unknown failure lesson: {lesson_id}") from exc

    def metrics(self) -> dict[str, Any]:
        total = len(self._lessons)
        reusable = sum(
            bool(item.repair.strip() and item.reusable_lesson.strip())
            for item in self._lessons.values()
        )
        reused = sum(item.reused_count > 0 for item in self._lessons.values())
        exact = sum(item.exact for item in self._lessons.values())
        return {
            "lesson_count": total,
            "reusable_lesson_rate": reusable / total if total else 1.0,
            "lesson_reuse_rate": reused / total if total else 0.0,
            "exact_failure_rate": exact / total if total else 0.0,
            "memory_digest_sha256": digest_json(self.to_dict()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "lessons": [item.to_dict() for item in self.lessons],
        }

    @classmethod
    def from_dict(cls: "type[_FailureMemoryT]", payload: dict[str, Any]) -> "_FailureMemoryT":
        if set(payload) - {"schema_version", "lessons"}:
            raise ValueError("unknown failure memory fields")
        if str(payload.get("schema_version", "1.0")) != "1.0":
            raise ValueError("unsupported failure memory schema")
        return cls(FailureLesson.from_dict(item) for item in payload.get("lessons", []))

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    @classmethod
    def load(cls: "type[_FailureMemoryT]", path: str | Path) -> "_FailureMemoryT":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("failure memory root must be an object")
        return cls.from_dict(payload)
