"""Candidate synthesis and counterexample review boundaries.

Execution output is deliberately kept separate from mathematical trace state:
this module can create candidate envelopes and queue suspected counterexamples,
but it never promotes claims or mutates routes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from ..schema import canonical_json, digest_json, utc_now
from .contracts import CandidateEnvelope


class SynthesisError(ValueError):
    pass


def _is_digest(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


@dataclass(frozen=True, slots=True)
class ExplorationCandidate:
    envelope: CandidateEnvelope
    payload: Any
    provenance: Mapping[str, Any]
    candidate_kind: str = "exploration"
    claim_ids: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        kind = str(self.candidate_kind).strip().lower()
        if kind not in {"exploration", "counterexample", "suspected_counterexample"}:
            raise SynthesisError("candidate_kind must be exploration or counterexample")
        if not self.envelope.candidate_id or self.candidate_id != self.envelope.candidate_id:
            raise SynthesisError("candidate identity is missing from envelope")
        if not _is_digest(self.envelope.payload_digest):
            raise SynthesisError("candidate envelope requires a SHA-256 payload digest")
        if digest_json(self.payload) != self.envelope.payload_digest:
            raise SynthesisError("candidate payload digest does not match envelope")
        provenance = dict(self.provenance or {})
        required = ("candidate_id", "workspace_id", "trace_id", "runtime_run_id", "generation_id")
        missing = [key for key in required if not str(provenance.get(key, "")).strip()]
        if missing:
            raise SynthesisError(f"candidate provenance misses fields: {missing}")
        if any(provenance.get(key) != getattr(self.envelope, key)
               for key in ("candidate_id", "workspace_id", "trace_id", "runtime_run_id", "generation_id")):
            raise SynthesisError("candidate provenance does not match envelope identity")
        declared = provenance.get("provenance_digest")
        if declared is not None and declared != self.provenance_digest:
            raise SynthesisError("candidate provenance digest does not match provenance")
        object.__setattr__(self, "candidate_kind", kind)
        object.__setattr__(self, "claim_ids", tuple(str(item) for item in self.claim_ids))

    @property
    def candidate_id(self) -> str:
        return self.envelope.candidate_id

    @property
    def provenance_digest(self) -> str:
        provenance = dict(self.provenance)
        provenance.pop("provenance_digest", None)
        return digest_json(provenance)

    def to_dict(self) -> dict[str, Any]:
        return {"envelope": self.envelope.to_dict(), "payload": self.payload,
                "provenance": {**dict(self.provenance), "provenance_digest": self.provenance_digest},
                "provenance_digest": self.provenance_digest,
                "candidate_kind": self.candidate_kind,
                "claim_ids": list(self.claim_ids), "created_at": self.created_at}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExplorationCandidate":
        allowed = {"envelope", "payload", "provenance", "provenance_digest", "candidate_kind", "claim_ids", "created_at"}
        unknown = set(payload) - allowed
        if unknown:
            raise SynthesisError(f"unknown candidate fields: {sorted(unknown)}")
        candidate = cls(CandidateEnvelope.from_dict(payload["envelope"]), payload.get("payload"),
                        dict(payload.get("provenance") or {}), str(payload.get("candidate_kind", "exploration")),
                        tuple(str(x) for x in payload.get("claim_ids", ())), str(payload.get("created_at") or utc_now()))
        declared = payload.get("provenance_digest")
        if declared is not None and declared != candidate.provenance_digest:
            raise SynthesisError("candidate provenance digest does not match provenance")
        return candidate


def _value(output: Any, name: str, default: Any = "") -> Any:
    if isinstance(output, Mapping):
        return output.get(name, default)
    return getattr(output, name, default)


def synthesize_candidate(output: Any, *, workspace_id: str | None = None,
                         trace_id: str | None = None, runtime_run_id: str | None = None,
                         generation_id: str | None = None, task_digest: str = "",
                         source_digest: str = "", evaluator_digest: str = "",
                         tool_registry_digest: str = "", budget_digest: str = "",
                         artifact_digest: str = "", payload: Any = None,
                         candidate_kind: str = "exploration",
                         claim_ids: tuple[str, ...] = (),
                         candidate_origin: str | None = None) -> ExplorationCandidate:
    """Normalize ordinary worker output without granting proof authority."""
    normalized_kind = str(candidate_kind).strip().lower()
    if normalized_kind not in {"exploration", "counterexample", "suspected_counterexample"}:
        raise SynthesisError("candidate_kind must be exploration or counterexample")
    origin = str(candidate_origin or _value(output, "candidate_origin", "") or
                 _value(output, "source_kind", "") or "runtime-execution").strip()
    if isinstance(output, CandidateEnvelope):
        effective_payload = output.to_dict() if payload is None else payload
        if not output.payload_digest or digest_json(effective_payload) != output.payload_digest:
            raise SynthesisError("candidate envelope payload digest does not match payload")
        provenance = output.to_dict() | {"source": origin, "candidate_origin": origin,
                                         "candidate_id": output.candidate_id}
        return ExplorationCandidate(output, effective_payload,
                                    provenance, normalized_kind, tuple(claim_ids))
    workspace_id = str(workspace_id or _value(output, "workspace_id"))
    trace_id = str(trace_id or _value(output, "trace_id"))
    runtime_run_id = str(runtime_run_id or _value(output, "runtime_run_id"))
    generation_id = str(generation_id or _value(output, "generation_id"))
    for name, value in (("workspace_id", workspace_id), ("trace_id", trace_id),
                        ("runtime_run_id", runtime_run_id), ("generation_id", generation_id)):
        if not value.strip():
            raise SynthesisError(f"{name} is required to preserve candidate provenance")
    worker_id = str(_value(output, "worker_id", "unknown-worker"))
    execution_id = str(_value(output, "execution_id", "execution"))
    payload = _value(output, "payload", output) if payload is None else payload
    if isinstance(payload, Mapping) and payload is output:
        payload = dict(payload)
    task_digest = task_digest or str(_value(output, "task_digest", "")) or (
        digest_json(_value(output, "task")) if _value(output, "task", None) is not None else digest_json(payload)
    )
    source_digest = source_digest or str(_value(output, "source_digest", "")) or (
        digest_json(_value(output, "source")) if _value(output, "source", None) is not None else ""
    )
    evaluator_digest = evaluator_digest or str(_value(output, "evaluator_digest", "")) or (
        digest_json(_value(output, "evaluator")) if _value(output, "evaluator", None) is not None else ""
    )
    tool_registry_digest = tool_registry_digest or str(_value(output, "tool_registry_digest", "")) or (
        digest_json(_value(output, "tool_registry")) if _value(output, "tool_registry", None) is not None else ""
    )
    budget_digest = budget_digest or str(_value(output, "budget_digest", "")) or (
        digest_json({"budget": _value(output, "budget"), "seed": _value(output, "seed")})
        if (_value(output, "budget", None) is not None or _value(output, "seed", None) is not None) else ""
    )
    artifact_digest = artifact_digest or str(_value(output, "artifact_digest", "")) or (
        digest_json(_value(output, "artifact")) if _value(output, "artifact", None) is not None else digest_json(payload)
    )
    payload_digest = digest_json(payload)
    identity = {"workspace_id": workspace_id, "trace_id": trace_id, "runtime_run_id": runtime_run_id,
                "generation_id": generation_id, "worker_id": worker_id, "execution_id": execution_id,
                "task_digest": task_digest, "source_digest": source_digest,
                "evaluator_digest": evaluator_digest, "tool_registry_digest": tool_registry_digest,
                "budget_digest": budget_digest, "artifact_digest": artifact_digest,
                "payload_digest": payload_digest, "candidate_origin": origin}
    candidate_id = "cand-" + digest_json(identity)
    envelope = CandidateEnvelope(
        candidate_id=candidate_id,
        workspace_id=workspace_id,
        trace_id=trace_id,
        runtime_run_id=runtime_run_id,
        generation_id=generation_id,
        task_digest=task_digest,
        source_digest=source_digest,
        evaluator_digest=evaluator_digest,
        tool_registry_digest=tool_registry_digest,
        budget_digest=budget_digest,
        artifact_digest=artifact_digest,
        payload_digest=payload_digest,
        worker_id=worker_id,
        execution_id=execution_id,
    )
    provenance = {**identity, "candidate_id": candidate_id, "source": origin,
                  "candidate_origin": origin}
    return ExplorationCandidate(envelope, payload, provenance, normalized_kind,
                                tuple(str(x) for x in claim_ids or _value(output, "claim_ids", ())))


standardize_execution_output = synthesize_candidate
normalize_execution_output = synthesize_candidate
create_candidate = synthesize_candidate
Candidate = ExplorationCandidate


@dataclass(frozen=True, slots=True)
class CounterexampleReview:
    review_id: str
    candidate: ExplorationCandidate
    status: str = "PENDING"
    reviewer: str = ""
    rationale: str = ""
    reviewed_at: str | None = None

    def __post_init__(self) -> None:
        status = str(self.status).strip().upper()
        if status not in {"PENDING", "ACCEPTED", "REJECTED"}:
            raise SynthesisError(f"unknown counterexample review status: {self.status}")
        if status == "PENDING" and (str(self.reviewer).strip() or str(self.rationale).strip() or self.reviewed_at):
            raise SynthesisError("pending review cannot carry reviewer, rationale, or reviewed_at")
        if status != "PENDING" and (not str(self.reviewer).strip() or not str(self.rationale).strip() or not self.reviewed_at):
            raise SynthesisError("resolved review requires reviewer, rationale, and reviewed_at")
        object.__setattr__(self, "status", status)


class CounterexampleReviewQueue:
    def __init__(self) -> None:
        self._items: dict[str, CounterexampleReview] = {}

    def submit(self, candidate: ExplorationCandidate) -> CounterexampleReview:
        if candidate.candidate_kind.upper() not in {"COUNTEREXAMPLE", "SUSPECTED_COUNTEREXAMPLE"}:
            raise SynthesisError("only suspected counterexamples enter the review queue")
        review_id = "review-" + digest_json({"candidate_id": candidate.candidate_id,
                                               "provenance": dict(candidate.provenance)})
        existing = self._items.get(review_id)
        if existing:
            return existing
        item = CounterexampleReview(review_id, candidate)
        self._items[review_id] = item
        return item

    def pending(self) -> tuple[CounterexampleReview, ...]:
        # Treat an externally corrupted queue as invalid rather than silently
        # dropping an item from the review surface.
        for item in self._items.values():
            if item.status not in {"PENDING", "ACCEPTED", "REJECTED"}:
                raise SynthesisError("review queue contains an invalid status")
        return tuple(item for item in self._items.values() if item.status == "PENDING")

    def resolve(self, review_id: str, *, accepted: bool, reviewer: str,
                rationale: str = "") -> CounterexampleReview:
        try:
            item = self._items[review_id]
        except KeyError as exc:
            raise SynthesisError("unknown review id") from exc
        if item.status != "PENDING":
            raise SynthesisError("review has already been resolved")
        if not isinstance(accepted, bool):
            raise SynthesisError("accepted must be a boolean")
        if not str(reviewer).strip() or not str(rationale).strip():
            raise SynthesisError("reviewer and rationale are required")
        updated = CounterexampleReview(item.review_id, item.candidate,
            "ACCEPTED" if accepted else "REJECTED", reviewer, rationale, utc_now())
        self._items[review_id] = updated
        return updated

    @property
    def reviews(self) -> tuple[CounterexampleReview, ...]:
        return tuple(self._items.values())


CounterexampleQueue = CounterexampleReviewQueue


def queue_counterexample(candidate: ExplorationCandidate, queue: CounterexampleReviewQueue | None = None) -> CounterexampleReview:
    return (queue or CounterexampleReviewQueue()).submit(candidate)


__all__ = ["SynthesisError", "ExplorationCandidate", "Candidate", "synthesize_candidate",
           "standardize_execution_output", "normalize_execution_output", "create_candidate", "CounterexampleReview", "CounterexampleReviewQueue", "CounterexampleQueue",
           "queue_counterexample"]
