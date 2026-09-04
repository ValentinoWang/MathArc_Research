"""Codex CLI adapter behind the MathArc backend contract."""
from __future__ import annotations

import time
from typing import Any, Mapping

from ....codex_runtime import CodexConfig, CodexRunner, CodexRuntimeError
from ...schema import digest_json
from ..contracts import ExecutionStatus, WorkerExecutionResult
from .base import BackendRequest, as_request, result_for


class CodexBackend:
    name = "codex"

    def __init__(self, runner: Any | None = None, *, config: CodexConfig | None = None,
                 role: str = "researcher", model: str | None = None) -> None:
        self.runner = runner or CodexRunner(config or CodexConfig.from_env())
        self.role = role
        self.model = model

    def execute(self, request: BackendRequest | Mapping[str, Any]) -> WorkerExecutionResult:
        req = as_request(request)
        started = time.monotonic()
        if req.cancel_event is not None and getattr(req.cancel_event, "is_set", lambda: False)():
            return result_for(req, ExecutionStatus.CANCELLED, failure_class="CANCELLED", error="cancelled",
                              elapsed_seconds=time.monotonic() - started)
        prompt = req.payload if isinstance(req.payload, str) else str((req.payload or {}).get("message", req.payload or ""))
        try:
            structured: dict[str, Any] | None = None
            # CodexRunner exposes a streaming API; test doubles may expose
            # run_turn or execute instead.  All forms remain read-only here.
            if hasattr(self.runner, "stream_turn"):
                for event in self.runner.stream_turn(prompt, role=self.role, model=self.model,
                    timeout_seconds=req.timeout_seconds):
                    if getattr(event, "type", None) == "matharc.result":
                        value = getattr(event, "payload", {}).get("result")
                        if isinstance(value, Mapping):
                            structured = dict(value)
            elif hasattr(self.runner, "run_turn"):
                value = self.runner.run_turn(prompt, role=self.role, model=self.model,
                                             timeout_seconds=req.timeout_seconds)
                structured = dict(getattr(value, "final_response", None) or getattr(value, "structured_output", None) or value)
            else:
                value = self.runner.execute(req)
                structured = dict(value) if isinstance(value, Mapping) else {"output": value}
            if structured is None:
                raise CodexRuntimeError("Codex completed without a structured result")
            digest = digest_json(structured)
            return result_for(req, ExecutionStatus.SUCCEEDED, result_digest=digest,
                              candidate_ids=(f"candidate-{digest[:16]}",), elapsed_seconds=time.monotonic() - started)
        except TimeoutError as exc:
            return result_for(req, ExecutionStatus.TIMED_OUT, failure_class="TIMEOUT", error=str(exc),
                              elapsed_seconds=time.monotonic() - started)
        except CodexRuntimeError as exc:
            message = str(exc)
            status = ExecutionStatus.TIMED_OUT if "exceeded" in message.lower() or "timeout" in message.lower() else ExecutionStatus.FAILED
            return result_for(req, status, failure_class="TIMEOUT" if status is ExecutionStatus.TIMED_OUT else "CODEX_ERROR",
                              error=message, elapsed_seconds=time.monotonic() - started)
        except Exception as exc:
            return result_for(req, ExecutionStatus.FAILED, failure_class="BACKEND_ERROR", error=str(exc),
                              elapsed_seconds=time.monotonic() - started)


__all__ = ["CodexBackend"]
