"""Frozen generation inputs and immutable generation commits."""
from __future__ import annotations

from dataclasses import dataclass, fields
import json
from typing import Any, Mapping, Sequence

from ..schema import digest_json
from .contracts import ExecutionStatus, ResearchWorkerSpec, WorkerExecutionResult
from .identity import IdentityError, RuntimeIdentity, idempotency_key


class GenerationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GenerationInputSnapshot:
    workspace_id: str
    trace_id: str
    runtime_run_id: str
    generation_id: str
    trace_digest: str
    contract_digest: str
    agenda_digest: str
    worker_spec_digest: str
    tool_registry_digest: str
    worker_ids: tuple[str, ...] = ()
    source_payload_digest: str = ""

    def __post_init__(self) -> None:
        try:
            RuntimeIdentity(self.workspace_id, self.trace_id, self.runtime_run_id, self.generation_id)
        except IdentityError as exc:
            raise GenerationError(str(exc)) from exc
        for name in ("trace_digest", "contract_digest", "agenda_digest", "worker_spec_digest", "tool_registry_digest"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise GenerationError(f"{name} must be non-empty")
        if len(set(self.worker_ids)) != len(self.worker_ids):
            raise GenerationError("worker_ids must be unique")

    @property
    def idempotency_key(self) -> str:
        return idempotency_key(self.runtime_run_id, self.generation_id)

    @property
    def snapshot_digest(self) -> str:
        return digest_json(self.to_dict())

    @classmethod
    def from_inputs(cls, *, workspace_id: str, trace_id: str, runtime_run_id: str,
                    generation_id: str, trace: Any, contract: Any, agenda: Any,
                    worker_specs: Sequence[ResearchWorkerSpec] | Any,
                    tool_registry: Any, source_payload: Any = None) -> "GenerationInputSnapshot":
        workers = tuple(worker_specs)
        worker_ids = tuple(sorted(worker.worker_id for worker in workers)) if workers and isinstance(workers[0], ResearchWorkerSpec) else ()
        return cls(workspace_id, trace_id, runtime_run_id, generation_id,
                   digest_json(trace), digest_json(contract), digest_json(agenda),
                   digest_json([worker.to_dict() if hasattr(worker, "to_dict") else worker for worker in workers]),
                   digest_json(tool_registry), worker_ids,
                   digest_json(source_payload) if source_payload is not None else "")

    def to_dict(self) -> dict[str, Any]:
        return {field.name: (list(getattr(self, field.name)) if field.name == "worker_ids" else getattr(self, field.name))
                for field in fields(self)}

    def to_json(self) -> str:
        from ..schema import canonical_json
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GenerationInputSnapshot":
        allowed = {field.name for field in fields(cls)}
        unknown = set(payload) - allowed
        if unknown: raise GenerationError(f"unknown fields for GenerationInputSnapshot: {sorted(unknown)}")
        data = dict(payload); data["worker_ids"] = tuple(data.get("worker_ids", ()))
        return cls(**data)

    @classmethod
    def from_json(cls, value: str) -> "GenerationInputSnapshot":
        try:
            return cls.from_dict(json.loads(value))
        except (TypeError, json.JSONDecodeError) as exc:
            raise GenerationError("invalid generation input JSON") from exc


@dataclass(frozen=True, slots=True)
class GenerationClosePolicy:
    minimum_completed: int = 1
    required_worker_ids: tuple[str, ...] = ()
    timeout_seconds: float | None = None
    allow_partial: bool = True
    close_on_all_terminal: bool = True

    def __post_init__(self) -> None:
        if self.minimum_completed < 0 or (self.timeout_seconds is not None and self.timeout_seconds <= 0):
            raise GenerationError("invalid close policy threshold")
        if len(set(self.required_worker_ids)) != len(self.required_worker_ids):
            raise GenerationError("required_worker_ids must be unique")

    def should_close(self, results: Sequence[WorkerExecutionResult], *, elapsed_seconds: float | None = None) -> bool:
        terminal = [r for r in results if r.status is not ExecutionStatus.RETRYABLE_FAILURE]
        completed = [r for r in terminal if r.status is ExecutionStatus.SUCCEEDED]
        required_done = all(any(r.worker_id == worker and r.status is ExecutionStatus.SUCCEEDED for r in results)
                            for worker in self.required_worker_ids)
        timed_out = self.timeout_seconds is not None and elapsed_seconds is not None and elapsed_seconds >= self.timeout_seconds
        return (len(completed) >= self.minimum_completed and required_done) or timed_out or (
            self.close_on_all_terminal and bool(results) and len(terminal) == len(results))


@dataclass(frozen=True, slots=True)
class GenerationCommit:
    workspace_id: str
    trace_id: str
    runtime_run_id: str
    generation_id: str
    snapshot_digest: str
    results: tuple[WorkerExecutionResult, ...]
    accepted_result_ids: tuple[str, ...] = ()
    duplicate_result_ids: tuple[str, ...] = ()
    failed_result_ids: tuple[str, ...] = ()
    status: str = "PARTIAL"
    closed: bool = True
    commit_digest: str = ""

    def __post_init__(self) -> None:
        if not self.commit_digest:
            object.__setattr__(self, "commit_digest", digest_json(self.to_dict(include_digest=False)))
        if any(result.generation_id != self.generation_id or result.runtime_run_id != self.runtime_run_id
               for result in self.results):
            raise GenerationError("commit contains a result from another generation")

    @property
    def idempotency_key(self) -> str:
        return idempotency_key(self.runtime_run_id, self.generation_id)

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload = {"workspace_id": self.workspace_id, "trace_id": self.trace_id,
                   "runtime_run_id": self.runtime_run_id, "generation_id": self.generation_id,
                   "snapshot_digest": self.snapshot_digest, "results": [r.to_dict() for r in self.results],
                   "accepted_result_ids": list(self.accepted_result_ids), "duplicate_result_ids": list(self.duplicate_result_ids),
                   "failed_result_ids": list(self.failed_result_ids), "status": self.status, "closed": self.closed}
        if include_digest: payload["commit_digest"] = self.commit_digest
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GenerationCommit":
        allowed = {field.name for field in fields(cls)}
        unknown = set(payload) - allowed
        if unknown: raise GenerationError(f"unknown fields for GenerationCommit: {sorted(unknown)}")
        data = dict(payload)
        data["results"] = tuple(WorkerExecutionResult.from_dict(item) for item in data.get("results", ()))
        for key in ("accepted_result_ids", "duplicate_result_ids", "failed_result_ids"): data[key] = tuple(data.get(key, ()))
        value = cls(**data)
        if payload.get("commit_digest") and payload["commit_digest"] != value.commit_digest:
            raise GenerationError("commit digest mismatch")
        return value

    def to_json(self) -> str:
        from ..schema import canonical_json
        return canonical_json(self.to_dict())

    @classmethod
    def from_json(cls, value: str) -> "GenerationCommit":
        try:
            return cls.from_dict(json.loads(value))
        except (TypeError, json.JSONDecodeError) as exc:
            raise GenerationError("invalid generation commit JSON") from exc


def __getattr__(name: str) -> Any:
    # Avoid a module cycle while keeping GenerationReducer available from the
    # generation contract namespace specified by the product contract.
    if name == "GenerationReducer":
        from .reducer import GenerationReducer
        return GenerationReducer
    raise AttributeError(name)


__all__ = ["GenerationError", "GenerationInputSnapshot", "GenerationClosePolicy", "GenerationCommit", "GenerationReducer"]
