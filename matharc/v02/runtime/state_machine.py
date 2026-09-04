"""Explicit lifecycle protocol for a persistent research run."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class LifecycleError(ValueError):
    pass


class RunState(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DRAINING = "DRAINING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class LifecycleReceipt:
    action: str
    previous_state: RunState
    resulting_state: RunState
    accepted: bool
    active_tasks: int
    terminated_tasks: tuple[str, ...] = ()
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action, "previous_state": self.previous_state.value,
                "resulting_state": self.resulting_state.value, "accepted": self.accepted,
                "active_tasks": self.active_tasks, "terminated_tasks": list(self.terminated_tasks), "reason": self.reason}


class RunStateMachine:
    """Small deterministic state machine; task admission is fail-closed."""

    def __init__(self, state: RunState | str = RunState.CREATED) -> None:
        self.state = state if isinstance(state, RunState) else RunState(state)
        self._active: set[str] = set()
        self._termination_results: dict[str, str] = {}

    @property
    def active_tasks(self) -> frozenset[str]: return frozenset(self._active)
    @property
    def status(self) -> RunState: return self.state
    @property
    def can_accept_tasks(self) -> bool: return self.state is RunState.RUNNING

    def start_task(self, task_id: str) -> None:
        if not self.can_accept_tasks: raise LifecycleError(f"run does not accept tasks in {self.state.value}")
        if not task_id: raise LifecycleError("task_id is required")
        self._active.add(task_id)

    accept_task = start_task

    def finish_task(self, task_id: str, *, result: str | None = None) -> str:
        if task_id not in self._active: raise LifecycleError(f"unknown active task: {task_id}")
        self._active.remove(task_id)
        result = result or self._termination_results.pop(task_id, "completed")
        if self.state is RunState.DRAINING and not self._active: self.state = RunState.STOPPED
        return result

    def transition(self, action: str, *, task_ids: list[str] | None = None, reason: str | None = None) -> LifecycleReceipt:
        action = action.lower().strip()
        previous = self.state
        terminated: tuple[str, ...] = ()
        if action in {"start", "run"}:
            if self.state not in {RunState.CREATED, RunState.PAUSED}: raise LifecycleError(f"cannot start from {self.state.value}")
            self.state = RunState.RUNNING
        elif action == "pause":
            if self.state is not RunState.RUNNING: raise LifecycleError(f"cannot pause from {self.state.value}")
            self.state = RunState.PAUSED
        elif action == "resume":
            if self.state is not RunState.PAUSED: raise LifecycleError(f"cannot resume from {self.state.value}")
            self.state = RunState.RUNNING
        elif action in {"stop", "drain"}:
            if self.state not in {RunState.RUNNING, RunState.PAUSED, RunState.CREATED, RunState.DRAINING}:
                raise LifecycleError(f"cannot stop from {self.state.value}")
            self.state = RunState.STOPPED if not self._active else RunState.DRAINING
            for task_id in self._active:
                self._termination_results[task_id] = "stopped"
        elif action == "cancel":
            if self.state in {RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED, RunState.STOPPED}:
                raise LifecycleError(f"cannot cancel from {self.state.value}")
            terminated = tuple(sorted(task_ids or self._active))
            self._active.difference_update(terminated)
            for task_id in terminated: self._termination_results[task_id] = "cancelled"
            self.state = RunState.CANCELLED
        elif action == "complete":
            if self._active: raise LifecycleError("cannot complete while tasks are active")
            if self.state not in {RunState.RUNNING, RunState.DRAINING, RunState.CREATED}: raise LifecycleError(f"cannot complete from {self.state.value}")
            self.state = RunState.COMPLETED
        elif action == "fail":
            terminated = tuple(sorted(self._active)); self._active.clear(); self.state = RunState.FAILED
        else: raise LifecycleError(f"unknown lifecycle action: {action}")
        return LifecycleReceipt(action, previous, self.state, True, len(self._active), terminated, reason)

    # Explicit verbs are part of the public protocol and make call sites
    # readable while retaining one transition implementation.
    def start(self, **kwargs: Any) -> LifecycleReceipt: return self.transition("start", **kwargs)
    def pause(self, **kwargs: Any) -> LifecycleReceipt: return self.transition("pause", **kwargs)
    def resume(self, **kwargs: Any) -> LifecycleReceipt: return self.transition("resume", **kwargs)
    def stop(self, **kwargs: Any) -> LifecycleReceipt: return self.transition("stop", **kwargs)
    def drain(self, **kwargs: Any) -> LifecycleReceipt: return self.transition("drain", **kwargs)
    def cancel(self, **kwargs: Any) -> LifecycleReceipt: return self.transition("cancel", **kwargs)


StateMachine = RunStateMachine
__all__ = ["LifecycleError", "LifecycleReceipt", "RunState", "RunStateMachine", "StateMachine"]
