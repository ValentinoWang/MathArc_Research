"""The sole deterministic reducer for a research generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .contracts import ExecutionStatus, ResearchWorkerSpec, WorkerExecutionResult
from .generation import GenerationClosePolicy, GenerationCommit, GenerationError, GenerationInputSnapshot


@dataclass
class GenerationReducer:
    snapshot: GenerationInputSnapshot
    workers: tuple[ResearchWorkerSpec, ...] = ()
    close_policy: GenerationClosePolicy = GenerationClosePolicy()

    def __post_init__(self) -> None:
        self._closed_commit: GenerationCommit | None = None
        self._late_results: list[WorkerExecutionResult] = []

    @property
    def late_results(self) -> tuple[WorkerExecutionResult, ...]:
        return tuple(self._late_results)

    @property
    def closed_commit(self) -> GenerationCommit | None:
        return self._closed_commit

    def submit(self, result: WorkerExecutionResult) -> str:
        self._validate_result(result)
        if self._closed_commit is not None:
            self._late_results.append(result)
            return "LATE_QUEUED"
        return "ACCEPTED"

    def reduce(self, results: Sequence[WorkerExecutionResult], *, elapsed_seconds: float | None = None) -> GenerationCommit:
        if self._closed_commit is not None:
            incoming = tuple(results)
            if incoming and all(r.to_dict() == old.to_dict() for r, old in zip(incoming, self._closed_commit.results)):
                return self._closed_commit
            for result in incoming: self.submit(result)
            return self._closed_commit
        by_key: dict[str, WorkerExecutionResult] = {}
        duplicate: list[str] = []
        for result in results:
            self._validate_result(result)
            key = result.idempotency_key
            existing = by_key.get(key)
            if existing is None:
                by_key[key] = result
            elif existing.to_dict() == result.to_dict():
                duplicate.append(result.execution_id)
            else:
                raise GenerationError(f"conflicting result for idempotency key: {key}")
        ordered = tuple(sorted(by_key.values(), key=lambda r: (r.generation_id, r.worker_id, r.execution_id, r.result_digest)))
        accepted = tuple(r.execution_id for r in ordered if r.status is ExecutionStatus.SUCCEEDED)
        failed = tuple(r.execution_id for r in ordered if r.status is not ExecutionStatus.SUCCEEDED)
        status = "COMPLETED" if len(accepted) >= self.close_policy.minimum_completed and all(
            any(r.worker_id == worker and r.status is ExecutionStatus.SUCCEEDED for r in ordered)
            for worker in self.close_policy.required_worker_ids) else ("PARTIAL" if accepted else "FAILED")
        commit = GenerationCommit(self.snapshot.workspace_id, self.snapshot.trace_id, self.snapshot.runtime_run_id,
                                  self.snapshot.generation_id, self.snapshot.snapshot_digest, ordered,
                                  accepted, tuple(duplicate), failed, status,
                                  self.close_policy.should_close(ordered, elapsed_seconds=elapsed_seconds))
        if commit.closed: self._closed_commit = commit
        return commit

    def commit(self, results: Sequence[WorkerExecutionResult], *, elapsed_seconds: float | None = None) -> GenerationCommit:
        return self.reduce(results, elapsed_seconds=elapsed_seconds)

    def _validate_result(self, result: WorkerExecutionResult) -> None:
        if not isinstance(result, WorkerExecutionResult):
            raise TypeError("GenerationReducer accepts WorkerExecutionResult only")
        if (result.workspace_id, result.trace_id, result.runtime_run_id, result.generation_id) != (
            self.snapshot.workspace_id, self.snapshot.trace_id, self.snapshot.runtime_run_id, self.snapshot.generation_id):
            raise GenerationError("result identity does not match frozen generation snapshot")
        if self.snapshot.worker_ids and result.worker_id not in self.snapshot.worker_ids:
            raise GenerationError(f"unknown worker for generation: {result.worker_id}")


__all__ = ["GenerationReducer"]
