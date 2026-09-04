"""Transport-neutral console runtime service."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from ..access_server import AccessAPI
from ..console_export import ConsoleLocalProjectionConfig
from .reconnect import ReconnectManager, ReconnectResult
from .view_model import ConsoleSnapshot, project_console_snapshot

try:
    from .contracts import ActionStatus, RuntimeActionReceipt, RunStatus
except ImportError:  # pragma: no cover - keeps this module importable in isolation
    ActionStatus = RuntimeActionReceipt = RunStatus = None  # type: ignore[assignment]
from .state_machine import RunState, RunStateMachine

ACTION_CLASSES: dict[str, str] = {
    **{a: "navigate" for a in ("camp", "demo", "enter", "go", "pick", "plane", "scroll", "topic", "toproof")},
    **{a: "wired-read" for a in ("review-bundle", "review-refresh")},
    "review-submit": "wired-write",
}
_ALL_ACTIONS = "cactor camp certroute cev cfg cnode compile conj cround csubj delta demo expl export fill filter fnode fold foldall funnel gate go knowl leadseed newtopic novroute ntadd ntcrit obs pick plan plane promote recheck review-bundle review-refresh review-submit role round rsn rt rub rubsel scroll sign signin startwatch stopwatch tamper tier tool topic toproof topup usetable ver".split()
ACTION_CLASSES.update({a: "local-ui-state" for a in _ALL_ACTIONS if a not in ACTION_CLASSES})
for action in ("cfg", "compile", "export", "ntadd", "plan", "promote", "sign", "signin", "startwatch", "stopwatch", "topup"):
    ACTION_CLASSES[action] = "simulated-write"
SIMULATED_WRITES = frozenset(a for a, kind in ACTION_CLASSES.items() if kind == "simulated-write")
RUNTIME_ACTIONS = frozenset({"start", "pause", "resume", "stop", "revalidate"})
FORBIDDEN_INPUT_FIELDS = frozenset({"command", "cwd", "environment", "env", "executable", "arguments", "args", "argv"})


class ConsoleRuntimeError(Exception):
    pass


class UnknownActionError(ConsoleRuntimeError, ValueError):
    pass


class PermissionDeniedError(ConsoleRuntimeError, PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class ActionResult:
    action: str
    status: str
    idempotency_key: str
    replayed: bool = False
    payload: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action, "status": self.status, "idempotency_key": self.idempotency_key, "replayed": self.replayed, "payload": dict(self.payload or {})}


class ConsoleRuntimeService:
    """Read-only snapshot service plus a strictly bounded action registry."""

    def __init__(self, workspace_root: str | Path, *, access_api: AccessAPI | None = None, local_projection_config: ConsoleLocalProjectionConfig | None = None, runtime_store: Any | None = None, action_handler: Callable[[str, Mapping[str, Any]], Mapping[str, Any]] | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.access_api = access_api
        self.local_projection_config = local_projection_config
        self.runtime_store = runtime_store
        self.action_handler = action_handler
        self._lock = threading.RLock()
        self._actions: dict[str, ActionResult] = {}
        self._snapshot: ConsoleSnapshot | None = None
        self._reconnect: ReconnectManager | None = None
        self._runs: dict[str, RunStateMachine] = {}
        self._runtime_receipts: dict[tuple[str, str], Any] = {}

    def snapshot(self, cookie_header: str = "") -> ConsoleSnapshot:
        self._authorize(cookie_header)
        with self._lock:
            snap = project_console_snapshot(self.workspace_root, local_projection_config=self.local_projection_config, runtime_store=self.runtime_store)
            self._snapshot = snap
            self._reconnect = ReconnectManager(snap.run_id, snap.sequence)
            return snap

    get_snapshot = snapshot

    def register_action(self, action: str, *, idempotency_key: str, payload: Mapping[str, Any] | None = None, cookie_header: str = "", data_boundary: str = "live", view: str | None = None) -> ActionResult:
        self._authorize(cookie_header, view=view)
        if action not in ACTION_CLASSES:
            raise UnknownActionError(f"unknown console action: {action}")
        if not isinstance(idempotency_key, str) or not idempotency_key.strip() or len(idempotency_key) > 200:
            raise ValueError("idempotency_key is required")
        if data_boundary not in {"live", "demo"}:
            raise ValueError("data_boundary must be live or demo")
        supplied = set(payload or {})
        if FORBIDDEN_INPUT_FIELDS.intersection(supplied):
            raise ValueError("command, cwd, environment, executable, and arguments are not accepted")
        if ACTION_CLASSES[action] == "simulated-write" and data_boundary == "live":
            raise PermissionDeniedError("simulated-write actions are unavailable for live data")
        with self._lock:
            prior = self._actions.get(idempotency_key)
            if prior is not None:
                if prior.action != action:
                    raise ValueError("idempotency key conflicts with another action")
                return ActionResult(prior.action, prior.status, prior.idempotency_key, True, prior.payload)
            result_payload = dict(self.action_handler(action, payload or {}) if self.action_handler else {})
            result = ActionResult(action, "accepted", idempotency_key, False, result_payload)
            self._actions[idempotency_key] = result
            return result

    dispatch = register_action

    def create_run(self, runtime_run_id: str, *, cookie_header: str = "", actor: str = "console", **metadata: Any) -> dict[str, Any]:
        """Register a bounded runtime identity; no process is spawned here."""
        self._authorize(cookie_header, require_runtime=True)
        if not isinstance(runtime_run_id, str) and hasattr(runtime_run_id, "runtime_run_id"):
            runtime_run_id = str(runtime_run_id.runtime_run_id)
        elif isinstance(runtime_run_id, Mapping) and runtime_run_id.get("runtime_run_id"):
            runtime_run_id = str(runtime_run_id["runtime_run_id"])
        if not isinstance(runtime_run_id, str) or not runtime_run_id.strip():
            raise ValueError("runtime_run_id is required")
        if FORBIDDEN_INPUT_FIELDS.intersection(metadata):
            raise ValueError("command, cwd, environment, executable, and arguments are not accepted")
        with self._lock:
            if runtime_run_id in self._runs:
                return {"runtime_run_id": runtime_run_id, "status": self._runs[runtime_run_id].status.value}
            self._runs[runtime_run_id] = RunStateMachine(RunState.CREATED)
            return {"runtime_run_id": runtime_run_id, "status": RunState.CREATED.value, "actor": actor}

    start_run = create_run
    post_run = create_run

    def runtime_action(self, runtime_run_id: str, action: str, *, action_id: str, actor: str = "console", cookie_header: str = "", payload: Mapping[str, Any] | None = None) -> Any:
        """Apply one of five lifecycle verbs and return a durable-shaped receipt."""
        self._authorize(cookie_header, require_runtime=True)
        action = str(action).strip().casefold()
        if action not in RUNTIME_ACTIONS:
            raise UnknownActionError(f"unknown runtime action: {action}")
        data = dict(payload or {})
        if FORBIDDEN_INPUT_FIELDS.intersection(data):
            raise ValueError("command, cwd, environment, executable, and arguments are not accepted")
        if not action_id or not isinstance(action_id, str):
            raise ValueError("action_id is required")
        key = (runtime_run_id, action_id)
        with self._lock:
            if key in self._runtime_receipts:
                return self._runtime_receipts[key]
            machine = self._runs.setdefault(runtime_run_id, RunStateMachine(RunState.CREATED))
            previous = machine.status.value
            try:
                if action == "revalidate":
                    resulting = machine.status.value
                else:
                    resulting = machine.transition(action).resulting_state.value
                status = ActionStatus.COMPLETED if ActionStatus is not None else "COMPLETED"
                prev_enum = RunStatus(previous) if RunStatus is not None else previous
                known_states = {item.value for item in RunStatus} if RunStatus is not None else set()
                next_enum = RunStatus(resulting) if RunStatus is not None and resulting in known_states else prev_enum
                reason = None if resulting in known_states else f"resulting_state:{resulting}"
                receipt = RuntimeActionReceipt(action_id, action, actor, runtime_run_id, status, prev_enum, next_enum, reason) if RuntimeActionReceipt is not None else ActionResult(action, "completed", action_id, False, {"runtime_run_id": runtime_run_id, "previous_state": previous, "resulting_state": resulting})
            except Exception as exc:
                status = ActionStatus.FAILED if ActionStatus is not None else "FAILED"
                prev_enum = RunStatus(previous) if RunStatus is not None else previous
                receipt = RuntimeActionReceipt(action_id, action, actor, runtime_run_id, status, prev_enum, prev_enum, str(exc)) if RuntimeActionReceipt is not None else ActionResult(action, "failed", action_id, False, {"runtime_run_id": runtime_run_id, "reason": str(exc)})
            self._runtime_receipts[key] = receipt
            return receipt

    post_action = runtime_action
    run_action = runtime_action
    action = runtime_action

    def reconnect(self, *, cookie_header: str = "", run_id: str, after: int, events: list[Mapping[str, Any]]) -> ReconnectResult:
        self._authorize(cookie_header)
        with self._lock:
            if self._reconnect is None or self._reconnect.run_id != run_id:
                snap = self.snapshot(cookie_header)
                if snap.run_id != run_id:
                    return ReconnectResult(snap.run_id, snap.sequence, (), True, "run_id_changed")
            assert self._reconnect is not None
            return self._reconnect.reconnect(run_id=run_id, after=after, events=events)

    def _authorize(self, cookie_header: str, *, view: str | None = None, require_runtime: bool = False) -> None:
        if self.access_api is None:
            return
        try:
            session = self.access_api.authenticate(cookie_header)
        except Exception as exc:
            raise PermissionDeniedError("valid invitation session required") from exc
        if require_runtime and session.topic_scopes and "*" not in session.topic_scopes:
            allowed = {str(item).casefold() for item in session.topic_scopes}
            if not ({"runtime", "runtime_actions", "operations"} & allowed):
                raise PermissionDeniedError("session has no runtime operation permission")
        if view is not None and session.topic_scopes and "*" not in session.topic_scopes and view not in session.topic_scopes:
            raise PermissionDeniedError("session is not scoped to this console view")


__all__ = ["ACTION_CLASSES", "SIMULATED_WRITES", "ActionResult", "ConsoleRuntimeService", "ConsoleRuntimeError", "UnknownActionError", "PermissionDeniedError"]
