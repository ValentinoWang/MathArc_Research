"""Common MathArc backend request/result boundary."""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from ...schema import digest_json
from ..contracts import ExecutionStatus, WorkerExecutionResult


@dataclass(frozen=True, slots=True)
class BackendRequest:
    workspace_id: str
    trace_id: str
    runtime_run_id: str
    generation_id: str
    worker_id: str
    task_id: str
    payload: Any = None
    seed: int = 0
    timeout_seconds: float = 300.0
    max_retries: int = 0
    execution_id: str | None = None
    cancel_event: Any = field(default=None, compare=False, repr=False)
    budget: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("workspace_id", "trace_id", "runtime_run_id", "generation_id", "worker_id", "task_id"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.timeout_seconds <= 0 or self.max_retries < 0:
            raise ValueError("timeout_seconds must be positive and max_retries non-negative")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], **defaults: Any) -> "BackendRequest":
        data = dict(payload)
        # Accept the common aliases used by HTTP callers and run contracts.
        if "input" in data and "payload" not in data:
            data["payload"] = data.pop("input")
        if "run_id" in data and "runtime_run_id" not in data:
            data["runtime_run_id"] = data.pop("run_id")
        data.update({key: value for key, value in defaults.items() if key not in data})
        return cls(**data)

    @property
    def request_digest(self) -> str:
        return digest_json({"workspace_id": self.workspace_id, "trace_id": self.trace_id,
            "runtime_run_id": self.runtime_run_id, "generation_id": self.generation_id,
            "worker_id": self.worker_id, "task_id": self.task_id, "payload": self.payload,
            "seed": self.seed, "budget": dict(self.budget)})

    def to_dict(self) -> dict[str, Any]:
        return {"workspace_id": self.workspace_id, "trace_id": self.trace_id,
                "runtime_run_id": self.runtime_run_id, "generation_id": self.generation_id,
                "worker_id": self.worker_id, "task_id": self.task_id, "payload": self.payload,
                "seed": self.seed, "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries, "execution_id": self.execution_id,
                "budget": dict(self.budget)}


class Backend(Protocol):
    name: str
    def execute(self, request: BackendRequest) -> WorkerExecutionResult: ...


class BackendExecutionError(RuntimeError):
    def __init__(self, message: str, *, failure_class: str = "BACKEND_ERROR", retryable: bool = False) -> None:
        super().__init__(message)
        self.failure_class = failure_class
        self.retryable = retryable


def as_request(request: BackendRequest | Mapping[str, Any], **defaults: Any) -> BackendRequest:
    return request if isinstance(request, BackendRequest) else BackendRequest.from_mapping(request, **defaults)


def result_for(request: BackendRequest, status: ExecutionStatus, *, result_digest: str = "",
               candidate_ids: tuple[str, ...] = (), failure_class: str | None = None,
               error: str | None = None, elapsed_seconds: float | None = None) -> WorkerExecutionResult:
    return WorkerExecutionResult(workspace_id=request.workspace_id, trace_id=request.trace_id,
        runtime_run_id=request.runtime_run_id, generation_id=request.generation_id,
        worker_id=request.worker_id, execution_id=request.execution_id or f"exec-{uuid.uuid4().hex[:16]}",
        status=status, result_digest=result_digest, candidate_ids=tuple(candidate_ids),
        failure_class=failure_class, error=error, elapsed_seconds=elapsed_seconds)


class DeterministicTestBackend:
    """Pure backend used for contract tests and deterministic smoke runs."""
    name = "deterministic-test"

    def __init__(self, output: Any = None, *, fail: bool = False, failure_class: str = "TEST_FAILURE") -> None:
        self.output = output
        self.fail = fail
        self.failure_class = failure_class
        self.calls = 0

    def execute(self, request: BackendRequest | Mapping[str, Any]) -> WorkerExecutionResult:
        req = as_request(request)
        self.calls += 1
        started = time.monotonic()
        if req.cancel_event is not None and getattr(req.cancel_event, "is_set", lambda: False)():
            return result_for(req, ExecutionStatus.CANCELLED, failure_class="CANCELLED", error="cancelled",
                              elapsed_seconds=time.monotonic() - started)
        if self.fail:
            return result_for(req, ExecutionStatus.FAILED, failure_class=self.failure_class,
                              error="deterministic backend failure", elapsed_seconds=time.monotonic() - started)
        output = self.output if self.output is not None else {"task_id": req.task_id, "seed": req.seed, "payload": req.payload}
        digest = digest_json(output)
        candidate = f"candidate-{digest[:16]}"
        return result_for(req, ExecutionStatus.SUCCEEDED, result_digest=digest,
                          candidate_ids=(candidate,), elapsed_seconds=time.monotonic() - started)


__all__ = ["BackendRequest", "Backend", "BackendExecutionError", "as_request", "result_for", "DeterministicTestBackend"]
