"""Allowlisted local exact-tool backend.

The adapter accepts a registered callable/registry object.  It does not
accept arbitrary shell text, working directories, or environment overrides.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Mapping

from ...schema import digest_json
from ..contracts import ExecutionStatus, WorkerExecutionResult
from .base import BackendRequest, BackendExecutionError, as_request, result_for


class LocalExactToolBackend:
    name = "local-exact-tool"

    def __init__(self, tool: Callable[..., Any] | Any | None = None) -> None:
        self.tool = tool

    def execute(self, request: BackendRequest | Mapping[str, Any]) -> WorkerExecutionResult:
        req = as_request(request)
        started = time.monotonic()
        if req.cancel_event is not None and getattr(req.cancel_event, "is_set", lambda: False)():
            return result_for(req, ExecutionStatus.CANCELLED, failure_class="CANCELLED", error="cancelled",
                              elapsed_seconds=time.monotonic() - started)
        try:
            if self.tool is None:
                raise BackendExecutionError("no exact tool registered", failure_class="TOOL_UNAVAILABLE")
            payload = req.payload
            if callable(self.tool):
                try:
                    output = self.tool(payload, seed=req.seed)
                except TypeError:
                    output = self.tool(payload)
            elif hasattr(self.tool, "execute"):
                if isinstance(payload, Mapping) and ("template_id" in payload or "tool" in payload):
                    template_id = str(payload.get("template_id", payload.get("tool")))
                    arguments = payload.get("arguments", payload.get("args", {}))
                    output = self.tool.execute(template_id,
                                               claim_id=str(payload.get("claim_id", req.task_id)),
                                               arguments=arguments if isinstance(arguments, Mapping) else {})
                else:
                    output = self.tool.execute(payload)
            elif hasattr(self.tool, "evaluate"):
                output = self.tool.evaluate(payload)
            else:
                raise BackendExecutionError("exact tool is not callable", failure_class="TOOL_UNAVAILABLE")
            if hasattr(output, "tool_call"):
                output = {"tool_call": output.tool_call.to_dict() if hasattr(output.tool_call, "to_dict") else str(output.tool_call),
                          "evidence": output.evidence.to_dict() if getattr(output, "evidence", None) is not None and hasattr(output.evidence, "to_dict") else None}
            if isinstance(output, Mapping) and output.get("status") in {"FAIL", "ERROR", False}:
                raise BackendExecutionError(str(output.get("error", "exact tool failed")), failure_class="EXACT_TOOL_FAILURE")
            digest = digest_json(output)
            return result_for(req, ExecutionStatus.SUCCEEDED, result_digest=digest,
                              candidate_ids=(f"candidate-{digest[:16]}",), elapsed_seconds=time.monotonic() - started)
        except BackendExecutionError as exc:
            return result_for(req, ExecutionStatus.FAILED, failure_class=exc.failure_class,
                              error=str(exc), elapsed_seconds=time.monotonic() - started)
        except TimeoutError as exc:
            return result_for(req, ExecutionStatus.TIMED_OUT, failure_class="TIMEOUT", error=str(exc),
                              elapsed_seconds=time.monotonic() - started)
        except Exception as exc:
            return result_for(req, ExecutionStatus.FAILED, failure_class="EXACT_TOOL_ERROR", error=str(exc),
                              elapsed_seconds=time.monotonic() - started)


__all__ = ["LocalExactToolBackend"]
