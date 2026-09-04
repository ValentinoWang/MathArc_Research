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


@dataclass(frozen=True, slots=True)
class ExplorationCandidate:
    envelope: CandidateEnvelope
    payload: Any
    provenance: Mapping[str, Any]
    candidate_kind: str = "exploration"
    claim_ids: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)

    @property
    def candidate_id(self) -> str:
        return self.envelope.candidate_id

    @property
    def provenance_digest(self) -> str:
        return digest_json(dict(self.provenance))

    def to_dict(self) -> dict[str, Any]:
        return {"envelope": self.envelope.to_dict(), "payload": self.payload,
                "provenance": dict(self.provenance), "candidate_kind": self.candidate_kind,
                "claim_ids": list(self.claim_ids), "created_at": self.created_at}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExplorationCandidate":
        allowed = {"envelope", "payload", "provenance", "candidate_kind", "claim_ids", "created_at"}
        unknown = set(payload) - allowed
        if unknown:
            raise SynthesisError(f"unknown candidate fields: {sorted(unknown)}")
        return cls(CandidateEnvelope.from_dict(payload["envelope"]), payload.get("payload"),
                   dict(payload.get("provenance") or {}), str(payload.get("candidate_kind", "exploration")),
                   tuple(str(x) for x in payload.get("claim_ids", ())), str(payload.get("created_at") or utc_now()))


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
    claim_ids: tuple[str, ...] = ()) -> ExplorationCandidate:
    """Normalize ordinary worker output without granting proof authority."""
    if isinstance(output, CandidateEnvelope):
        provenance = output.to_dict() | {"source": "runtime-execution", "candidate_id": output.candidate_id}
        return ExplorationCandidate(output, output.to_dict() if payload is None else payload,
                                    provenance, candidate_kind, tuple(claim_ids))
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
                "payload_digest": payload_digest}
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
    provenance = {**identity, "candidate_id": candidate_id, "source": "runtime-execution"}
    return ExplorationCandidate(envelope, payload, provenance, candidate_kind,
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
        return tuple(item for item in self._items.values() if item.status == "PENDING")

    def resolve(self, review_id: str, *, accepted: bool, reviewer: str,
                rationale: str = "") -> CounterexampleReview:
        item = self._items[review_id]
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
