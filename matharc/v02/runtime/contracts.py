"""Versioned, immutable contracts for MathArc native runtime execution."""
from __future__ import annotations

import json
from dataclasses import dataclass, fields, replace
from enum import Enum
from typing import Any, Mapping
from types import MappingProxyType

from ..schema import canonical_json, digest_json
from .identity import IdentityError, RuntimeIdentity, idempotency_key


class ContractError(ValueError):
    pass


class ExecutionStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    SUCCESS = "SUCCEEDED"
    TIMEOUT = "TIMED_OUT"
    CANCELED = "CANCELLED"


class RunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DRAINING = "DRAINING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    STOPPED = "STOPPED"


class ActionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def _strict(cls: type[Any], payload: Mapping[str, Any]) -> None:
    unknown = set(payload) - {field.name for field in fields(cls)}
    if unknown:
        raise ContractError(f"unknown fields for {cls.__name__}: {sorted(unknown)}")


def _enum(enum_type: type[Enum], value: Any) -> Enum:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"unknown {enum_type.__name__}: {value}") from exc


def _tuple(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise ContractError("expected an array")
    return tuple(value)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_thaw(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class ResearchWorkerSpec:
    worker_id: str
    role: str = "researcher"
    backend: str = "local"
    required: bool = False
    timeout_seconds: float = 300.0
    max_retries: int = 0
    workspace_id: str | None = None
    runtime_run_id: str | None = None
    contract_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.worker_id.strip() or not self.role.strip() or not self.backend.strip():
            raise ContractError("worker_id, role, and backend are required")
        if self.timeout_seconds <= 0 or self.max_retries < 0:
            raise ContractError("timeout_seconds must be positive and max_retries non-negative")
        if not self.contract_version.startswith("1."):
            raise ContractError(f"unsupported contract version: {self.contract_version}")

    def to_dict(self) -> dict[str, Any]:
        return {"worker_id": self.worker_id, "role": self.role, "backend": self.backend,
                "required": self.required, "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries, "workspace_id": self.workspace_id,
                "runtime_run_id": self.runtime_run_id, "contract_version": self.contract_version}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResearchWorkerSpec":
        _strict(cls, payload)
        return cls(**dict(payload))


@dataclass(frozen=True, slots=True)
class ResearchRunSpec:
    workspace_id: str
    trace_id: str
    runtime_run_id: str
    task_id: str
    contract_version: str = "1.0"
    source_digest: str = ""
    evaluator_digest: str = ""
    tool_registry_digest: str = ""
    seed: int | None = None
    budget: Mapping[str, Any] | None = None
    workers: tuple[ResearchWorkerSpec, ...] = ()
    status: RunStatus = RunStatus.CREATED

    def __post_init__(self) -> None:
        for name in ("workspace_id", "trace_id", "runtime_run_id", "task_id", "contract_version"):
            if not getattr(self, name).strip():
                raise ContractError(f"{name} is required")
        if not isinstance(self.status, RunStatus):
            raise TypeError("status must be a RunStatus")
        if any(not isinstance(worker, ResearchWorkerSpec) for worker in self.workers):
            raise TypeError("workers must contain ResearchWorkerSpec")
        for worker in self.workers:
            if worker.workspace_id is not None and worker.workspace_id != self.workspace_id:
                raise ContractError(f"worker {worker.worker_id} belongs to another workspace")
            if worker.runtime_run_id is not None and worker.runtime_run_id != self.runtime_run_id:
                raise ContractError(f"worker {worker.worker_id} belongs to another runtime run")
            if worker.contract_version != self.contract_version:
                raise ContractError(f"worker {worker.worker_id} contract_version does not match run")
        object.__setattr__(self, "budget", _freeze(self.budget or {}))
        object.__setattr__(self, "workers", tuple(self.workers))
        if not self.contract_version.startswith("1."):
            raise ContractError(f"unsupported contract version: {self.contract_version}")

    @property
    def identity(self) -> RuntimeIdentity:
        return RuntimeIdentity(self.workspace_id, self.trace_id, self.runtime_run_id)

    def to_dict(self) -> dict[str, Any]:
        return {"workspace_id": self.workspace_id, "trace_id": self.trace_id,
                "runtime_run_id": self.runtime_run_id, "task_id": self.task_id,
                "contract_version": self.contract_version, "source_digest": self.source_digest,
                "evaluator_digest": self.evaluator_digest, "tool_registry_digest": self.tool_registry_digest,
                "seed": self.seed, "budget": _thaw(self.budget or {}),
                "workers": [worker.to_dict() for worker in self.workers], "status": self.status.value}

    def transition(self, status: RunStatus) -> "ResearchRunSpec":
        """Apply the small, explicit run lifecycle state machine."""
        if not isinstance(status, RunStatus):
            raise TypeError("status must be a RunStatus")
        allowed = {
            RunStatus.CREATED: {RunStatus.RUNNING, RunStatus.CANCELLED},
            RunStatus.RUNNING: {RunStatus.PAUSED, RunStatus.DRAINING, RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.STOPPED},
            RunStatus.PAUSED: {RunStatus.RUNNING, RunStatus.CANCELLED, RunStatus.STOPPED},
            RunStatus.DRAINING: {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.STOPPED},
            RunStatus.COMPLETED: set(), RunStatus.FAILED: set(), RunStatus.CANCELLED: set(), RunStatus.STOPPED: set(),
        }
        if status not in allowed[self.status]:
            raise ContractError(f"invalid run state transition: {self.status.value} -> {status.value}")
        return replace(self, status=status)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResearchRunSpec":
        _strict(cls, payload)
        data = dict(payload)
        data["workers"] = tuple(ResearchWorkerSpec.from_dict(item) for item in data.get("workers", ()))
        data["status"] = _enum(RunStatus, data.get("status", RunStatus.CREATED.value))
        return cls(**data)


@dataclass(frozen=True, slots=True)
class WorkerExecutionResult:
    workspace_id: str
    trace_id: str
    runtime_run_id: str
    generation_id: str
    worker_id: str
    execution_id: str
    status: ExecutionStatus
    result_digest: str = ""
    candidate_ids: tuple[str, ...] = ()
    failure_class: str | None = None
    error: str | None = None
    elapsed_seconds: float | None = None
    contract_version: str = "1.0"

    def __post_init__(self) -> None:
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError("status must be an ExecutionStatus")
        if not isinstance(self.contract_version, str) or not self.contract_version.strip():
            raise ContractError("contract_version is required")
        if not self.contract_version.startswith("1."):
            raise ContractError(f"unsupported contract version: {self.contract_version}")
        try:
            RuntimeIdentity(self.workspace_id, self.trace_id, self.runtime_run_id,
                            self.generation_id, self.worker_id, self.execution_id)
        except IdentityError as exc:
            raise ContractError(str(exc)) from exc
        if self.status in {ExecutionStatus.FAILED, ExecutionStatus.RETRYABLE_FAILURE,
                           ExecutionStatus.TIMED_OUT} and not (self.failure_class or self.error):
            raise ContractError("failed results require failure_class or error")
        object.__setattr__(self, "candidate_ids", tuple(self.candidate_ids))

    @property
    def idempotency_key(self) -> str:
        return f"{idempotency_key(self.runtime_run_id, self.generation_id)}+{self.worker_id}+{self.execution_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"workspace_id": self.workspace_id, "trace_id": self.trace_id,
                "runtime_run_id": self.runtime_run_id, "generation_id": self.generation_id,
                "worker_id": self.worker_id, "execution_id": self.execution_id,
                "status": self.status.value, "result_digest": self.result_digest,
                "candidate_ids": list(self.candidate_ids), "failure_class": self.failure_class,
                "error": self.error, "elapsed_seconds": self.elapsed_seconds,
                "contract_version": self.contract_version}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkerExecutionResult":
        _strict(cls, payload)
        data = dict(payload)
        data["status"] = _enum(ExecutionStatus, data["status"])
        data["candidate_ids"] = tuple(data.get("candidate_ids", ()))
        return cls(**data)


@dataclass(frozen=True, slots=True)
class CandidateEnvelope:
    candidate_id: str
    workspace_id: str
    trace_id: str
    runtime_run_id: str
    generation_id: str
    task_digest: str = ""
    source_digest: str = ""
    evaluator_digest: str = ""
    tool_registry_digest: str = ""
    budget_digest: str = ""
    artifact_digest: str = ""
    payload_digest: str = ""
    worker_id: str | None = None
    execution_id: str | None = None

    def __post_init__(self) -> None:
        try:
            if (self.worker_id is None) != (self.execution_id is None):
                raise IdentityError("worker_id and execution_id must be supplied together")
            if self.worker_id is None:
                RuntimeIdentity(self.workspace_id, self.trace_id, self.runtime_run_id, self.generation_id)
            else:
                RuntimeIdentity(self.workspace_id, self.trace_id, self.runtime_run_id, self.generation_id,
                                self.worker_id, self.execution_id, self.candidate_id)
        except IdentityError as exc:
            raise ContractError(str(exc)) from exc

    @property
    def identity_digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in ("candidate_id", "workspace_id", "trace_id",
                "runtime_run_id", "generation_id", "task_digest", "source_digest", "evaluator_digest",
                "tool_registry_digest", "budget_digest", "artifact_digest", "payload_digest", "worker_id", "execution_id")}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateEnvelope":
        _strict(cls, payload)
        return cls(**dict(payload))


@dataclass(frozen=True, slots=True)
class RuntimeActionReceipt:
    action_id: str
    action: str
    actor: str
    target_runtime_run_id: str
    status: ActionStatus
    previous_state: RunStatus | None = None
    resulting_state: RunStatus | None = None
    reason: str | None = None
    contract_version: str = "1.0"

    def __post_init__(self) -> None:
        if not isinstance(self.status, ActionStatus):
            raise TypeError("status must be an ActionStatus")
        if self.previous_state is not None and not isinstance(self.previous_state, RunStatus):
            raise TypeError("previous_state must be a RunStatus")
        if self.resulting_state is not None and not isinstance(self.resulting_state, RunStatus):
            raise TypeError("resulting_state must be a RunStatus")

    def to_dict(self) -> dict[str, Any]:
        return {"action_id": self.action_id, "action": self.action, "actor": self.actor,
                "target_runtime_run_id": self.target_runtime_run_id, "status": self.status.value,
                "previous_state": self.previous_state.value if self.previous_state else None,
                "resulting_state": self.resulting_state.value if self.resulting_state else None,
                "reason": self.reason, "contract_version": self.contract_version}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RuntimeActionReceipt":
        _strict(cls, payload)
        data = dict(payload)
        data["status"] = _enum(ActionStatus, data["status"])
        if data.get("previous_state") is not None: data["previous_state"] = _enum(RunStatus, data["previous_state"])
        if data.get("resulting_state") is not None: data["resulting_state"] = _enum(RunStatus, data["resulting_state"])
        return cls(**data)


def _to_json(self: Any) -> str:
    return canonical_json(self.to_dict())


def _from_json(cls: type[Any], value: str) -> Any:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ContractError("invalid contract JSON") from exc
    return cls.from_dict(payload)


for _contract_type in (ResearchRunSpec, ResearchWorkerSpec, WorkerExecutionResult,
                       CandidateEnvelope, RuntimeActionReceipt):
    setattr(_contract_type, "to_json", _to_json)
    setattr(_contract_type, "from_json", classmethod(_from_json))


# Descriptive aliases keep the public surface readable for callers that use
# the word ``Result`` or ``Run`` in their type names.
ExecutionResultStatus = ExecutionStatus
RuntimeRunStatus = RunStatus
RuntimeActionStatus = ActionStatus


__all__ = ["ContractError", "ExecutionStatus", "ExecutionResultStatus", "RunStatus", "RuntimeRunStatus", "ActionStatus", "RuntimeActionStatus", "ResearchRunSpec",
           "ResearchWorkerSpec", "WorkerExecutionResult", "CandidateEnvelope", "RuntimeActionReceipt"]
