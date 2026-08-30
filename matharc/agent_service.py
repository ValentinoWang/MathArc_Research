from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Iterator

from .codex_runtime import (
    PUBLIC_AGENT_ROLES,
    CodexConfig,
    CodexEvent,
    CodexRunner,
    CodexRuntimeError,
    CodexSessionStore,
    build_agent_prompt,
    codex_status,
    result_digest,
    utc_now,
)
from .metrics import compute_metrics
from .models import ResearchRun


class AgentRequestError(ValueError):
    """Raised when the browser submits an invalid or unsafe agent request."""


class CodexAgentService:
    """Connect a frozen MathArc run to Codex research workers.

    Codex output is stored as proposal evidence. This service never promotes a
    mathematical claim; only ``ResearchEngine`` and verifier gates can do that.
    """

    def __init__(
        self,
        run: ResearchRun,
        *,
        workspace: str | Path | None = None,
        session_root: str | Path | None = None,
        config: CodexConfig | None = None,
    ) -> None:
        self.research_run = run
        selected_workspace = Path(
            workspace or os.environ.get("MATHARC_CODEX_WORKSPACE") or Path.cwd()
        ).resolve()
        self.config = config or CodexConfig.from_env(selected_workspace)
        self.runner = CodexRunner(self.config)
        self.store = CodexSessionStore(
            session_root
            or os.environ.get("MATHARC_CODEX_SESSION_DIR")
            or selected_workspace / ".matharc" / "codex-sessions"
        )

    def status(self) -> dict[str, Any]:
        value = codex_status(self.config)
        value.update(
            {
                "session_count": len(self.store.list_sessions(limit=200)),
                "run_id": self.research_run.run_id,
                "release_state": self.research_run.release_state,
            }
        )
        return value

    def roles(self) -> dict[str, Any]:
        return PUBLIC_AGENT_ROLES

    def validate_request(self, request: dict[str, Any]) -> dict[str, Any]:
        role = str(request.get("role", "strategist"))
        if role not in PUBLIC_AGENT_ROLES:
            raise AgentRequestError(f"unknown role: {role}")
        message = str(request.get("message", "")).strip()
        if not message:
            raise AgentRequestError("message is required")
        if len(message) > 48_000:
            raise AgentRequestError("message exceeds 48,000 characters")
        sandbox = str(request.get("sandbox") or self.config.sandbox)
        if sandbox not in {"read-only", "workspace-write"}:
            raise AgentRequestError("sandbox must be read-only or workspace-write")
        model_raw = request.get("model")
        thread_raw = request.get("thread_id")
        timeout_raw = request.get("timeout_seconds")
        timeout = int(timeout_raw) if timeout_raw is not None else self.config.timeout_seconds
        return {
            "role": role,
            "message": message,
            "sandbox": sandbox,
            "model": str(model_raw).strip() if model_raw else None,
            "thread_id": str(thread_raw).strip() if thread_raw else None,
            "timeout_seconds": max(30, min(timeout, 3600)),
        }

    def stream(self, request: dict[str, Any]) -> Iterator[CodexEvent]:
        selected = self.validate_request(request)
        prompt = build_agent_prompt(
            self.research_run,
            selected["role"],
            selected["message"],
            metrics=compute_metrics(self.research_run),
        )
        yield CodexEvent(
            sequence=0,
            type="matharc.turn.accepted",
            timestamp=utc_now(),
            payload={
                "turn_id": f"turn-{uuid.uuid4().hex[:12]}",
                "role": selected["role"],
                "sandbox": selected["sandbox"],
                "model": selected["model"] or self.config.model,
                "acceptance_authority": False,
                "message": "Codex is generating a proposal; claim promotion remains verifier-controlled.",
            },
        )
        result_payload: dict[str, Any] | None = None
        for event in self.runner.stream_turn(
            prompt,
            role=selected["role"],
            thread_id=selected["thread_id"],
            model=selected["model"],
            sandbox=selected["sandbox"],
            timeout_seconds=selected["timeout_seconds"],
        ):
            if event.type == "matharc.result":
                value = event.payload.get("result")
                if isinstance(value, dict):
                    result_payload = value
                    result_payload["run_id"] = self.research_run.run_id
                    result_payload["research_release_state"] = self.research_run.release_state
                    result_payload["result_sha256"] = result_digest(result_payload)
                    self.store.write_result(result_payload)
                    event.payload["result"] = result_payload
            yield event
        if result_payload is None:
            raise CodexRuntimeError("Codex stream ended without a MathArc result event")

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] | None = None
        events: list[dict[str, Any]] = []
        for event in self.stream(request):
            events.append(event.to_dict())
            if event.type == "matharc.result" and isinstance(event.payload.get("result"), dict):
                result = event.payload["result"]
        if result is None:
            raise CodexRuntimeError("Codex turn produced no structured result")
        return {"result": result, "events": events}

    def list_sessions(self, limit: int = 30) -> list[dict[str, Any]]:
        return self.store.list_sessions(limit=limit)

    def load_session(self, session_id: str) -> dict[str, Any]:
        return self.store.load_session(session_id)


def sse_encode(event: CodexEvent) -> bytes:
    event_name = event.type.replace(".", "_")
    data = json.dumps(event.to_dict(), ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_name}\ndata: {data}\n\n".encode("utf-8")
