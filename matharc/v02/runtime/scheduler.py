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

from .budget import ResourceLedger, ResourceReceipt, SemanticDeduplicator, semantic_experiment_key
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
    def __init__(self, *, max_concurrency: int = 1, workspace_root: str | Path | None = None, ledger: ResourceLedger | None = None, deduplicator: SemanticDeduplicator | None = None, max_retries: int = 0, timeout_seconds: float | None = None, process_mode: bool = False, use_processes: bool | None = None) -> None:
        if isinstance(max_concurrency, bool) or not isinstance(max_concurrency, int) or max_concurrency < 1:
            raise ValueError("max_concurrency must be a positive integer")
        if max_retries < 0 or (timeout_seconds is not None and timeout_seconds <= 0):
            raise ValueError("invalid retry or timeout limit")
        self.max_concurrency = max_concurrency
        self.workspace_root = Path(workspace_root) if workspace_root is not None else Path(tempfile.mkdtemp(prefix="matharc-runtime-"))
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger or ResourceLedger()
        self.deduplicator = deduplicator or SemanticDeduplicator()
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.process_mode = bool(process_mode if use_processes is None else use_processes)
        self._started: set[str] = set()
        self._lock = threading.Lock()

    def schedule(self, tasks: Iterable[Any], snapshot: GenerationInputSnapshot, worker: Callable[..., Any], *, run_id: str | None = None) -> tuple[ScheduledExecution, ...]:
        run_id = run_id or snapshot.runtime_run_id or f"run-{uuid.uuid4().hex[:12]}"
        snapshot_digest = getattr(snapshot, "input_digest_sha256", None) or getattr(snapshot, "snapshot_digest", "")
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
            if not self.deduplicator.claim(task, execution_id=idem, snapshot_digest=snapshot_digest):
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
                measured = result if isinstance(result, Mapping) else {}
                receipt = ResourceReceipt(
                    execution_id,
                    wall_seconds=float(measured.get("wall_seconds", measured.get("duration_seconds", wall)) or wall),
                    input_tokens=int(measured.get("input_tokens", 0) or 0),
                    output_tokens=int(measured.get("output_tokens", 0) or 0),
                    cost_usd=float(measured.get("cost_usd", 0.0) or 0.0),
                    status=status,
                    semantic_key=semantic_experiment_key(task, snapshot_digest=snapshot_digest),
                )
                self.ledger.record_receipt(receipt)
                results.append(ScheduledExecution(member, execution_id, f"{run_id}:{snapshot.generation_id}:{member}", str(workspace), status, attempts, result, error, {"recovered": status in {"timeout", "failed"}, "execution_id": execution_id}, receipt))
        return tuple(skipped + results)

    run = schedule
    schedule_tasks = schedule
    execute_parallel = schedule


Scheduler = BoundedScheduler
BoundedParallelScheduler = BoundedScheduler

__all__ = ["GenerationInputSnapshot", "ScheduledExecution", "BoundedScheduler", "BoundedParallelScheduler", "Scheduler", "WorkerCallable"]
