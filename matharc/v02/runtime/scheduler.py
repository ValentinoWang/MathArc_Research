"""Bounded, replayable scheduling over frozen generation inputs."""
from __future__ import annotations

import inspect
import tempfile
import threading
import time
import uuid
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Protocol

from .budget import ResourceLedger, ResourceReceipt, SemanticDeduplicator, semantic_experiment_key, _normalise_budget
from .generation import GenerationInputSnapshot


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, frozenset)):
        return [_plain(v) for v in value]
    return value


@dataclass(frozen=True, slots=True)
class ScheduledExecution:
    member_id: str
    execution_id: str
    idempotency_key: str
    workspace: str
    status: str
    attempts: int = 1
    result: Any = None
    error: str | None = None
    recovery_receipt: Mapping[str, Any] = field(default_factory=dict)
    resource_receipt: ResourceReceipt | None = None


class WorkerCallable(Protocol):
    def __call__(self, task: Any, snapshot: GenerationInputSnapshot, workspace: Path, execution_id: str) -> Any: ...


def _invoke(worker: Callable[..., Any], task: Any, snapshot: GenerationInputSnapshot, workspace: Path, execution_id: str) -> Any:
    """Support both the full worker protocol and simple one-argument test workers."""
    try:
        params = inspect.signature(worker).parameters
        count = len([p for p in params.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])
    except (TypeError, ValueError):
        count = 4
    if count >= 4:
        return worker(task, snapshot, workspace, execution_id)
    if count == 3:
        return worker(task, snapshot, workspace)
    if count == 2:
        return worker(task, snapshot)
    return worker(task)


class BoundedScheduler:
    def __init__(self, *, max_concurrency: int = 1, workspace_root: str | Path | None = None,
                 ledger: ResourceLedger | None = None, deduplicator: SemanticDeduplicator | None = None,
                 runtime_store: Any | None = None, budget: Mapping[str, Any] | None = None,
                 declared_budget: Mapping[str, Any] | None = None, max_retries: int = 0,
                 timeout_seconds: float | None = None, process_mode: bool = False,
                 use_processes: bool | None = None) -> None:
        if isinstance(max_concurrency, bool) or not isinstance(max_concurrency, int) or max_concurrency < 1:
            raise ValueError("max_concurrency must be a positive integer")
        if max_retries < 0 or (timeout_seconds is not None and timeout_seconds <= 0):
            raise ValueError("invalid retry or timeout limit")
        self.max_concurrency = max_concurrency
        self.workspace_root = Path(workspace_root) if workspace_root is not None else Path(tempfile.mkdtemp(prefix="matharc-runtime-"))
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.runtime_store = runtime_store
        if ledger is not None and budget is not None:
            raise ValueError("provide ledger or budget, not both")
        if ledger is None:
            limits = _ledger_limits(budget or {})
            ledger = ResourceLedger(runtime_store=runtime_store, **limits)
        elif runtime_store is not None and getattr(ledger, "runtime_store", None) is None:
            ledger.runtime_store = runtime_store
        self.ledger = ledger
        self.deduplicator = deduplicator or SemanticDeduplicator(runtime_store=runtime_store)
        self.declared_budget = dict(declared_budget or {})
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.process_mode = bool(process_mode if use_processes is None else use_processes)
        self._started: set[str] = set()
        self._lock = threading.Lock()

    def schedule(self, tasks: Iterable[Any], snapshot: GenerationInputSnapshot, worker: Callable[..., Any], *, run_id: str | None = None) -> tuple[ScheduledExecution, ...]:
        snapshot_run_id = getattr(snapshot, "runtime_run_id", "")
        # The snapshot is authoritative.  Keep accepting the historical
        # override argument, but never let it create a second runtime identity.
        run_id = snapshot_run_id or run_id or f"run-{uuid.uuid4().hex[:12]}"
        snapshot_digest = getattr(snapshot, "snapshot_digest", "")
        task_list = list(tasks)
        submissions: list[tuple[Any, str, str, Path, int]] = []
        skipped: list[ScheduledExecution] = []
        for index, task in enumerate(task_list):
            member_id = str(getattr(task, "member_id", None) or (task.get("member_id") if isinstance(task, Mapping) else None) or (task.get("id") if isinstance(task, Mapping) else f"member-{index}"))
            idem = f"{run_id}:{snapshot.generation_id}:{member_id}"
            with self._lock:
                if idem in self._started:
                    skipped.append(ScheduledExecution(member_id, f"execution-{uuid.uuid4().hex[:12]}", idem, "", "duplicate", 0))
                    continue
                self._started.add(idem)
            declared = _task_budget(task, self.declared_budget)
            try:
                task_budget = _normalise_budget(declared)
                global_budget = _normalise_budget(self.declared_budget)
                if any(name in global_budget and value > global_budget[name] for name, value in task_budget.items()):
                    raise ValueError("task declaration exceeds scheduler declared budget")
                admitted = self.ledger.admit(declared, execution_id=idem)
            except ValueError as exc:
                skipped.append(ScheduledExecution(member_id, f"execution-{uuid.uuid4().hex[:12]}", idem, "", "budget_rejected", 0, error=str(exc)))
                continue
            if not admitted:
                skipped.append(ScheduledExecution(member_id, f"execution-{uuid.uuid4().hex[:12]}", idem, "", "budget_exceeded", 0, error="declared budget exceeds remaining runtime budget"))
                continue
            if not self.deduplicator.claim(task, execution_id=idem, snapshot_digest=snapshot_digest, runtime_store=self.runtime_store):
                self.ledger.release(idem)
                skipped.append(ScheduledExecution(member_id, f"execution-{uuid.uuid4().hex[:12]}", idem, "", "deduplicated", 0))
                continue
            execution_id = f"exec-{uuid.uuid4().hex}"
            workspace = self.workspace_root / execution_id
            workspace.mkdir(parents=True, exist_ok=False)
            submissions.append((task, member_id, execution_id, workspace, 0))
        results: list[ScheduledExecution] = []
        executor_type = ProcessPoolExecutor if self.process_mode else ThreadPoolExecutor
        executor_kwargs = {"max_workers": self.max_concurrency}
        if not self.process_mode:
            executor_kwargs["thread_name_prefix"] = "matharc-worker"
        with executor_type(**executor_kwargs) as pool:
            pending: dict[Future[Any], tuple[Any, str, str, Path, int, float]] = {
                pool.submit(_invoke, worker, task, snapshot, workspace, execution_id): (task, member, execution_id, workspace, attempt, time.monotonic())
                for task, member, execution_id, workspace, attempt in submissions
            }
            for future, (task, member, execution_id, workspace, attempt, started) in list(pending.items()):
                status, result, error, attempts = "completed", None, None, 1
                current = future
                while True:
                    try:
                        result = current.result(timeout=self.timeout_seconds)
                        status = "completed"
                        break
                    except TimeoutError:
                        current.cancel(); status, error = "timeout", "worker timed out"
                    except BaseException as exc:  # worker failures become receipts, never scheduler crashes
                        status, error = "failed", f"{type(exc).__name__}: {exc}"
                    if attempts > self.max_retries:
                        break
                    attempts += 1
                    current = pool.submit(_invoke, worker, task, snapshot, workspace, execution_id)
                wall = max(0.0, time.monotonic() - started)
                validation_error = _validate_worker_result(result, snapshot, execution_id)
                if validation_error:
                    status, error = "failed", validation_error
                # Worker resource fields are advisory.  Validate them for
                # malformed/conflicting receipts, but charge only scheduler
                # wall time and the already admitted declaration.
                try:
                    advisory = _advisory_receipt(result, execution_id)
                    if advisory is not None:
                        _validate_advisory_consistency(result, advisory)
                except ValueError as exc:
                    if validation_error is None:
                        status, error = "failed", str(exc)
                receipt = ResourceReceipt(
                    execution_id,
                    wall_seconds=wall,
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0.0,
                    status=status,
                    semantic_key=semantic_experiment_key(task, snapshot_digest=snapshot_digest),
                )
                try:
                    self.ledger.validate_receipt(receipt)
                except ValueError as exc:
                    self.ledger.release(idem)
                    status = "budget_exceeded" if "budget" in str(exc) or "declaration" in str(exc) else "failed"
                    error = str(exc)
                results.append(ScheduledExecution(member, execution_id, f"{run_id}:{snapshot.generation_id}:{member}", str(workspace), status, attempts, result, error, {"recovered": status in {"timeout", "failed"}, "execution_id": execution_id}, receipt))
        return tuple(skipped + results)

    run = schedule
    schedule_tasks = schedule
    execute_parallel = schedule


Scheduler = BoundedScheduler
BoundedParallelScheduler = BoundedScheduler

__all__ = ["GenerationInputSnapshot", "ScheduledExecution", "BoundedScheduler", "BoundedParallelScheduler", "Scheduler", "WorkerCallable"]


def _ledger_limits(value: Mapping[str, Any]) -> dict[str, Any]:
    """Convert public budget aliases into ResourceLedger constructor fields."""
    if not isinstance(value, Mapping):
        raise ValueError("budget must be a mapping")
    aliases = {
        "wall_seconds_limit": ("wall_seconds", "max_seconds", "timeout_seconds"),
        "input_token_limit": ("input_tokens", "max_input_tokens"),
        "output_token_limit": ("output_tokens", "max_output_tokens"),
        "cost_usd_limit": ("cost_usd", "max_cost", "max_cost_usd"),
    }
    result = {}
    for field, keys in aliases.items():
        values = [value[key] for key in keys if key in value and value[key] is not None]
        if values:
            if any(item != values[0] for item in values[1:]):
                raise ValueError(f"conflicting budget declarations for {field}")
            result[field] = values[0]
    return result


def _task_budget(task: Any, fallback: Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(task, Mapping):
        value = task.get("budget", fallback)
    else:
        value = getattr(task, "budget", fallback)
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("task budget must be a mapping")
    return dict(value)


def _advisory_receipt(result: Any, execution_id: str) -> ResourceReceipt | None:
    if isinstance(result, Mapping):
        payload = result
    elif hasattr(result, "to_dict") and callable(result.to_dict):
        try:
            payload = result.to_dict()
        except Exception:
            return None
    else:
        return None
    nested = payload.get("resource_receipt", payload.get("receipt"))
    fields = {key: payload[key] for key in ("wall_seconds", "duration_seconds", "input_tokens", "output_tokens", "cost_usd") if key in payload}
    if nested is not None:
        if not isinstance(nested, Mapping):
            raise ValueError("resource receipt must be a mapping")
        if fields:
            for key, value in fields.items():
                if key in nested and nested[key] != value:
                    raise ValueError(f"conflicting resource receipt field: {key}")
        fields = dict(nested)
    if not fields:
        return None
    return ResourceReceipt.from_mapping(fields, execution_id=execution_id)


def _validate_advisory_consistency(result: Any, advisory: ResourceReceipt) -> None:
    payload = result if isinstance(result, Mapping) else (result.to_dict() if hasattr(result, "to_dict") else {})
    receipt_id = payload.get("receipt_execution_id")
    if receipt_id is not None and receipt_id != advisory.execution_id:
        raise ValueError("resource receipt execution_id conflicts with scheduler execution")


def _validate_worker_result(result: Any, snapshot: GenerationInputSnapshot, execution_id: str) -> str | None:
    if isinstance(result, Mapping):
        payload = result
    elif hasattr(result, "to_dict") and callable(result.to_dict):
        try:
            payload = result.to_dict()
        except Exception:
            return "worker result could not be serialized"
    else:
        return None
    expected = {
        "workspace_id": snapshot.workspace_id,
        "trace_id": snapshot.trace_id,
        "runtime_run_id": snapshot.runtime_run_id,
        "generation_id": snapshot.generation_id,
        "execution_id": execution_id,
    }
    for field, value in expected.items():
        if field in payload and payload[field] != value:
            return f"worker result {field} does not match snapshot identity"
    if "run_id" in payload and payload["run_id"] != snapshot.runtime_run_id:
        return "worker result run_id does not match snapshot identity"
    return None
