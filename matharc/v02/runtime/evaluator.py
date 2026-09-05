"""Budgeted, seeded evaluator contract for the native MathArc runtime.

The evaluator is intentionally side-effect free.  A smoke evaluation is a
necessary preflight; a failed smoke run is terminal for the coordinator and
must never start a full research run.
"""
from __future__ import annotations

import inspect
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Protocol

from ..schema import digest_json


class EvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class EvaluationBudget:
    """Hard limits shared by smoke and full evaluation."""

    max_seconds: float = 30.0
    max_steps: int = 1000
    max_cost: float | None = None

    def __post_init__(self) -> None:
        if self.max_seconds <= 0 or self.max_steps <= 0:
            raise ValueError("evaluation budget limits must be positive")
        if self.max_cost is not None:
            try:
                valid_cost = (not isinstance(self.max_cost, bool)
                              and math.isfinite(float(self.max_cost))
                              and float(self.max_cost) >= 0)
            except (TypeError, ValueError):
                valid_cost = False
            if not valid_cost:
                raise ValueError("max_cost must be a finite non-negative number")

    def to_dict(self) -> dict[str, Any]:
        return {"max_seconds": self.max_seconds, "max_steps": self.max_steps,
                "max_cost": self.max_cost}

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class EvaluationRequest:
    task_id: str
    evaluator_id: str
    input: Any = None
    seed: int = 0
    budget: EvaluationBudget = field(default_factory=EvaluationBudget)
    smoke: bool = False

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.evaluator_id.strip():
            raise ValueError("task_id and evaluator_id are required")
        if isinstance(self.budget, Mapping):
            object.__setattr__(self, "budget", EvaluationBudget(
                max_seconds=float(self.budget.get("max_seconds", 30)),
                max_steps=int(self.budget.get("max_steps", 1000)),
                max_cost=self.budget.get("max_cost")))
        elif not isinstance(self.budget, EvaluationBudget):
            raise TypeError("budget must be EvaluationBudget")

    @property
    def input_digest(self) -> str:
        return digest_json(self.input)

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "evaluator_id": self.evaluator_id,
                "input": self.input, "seed": self.seed,
                "budget": self.budget.to_dict(), "smoke": self.smoke}

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "EvaluationRequest":
        data = dict(payload)
        if "input_payload" in data and "input" not in data:
            data["input"] = data.pop("input_payload")
        unknown = set(data) - {"task_id", "evaluator_id", "input", "seed", "budget", "smoke"}
        if unknown:
            raise ValueError(f"unknown evaluation request fields: {sorted(unknown)}")
        return cls(**data)

    from_dict = from_mapping


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    status: EvaluationStatus
    evaluator_id: str
    task_id: str
    seed: int
    budget_digest: str
    score: float | None = None
    output: Any = None
    steps: int = 0
    elapsed_seconds: float = 0.0
    error: str | None = None
    smoke: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.status, EvaluationStatus):
            raise TypeError("status must be EvaluationStatus")
        if self.steps < 0 or self.elapsed_seconds < 0:
            raise ValueError("steps and elapsed_seconds must be non-negative")

    @property
    def passed(self) -> bool:
        return self.status is EvaluationStatus.PASS

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status.value, "evaluator_id": self.evaluator_id,
                "task_id": self.task_id, "seed": self.seed,
                "budget_digest": self.budget_digest, "score": self.score,
                "output": self.output, "steps": self.steps,
                "elapsed_seconds": self.elapsed_seconds, "error": self.error,
                "smoke": self.smoke}

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "EvaluationResult":
        data = dict(payload)
        unknown = set(data) - {"status", "evaluator_id", "task_id", "seed", "budget_digest", "score", "output", "steps", "elapsed_seconds", "error", "smoke"}
        if unknown:
            raise ValueError(f"unknown evaluation result fields: {sorted(unknown)}")
        data["status"] = EvaluationStatus(data["status"])
        return cls(**data)

    from_dict = from_mapping


class EvaluatorFn(Protocol):
    def __call__(self, request: EvaluationRequest) -> Any: ...


class EvaluationContract:
    """Execute an evaluator under its declared budget and seed."""

    def __init__(self, evaluator_id: str, fn: EvaluatorFn, *, budget: EvaluationBudget | None = None) -> None:
        if not isinstance(evaluator_id, str) or not evaluator_id.strip():
            raise ValueError("evaluator_id is required")
        self.evaluator_id = evaluator_id
        self.fn = fn
        self.budget = budget or EvaluationBudget()

    def _validate_budget(self, request: EvaluationRequest) -> None:
        """A caller may narrow a contract budget, never widen it."""
        limits = (("max_seconds", request.budget.max_seconds, self.budget.max_seconds),
                  ("max_steps", request.budget.max_steps, self.budget.max_steps))
        for name, requested, declared in limits:
            if requested > declared:
                raise ValueError(f"request {name} exceeds declared contract budget")
        if self.budget.max_cost is not None:
            if request.budget.max_cost is None or request.budget.max_cost > self.budget.max_cost:
                raise ValueError("request max_cost exceeds declared contract budget")

    def _run(self, request: EvaluationRequest) -> EvaluationResult:
        if request.evaluator_id != self.evaluator_id:
            raise ValueError("request evaluator_id does not match contract")
        self._validate_budget(request)
        started = time.monotonic()
        try:
            value = self.fn(request)
            # Evaluators may return (output, steps), or a mapping carrying a
            # score/steps field.  The contract keeps the output opaque.
            steps = 1
            score = None
            output = value
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], int):
                output, steps = value
            elif isinstance(value, Mapping):
                steps = int(value.get("steps", 1))
                score = value.get("score")
            cost = None
            if isinstance(value, Mapping):
                raw_cost = value.get("cost", value.get("cost_usd",
                                  value.get("total_cost_usd", value.get("spent_cost"))))
                if raw_cost is not None:
                    if isinstance(raw_cost, bool) or not isinstance(raw_cost, (int, float)) or not math.isfinite(float(raw_cost)) or raw_cost < 0:
                        return EvaluationResult(EvaluationStatus.FAIL, request.evaluator_id,
                            request.task_id, request.seed, request.budget.digest, score=score,
                            output=output, steps=steps, elapsed_seconds=time.monotonic() - started,
                            error="invalid evaluation cost", smoke=request.smoke)
                    cost = float(raw_cost)
            elapsed = time.monotonic() - started
            if (elapsed > request.budget.max_seconds or steps > request.budget.max_steps
                    or (request.budget.max_cost is not None and cost is not None and cost > request.budget.max_cost)):
                return EvaluationResult(EvaluationStatus.TIMEOUT, request.evaluator_id,
                    request.task_id, request.seed, request.budget.digest, score=score,
                    output=output, steps=steps, elapsed_seconds=elapsed,
                    error="evaluation budget exceeded", smoke=request.smoke)
            return EvaluationResult(EvaluationStatus.PASS, request.evaluator_id,
                request.task_id, request.seed, request.budget.digest, score=score,
                output=output, steps=steps, elapsed_seconds=elapsed, smoke=request.smoke)
        except TimeoutError as exc:
            return EvaluationResult(EvaluationStatus.TIMEOUT, request.evaluator_id,
                request.task_id, request.seed, request.budget.digest,
                elapsed_seconds=time.monotonic() - started, error=str(exc), smoke=request.smoke)
        except Exception as exc:  # evaluator failures are data, not coordinator crashes
            return EvaluationResult(EvaluationStatus.FAIL, request.evaluator_id,
                request.task_id, request.seed, request.budget.digest,
                elapsed_seconds=time.monotonic() - started, error=str(exc), smoke=request.smoke)

    def smoke_test(self, request: EvaluationRequest | None = None) -> EvaluationResult:
        req = request or EvaluationRequest(self.evaluator_id, self.evaluator_id,
                                            input=None, seed=0, budget=self.budget, smoke=True)
        if not req.smoke:
            req = EvaluationRequest(req.task_id, req.evaluator_id, req.input, req.seed, req.budget, True)
        return self._run(req)

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        if request.smoke:
            return self._run(request)
        return self._run(request)


# Friendly aliases used by callers that describe this object as a runner.
Evaluator = EvaluationContract
EvaluatorInput = EvaluationRequest
EvaluatorOutput = EvaluationResult


def run_smoke_gate(contract: EvaluationContract, request: EvaluationRequest) -> EvaluationResult:
    """Run the mandatory preflight; callers must check ``passed`` before work."""
    return contract.smoke_test(request)


__all__ = ["EvaluationStatus", "EvaluationBudget", "EvaluationRequest", "EvaluationResult",
           "EvaluationContract", "Evaluator", "EvaluatorInput", "EvaluatorOutput", "run_smoke_gate"]
