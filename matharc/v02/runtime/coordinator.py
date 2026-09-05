"""Coordinator for the first-party MathArc execution backends."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..schema import digest_json
from .contracts import CandidateEnvelope, ContractError, ExecutionStatus, ResearchRunSpec, ResearchWorkerSpec, WorkerExecutionResult
from .generation import GenerationCommit, GenerationInputSnapshot
from .identity import IdentityError, RuntimeIdentity
from .evaluator import EvaluationContract, EvaluationRequest, EvaluationResult, EvaluationStatus
from .backends.base import Backend, BackendRequest, DeterministicTestBackend, as_request
from .backends.codex import CodexBackend
from .backends.local_process import LocalExactToolBackend


@dataclass(frozen=True, slots=True)
class CoordinatorRun:
    smoke_result: EvaluationResult
    results: tuple[WorkerExecutionResult, ...] = ()
    candidates: tuple[CandidateEnvelope, ...] = ()
    started_full_run: bool = False

    @property
    def success(self) -> bool:
        return self.smoke_result.passed and any(r.status is ExecutionStatus.SUCCEEDED for r in self.results)


class RuntimeCoordinator:
    """Run smoke-gated workers and assemble proposal-only candidate envelopes."""

    ALLOWED_BACKENDS = ("deterministic-test", "deterministic", "codex", "local", "local-exact-tool", "local_process")

    def __init__(self, backends: Mapping[str, Backend] | None = None, *, backend_registry: Mapping[str, Backend] | None = None,
                 runtime_store: Any | None = None, evaluator: EvaluationContract | None = None) -> None:
        selected_backends = backends if backends is not None else backend_registry
        self.backends: dict[str, Backend] = dict(selected_backends or {
            "deterministic-test": DeterministicTestBackend(),
            "codex": CodexBackend(),
            "local-exact-tool": LocalExactToolBackend(),
            "local": LocalExactToolBackend(),
        })
        unknown = set(self.backends) - set(self.ALLOWED_BACKENDS)
        if unknown:
            raise ValueError(f"unsupported MathArc backend(s): {sorted(unknown)}")
        self.runtime_store = runtime_store
        self.evaluator = evaluator
        self._seen: dict[str, WorkerExecutionResult] = {}
        self._request_digests: dict[str, str] = {}
        self._approved_tasks: dict[str, Mapping[str, Any]] = {}
        self._started_tasks: set[str] = set()
        self._lock = threading.Lock()

    def ingest_approved_task(self, task: Mapping[str, Any]) -> str:
        """Register an approved dynamic task without starting execution."""
        if not isinstance(task, Mapping):
            raise TypeError("approved task must be a mapping")
        task_id = task.get("task_id") or task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("approved task requires task_id")
        status = str(task.get("approval_status", task.get("status", ""))).upper()
        if status not in {"APPROVED", "ACCEPTED"}:
            raise PermissionError("task is not approved")
        budget = task.get("budget", {})
        if not isinstance(budget, Mapping):
            raise ValueError("approved task budget must be an object")
        max_cost = budget.get("max_cost")
        if max_cost is not None and (not isinstance(max_cost, (int, float)) or max_cost < 0):
            raise ValueError("approved task max_cost must be non-negative")
        with self._lock:
            existing = self._approved_tasks.get(task_id)
            if existing is not None and dict(existing) != dict(task):
                raise ValueError(f"approved task conflicts with existing task: {task_id}")
            self._approved_tasks[task_id] = dict(task)
        return task_id

    def run_approved_task(self, task_id: str, spec: ResearchRunSpec, **kwargs: Any) -> CoordinatorRun:
        """Consume an approved task exactly once, enforcing its budget."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id is required")
        with self._lock:
            task = self._approved_tasks.get(task_id)
            if task is None:
                raise PermissionError("task has not been approved")
            if task_id in self._started_tasks:
                raise ValueError(f"approved task already started: {task_id}")
            declared = task.get("budget", {})
            requested = dict(spec.budget or {})
            for key in ("max_cost", "max_seconds", "max_steps"):
                if key in declared and key in requested and requested[key] > declared[key]:
                    raise ValueError(f"requested {key} exceeds approved task budget")
            self._started_tasks.add(task_id)
        try:
            return self.run(spec, **kwargs)
        except Exception:
            with self._lock:
                self._started_tasks.discard(task_id)
            raise

    def execute_backend(self, request: BackendRequest | Mapping[str, Any], *, backend: str | None = None) -> WorkerExecutionResult:
        req = as_request(request)
        backend_name = backend or str((req.payload or {}).get("backend", "deterministic-test")) if isinstance(req.payload, Mapping) else backend
        backend_name = backend_name or "deterministic-test"
        aliases = {"deterministic": "deterministic-test", "local": "local-exact-tool", "local_process": "local-exact-tool"}
        requested_backend = backend_name
        backend_name = aliases.get(backend_name, backend_name)
        if backend_name not in self.backends and requested_backend in self.backends:
            backend_name = requested_backend
        if backend_name not in self.backends:
            raise ValueError(f"backend is not enabled: {backend_name}")
        key = req.execution_id or digest_json(req.to_dict() if hasattr(req, "to_dict") else req.request_digest)
        with self._lock:
            if key in self._seen:
                if self._request_digests.get(key) != req.request_digest:
                    raise ValueError(f"execution_id conflicts with a different request: {key}")
                return self._seen[key]
        attempts = 0
        result: WorkerExecutionResult
        while True:
            attempts += 1
            result = self.backends[backend_name].execute(req)
            self._validate_result_identity(req, result)
            if (result.elapsed_seconds is not None and result.elapsed_seconds > req.timeout_seconds
                    and result.status is ExecutionStatus.SUCCEEDED):
                result = WorkerExecutionResult(
                    workspace_id=result.workspace_id, trace_id=result.trace_id,
                    runtime_run_id=result.runtime_run_id, generation_id=result.generation_id,
                    worker_id=result.worker_id, execution_id=result.execution_id,
                    status=ExecutionStatus.TIMED_OUT, result_digest=result.result_digest,
                    candidate_ids=(), failure_class="TIMEOUT", error="backend exceeded timeout",
                    elapsed_seconds=result.elapsed_seconds, contract_version=result.contract_version)
            if result.status is not ExecutionStatus.RETRYABLE_FAILURE or attempts > req.max_retries:
                break
        with self._lock:
            self._seen[key] = result
            self._request_digests[key] = req.request_digest
        # RuntimeStore is an optional execution ledger only.  Never pass a
        # trace/workspace object or invoke mathematical promotion here.
        if self.runtime_store is not None:
            recorder = getattr(self.runtime_store, "record_execution", None) or getattr(self.runtime_store, "append", None)
            if callable(recorder):
                recorder(result)
        return result

    @staticmethod
    def _validate_result_identity(request: BackendRequest, result: WorkerExecutionResult) -> None:
        """Require a backend result to be an exact child of its request."""
        if not isinstance(result, WorkerExecutionResult):
            raise ContractError("backend must return WorkerExecutionResult")
        expected = RuntimeIdentity(request.workspace_id, request.trace_id, request.runtime_run_id,
                                   request.generation_id, request.worker_id, request.execution_id)
        actual = RuntimeIdentity(result.workspace_id, result.trace_id, result.runtime_run_id,
                                 result.generation_id, result.worker_id, result.execution_id)
        try:
            expected.require_ancestor_of(actual)
            actual.require_ancestor_of(expected)
        except IdentityError as exc:
            raise ContractError(f"backend result identity mismatch: {exc}") from exc
        if result.contract_version != request.contract_version:
            raise ContractError("backend result contract_version does not match request")

    def assemble_candidate(self, spec: ResearchRunSpec, request: BackendRequest,
                           result: WorkerExecutionResult) -> tuple[CandidateEnvelope, ...]:
        if result.status is not ExecutionStatus.SUCCEEDED:
            return ()
        if (request.workspace_id, request.trace_id, request.runtime_run_id) != (
                spec.workspace_id, spec.trace_id, spec.runtime_run_id):
            raise ContractError("backend request identity does not match run spec")
        self._validate_result_identity(request, result)
        candidate_ids = result.candidate_ids or (f"candidate-{result.result_digest[:16]}",)
        task_digest = digest_json({"task_id": spec.task_id})
        budget_digest = digest_json(dict(spec.budget or request.budget))
        payload_digest = digest_json(request.payload)
        return tuple(CandidateEnvelope(candidate_id=cid, workspace_id=result.workspace_id,
            trace_id=result.trace_id, runtime_run_id=result.runtime_run_id,
            generation_id=result.generation_id, task_digest=task_digest,
            source_digest=spec.source_digest, evaluator_digest=spec.evaluator_digest,
            tool_registry_digest=spec.tool_registry_digest, budget_digest=budget_digest,
            artifact_digest=result.result_digest, payload_digest=payload_digest,
            worker_id=result.worker_id, execution_id=result.execution_id) for cid in candidate_ids)

    def run(self, spec: ResearchRunSpec, *, evaluator: EvaluationContract | None = None,
            evaluation_input: Any = None, smoke: EvaluationRequest | None = None,
            generation_snapshot: GenerationInputSnapshot | None = None) -> CoordinatorRun:
        if self.runtime_store is not None:
            creator = getattr(self.runtime_store, "create_run", None)
            if callable(creator):
                creator(spec)
        contract = evaluator or self.evaluator
        if contract is None:
            contract = EvaluationContract(spec.task_id, lambda req: True,
                                          budget=_budget_from_spec(spec))
        workers = spec.workers or (ResearchWorkerSpec(worker_id="worker-1", backend="deterministic-test"),)
        for worker in workers:
            if worker.workspace_id is not None and worker.workspace_id != spec.workspace_id:
                raise ContractError(f"worker {worker.worker_id} belongs to another workspace")
            if worker.runtime_run_id is not None and worker.runtime_run_id != spec.runtime_run_id:
                raise ContractError(f"worker {worker.worker_id} belongs to another runtime run")
            if worker.contract_version != spec.contract_version:
                raise ContractError(f"worker {worker.worker_id} contract_version does not match run")
        snapshot = generation_snapshot or GenerationInputSnapshot.from_inputs(
            workspace_id=spec.workspace_id, trace_id=spec.trace_id,
            runtime_run_id=spec.runtime_run_id, generation_id="generation-1",
            trace={"trace_id": spec.trace_id},
            contract={"task_id": spec.task_id, "evaluator_id": contract.evaluator_id,
                      "budget": contract.budget.to_dict(), "contract_version": spec.contract_version},
            agenda=evaluation_input, worker_specs=workers,
            tool_registry=tuple(sorted(self.backends)), source_payload=evaluation_input,
            contract_version=spec.contract_version)
        if (snapshot.workspace_id, snapshot.trace_id, snapshot.runtime_run_id) != (
                spec.workspace_id, spec.trace_id, spec.runtime_run_id):
            raise ContractError("generation snapshot does not match run identity")
        if snapshot.generation_id != "generation-1":
            raise ContractError("generation snapshot does not match coordinator generation")
        if snapshot.contract_version != spec.contract_version:
            raise ContractError("generation snapshot contract_version does not match run")
        if tuple(sorted(snapshot.worker_ids)) != tuple(sorted(worker.worker_id for worker in workers)):
            raise ContractError("generation snapshot workers do not match run")
        smoke_request = smoke or EvaluationRequest(spec.task_id, contract.evaluator_id,
            input=evaluation_input, seed=int(spec.seed or 0), budget=contract.budget, smoke=True)
        if hasattr(contract, "smoke_test"):
            smoke_result = contract.smoke_test(smoke_request)
        else:
            smoke_result = contract.evaluate(smoke_request)
        if not smoke_result.passed:
            return CoordinatorRun(smoke_result=smoke_result, started_full_run=False)
        results: list[WorkerExecutionResult] = []
        candidates: list[CandidateEnvelope] = []
        for worker in workers:
            req = BackendRequest(spec.workspace_id, spec.trace_id, spec.runtime_run_id,
                f"generation-1", worker.worker_id, spec.task_id, evaluation_input,
                int(spec.seed or 0), worker.timeout_seconds, worker.max_retries,
                execution_id=f"exec-{spec.runtime_run_id}-{worker.worker_id}", budget=dict(spec.budget or {}),
                contract_version=spec.contract_version)
            result = self.execute_backend(req, backend=worker.backend)
            results.append(result)
            worker_candidates = self.assemble_candidate(spec, req, result)
            candidates.extend(worker_candidates)
            if self.runtime_store is not None:
                importer = getattr(self.runtime_store, "import_candidate", None)
                if callable(importer):
                    for candidate in worker_candidates:
                        importer(candidate)
        if self.runtime_store is not None:
            commit_recorder = getattr(self.runtime_store, "record_generation_commit", None)
            if callable(commit_recorder):
                accepted = tuple(result.execution_id for result in results if result.status is ExecutionStatus.SUCCEEDED)
                failed = tuple(result.execution_id for result in results if result.status is not ExecutionStatus.SUCCEEDED)
                status = "COMPLETED" if results and not failed else ("PARTIAL" if accepted else "FAILED")
                commit_recorder(GenerationCommit(
                    workspace_id=spec.workspace_id,
                    trace_id=spec.trace_id,
                    runtime_run_id=spec.runtime_run_id,
                    generation_id="generation-1",
                    snapshot_digest=snapshot.snapshot_digest,
                    results=tuple(results),
                    accepted_result_ids=accepted,
                    failed_result_ids=failed,
                    status=status,
                ).to_dict())
        return CoordinatorRun(smoke_result=smoke_result, results=tuple(results),
                              candidates=tuple(candidates), started_full_run=True)

    def execute(self, request: Any, **kwargs: Any) -> Any:
        if isinstance(request, BackendRequest) or isinstance(request, Mapping):
            # A direct backend execution is useful to adapters and remains
            # subject to the same idempotency and failure classification.
            if isinstance(request, Mapping) and "task_id" not in request:
                raise ValueError("backend request requires task_id")
            return self.execute_backend(request, backend=kwargs.get("backend"))
        return self.run(request, **kwargs)


def _budget_from_spec(spec: ResearchRunSpec):
    from .evaluator import EvaluationBudget
    raw = dict(spec.budget or {})
    return EvaluationBudget(max_seconds=float(raw.get("max_seconds", 30)),
                            max_steps=int(raw.get("max_steps", 1000)),
                            max_cost=raw.get("max_cost"))


BackendCoordinator = RuntimeCoordinator

__all__ = ["RuntimeCoordinator", "BackendCoordinator", "CoordinatorRun", "DeterministicTestBackend", "CodexBackend", "LocalExactToolBackend"]
