"""Claude Code CLI adapter for the v0.2 research loop.

Mirrors matharc/codex_runtime.py's architecture (the v0.1 OpenAI Codex CLI
adapter) but targets the `claude` CLI (Claude Code) in non-interactive
--print mode with --json-schema structured-output validation instead of
Codex's --output-schema/--output-last-message file pair.

Claude Code is a worker like Codex: its output is a structured proposal that
must pass through ResearchOrchestrator.accept_agent_proposal, and it can
never mark a claim PROVED.  The subprocess is launched with every mutating
and networked tool disallowed (--disallowedTools), no MCP servers
(--strict-mcp-config) and no project/user settings (--setting-sources ""),
so a worker turn is a bounded text completion against the prompt it is
given -- it cannot read or write files, run commands, or reach the network
on its own.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .prompting import RESEARCH_RULES_MARKER, ROLE_DEFINITIONS, build_worker_prompt
from .schema import utc_now


class ClaudeCodeRuntimeError(RuntimeError):
    """Raised when the Claude Code CLI or its structured-output contract fails."""


_MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,120}$")

# A worker turn must never be able to read, write, execute, or reach the
# network on its own -- it receives the entire bounded state it needs as
# text in the prompt and returns a schema-validated proposal.  This is a
# single space-separated CLI value, matching how --disallowedTools parses
# its argument (confirmed against the installed Claude Code CLI).
_DEFAULT_DISALLOWED_TOOLS = (
    "Bash Read Write Edit NotebookEdit Glob Grep WebFetch WebSearch "
    "Task SendUserMessage KillShell BashOutput"
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class ClaudeCodeConfig:
    executable: str = "claude"
    model: str | None = None
    timeout_seconds: int = 600
    max_output_chars: int = 200_000
    disallowed_tools: str = _DEFAULT_DISALLOWED_TOOLS
    extra_args: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> "ClaudeCodeConfig":
        return cls(
            executable=os.environ.get("MATHARC_CLAUDE_EXECUTABLE", "claude"),
            model=os.environ.get("MATHARC_CLAUDE_MODEL") or None,
            timeout_seconds=max(30, int(os.environ.get("MATHARC_CLAUDE_TIMEOUT", "600"))),
        )

    def validate(self) -> None:
        if self.model and not _MODEL_RE.fullmatch(self.model):
            raise ValueError("model contains unsupported characters")


def claude_code_status(config: ClaudeCodeConfig | None = None) -> dict[str, Any]:
    config = config or ClaudeCodeConfig.from_env()
    executable = shutil.which(config.executable)
    if executable is None and Path(config.executable).is_file():
        executable = str(Path(config.executable).resolve())
    return {
        "available": executable is not None,
        "executable": executable or config.executable,
        "default_model": config.model,
        "disallowed_tools": config.disallowed_tools,
        "roles": {key: value["label"] for key, value in ROLE_DEFINITIONS.items()},
        "acceptance_authority": False,
        "message": (
            "Claude Code CLI is available. Its output remains proposal evidence "
            "until MathArc gates accept it."
            if executable
            else "Claude Code CLI ('claude') is not installed or not on PATH."
        ),
    }


@dataclass(slots=True)
class ClaudeCodeTurnResult:
    call_id: str
    role: str
    prompt_sha256: str
    command: list[str]
    started_at: str
    ended_at: str
    return_code: int
    session_id: str | None
    structured_output: dict[str, Any]
    raw_result_text: str
    usage: dict[str, Any] = field(default_factory=dict)
    cost_usd: float | None = None
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "role": self.role,
            "prompt_sha256": self.prompt_sha256,
            "command": self.command,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "return_code": self.return_code,
            "session_id": self.session_id,
            "structured_output": self.structured_output,
            "raw_result_text": self.raw_result_text,
            "usage": self.usage,
            "cost_usd": self.cost_usd,
            "stderr": self.stderr,
        }


class ClaudeCodeRunner:
    """Non-interactive Claude Code CLI adapter with schema-forced output.

    Unlike matharc/codex_runtime.py's CodexRunner, this does not stream a
    JSONL event feed -- Claude Code's --output-format json returns one
    result object once the turn completes, which is sufficient for a
    proposal-only worker.  A live event stream (matching Codex's richer
    dashboard integration) is deferred future work, not attempted here.
    """

    def __init__(self, config: ClaudeCodeConfig | None = None) -> None:
        self.config = config or ClaudeCodeConfig.from_env()
        self.config.validate()

    def build_command(
        self,
        *,
        json_schema: Mapping[str, Any],
        model: str | None = None,
    ) -> list[str]:
        selected_model = model or self.config.model
        if selected_model and not _MODEL_RE.fullmatch(selected_model):
            raise ValueError("model contains unsupported characters")
        command = [
            self.config.executable,
            "--print",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(json_schema, ensure_ascii=False, separators=(",", ":")),
            "--strict-mcp-config",
            "--setting-sources",
            "",
        ]
        if self.config.disallowed_tools:
            command.extend(["--disallowedTools", self.config.disallowed_tools])
        if selected_model:
            command.extend(["--model", selected_model])
        command.extend(self.config.extra_args)
        return command

    def run_turn(
        self,
        prompt: str,
        *,
        role: str,
        json_schema: Mapping[str, Any],
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> ClaudeCodeTurnResult:
        if role not in ROLE_DEFINITIONS:
            raise ValueError(f"unknown role: {role}")
        if RESEARCH_RULES_MARKER not in prompt:
            # A worker must never receive a turn without the research rules,
            # even when the caller bypasses build_worker_prompt.
            prompt = build_worker_prompt(role=role, trace_view={}, user_message=prompt)
        timeout = timeout_seconds or self.config.timeout_seconds
        call_id = f"CLAUDE-{role.upper()}-{uuid.uuid4().hex[:12]}"
        command = self.build_command(json_schema=json_schema, model=model)
        executable = shutil.which(command[0])
        if executable is None and not Path(command[0]).is_file():
            raise ClaudeCodeRuntimeError(
                f"Claude Code executable not found: {command[0]}. "
                "Install @anthropic-ai/claude-code or set MATHARC_CLAUDE_EXECUTABLE."
            )
        started_at = utc_now()
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ClaudeCodeRuntimeError(f"Claude Code turn exceeded {timeout} seconds") from exc
        ended_at = utc_now()
        if completed.returncode != 0:
            raise ClaudeCodeRuntimeError(
                f"Claude Code exited with code {completed.returncode}: {completed.stderr[-4000:]}"
            )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ClaudeCodeRuntimeError(
                f"Claude Code emitted invalid JSON: {completed.stdout[:2000]}"
            ) from exc
        if not isinstance(payload, dict):
            raise ClaudeCodeRuntimeError("Claude Code result root must be an object")
        if payload.get("is_error"):
            raise ClaudeCodeRuntimeError(f"Claude Code reported an error result: {payload}")
        structured = self._extract_structured_output(payload)
        if structured is None:
            raise ClaudeCodeRuntimeError(
                "Claude Code completed without a schema-validated structured result"
            )
        cost = payload.get("total_cost_usd")
        return ClaudeCodeTurnResult(
            call_id=call_id,
            role=role,
            prompt_sha256=_sha256_text(prompt),
            command=command,
            started_at=started_at,
            ended_at=ended_at,
            return_code=completed.returncode,
            session_id=(
                str(payload["session_id"]) if payload.get("session_id") is not None else None
            ),
            structured_output=structured,
            raw_result_text=completed.stdout[: self.config.max_output_chars],
            usage=dict(payload.get("usage") or {}),
            cost_usd=float(cost) if isinstance(cost, (int, float)) else None,
            stderr=completed.stderr[-4000:],
        )

    @staticmethod
    def _extract_structured_output(payload: Mapping[str, Any]) -> dict[str, Any] | None:
        structured = payload.get("structured_output")
        if isinstance(structured, dict):
            return structured
        raw_result = payload.get("result")
        if isinstance(raw_result, dict):
            return raw_result
        if isinstance(raw_result, str):
            try:
                parsed = json.loads(raw_result)
            except json.JSONDecodeError:
                return None
            return parsed if isinstance(parsed, dict) else None
        return None
