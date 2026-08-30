"""Model-backed proposal workers for the v0.2 research loop.

LLMProposalWorker implements the same ProposalWorker protocol as
SubprocessProposalWorker/StaticProposalWorker (workers.py), so it drops into
ResearchSession or ResearchCampaign unchanged.  Today it is backed by
ClaudeCodeRunner (the Claude Code CLI, launched with every mutating tool
disallowed); the class itself only depends on a small ModelRunner protocol so
a future Codex-CLI-backed or raw-API-backed runner can implement the same
seam without touching this module.

Like every other worker, a call here can never raise out of execute(): any
failure is recorded as a ToolCallRecord with status=ERROR and proposal=None,
exactly like SubprocessProposalWorker's own error handling, so one worker's
failure never crashes the rest of a round.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from .claude_code_runtime import ClaudeCodeRunner, ClaudeCodeRuntimeError
from .orchestrator import ResearchRoundPlan
from .prompting import PROPOSAL_OUTPUT_SCHEMA, build_worker_prompt
from .schema import ToolCallRecord, ToolStatus, canonical_json, digest_json, utc_now
from .workers import WorkerExecution


class ModelTurnResult(Protocol):
    """The subset of a model-runner turn result LLMProposalWorker consumes."""

    call_id: str
    command: list[str]
    prompt_sha256: str
    started_at: str
    ended_at: str
    structured_output: dict[str, Any]
    raw_result_text: str
    usage: dict[str, Any]
    cost_usd: float | None
    stderr: str


class ModelRunner(Protocol):
    def run_turn(
        self,
        prompt: str,
        *,
        role: str,
        json_schema: Mapping[str, Any],
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> ModelTurnResult: ...


@dataclass(slots=True)
class ModelWorkerRoutingEntry:
    provider: str
    model: str | None = None


def load_model_routing(path: str | Path) -> dict[str, ModelWorkerRoutingEntry]:
    """Load a role -> {provider, model} routing table from a JSON file.

    Kept as JSON rather than TOML so the loader has zero dependency on the
    Python version (tomllib is 3.11+ only; this project supports 3.10).
    """

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("model routing file root must be an object")
    routing: dict[str, ModelWorkerRoutingEntry] = {}
    for role, spec in payload.items():
        if not isinstance(spec, Mapping) or "provider" not in spec:
            raise ValueError(f"model routing entry for {role!r} needs a provider")
        routing[str(role)] = ModelWorkerRoutingEntry(
            provider=str(spec["provider"]),
            model=(str(spec["model"]) if spec.get("model") is not None else None),
        )
    return routing


class LLMProposalWorker:
    """A ProposalWorker backed by a real model runner (default: Claude Code CLI).

    The runner receives only the bounded trace_view for the round's focus
    claim (see prompting.build_trace_view) -- never the whole trace -- so
    prompt size stays bounded as a research trace grows.
    """

    def __init__(
        self,
        role: str,
        *,
        runner: ModelRunner | None = None,
        model: str | None = None,
        json_schema: Mapping[str, Any] | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.role = role
        self.runner: ModelRunner = runner or ClaudeCodeRunner()
        self.model = model
        self.json_schema = json_schema or PROPOSAL_OUTPUT_SCHEMA
        self.timeout_seconds = timeout_seconds

    def execute(
        self,
        plan: ResearchRoundPlan,
        trace_view: Mapping[str, Any],
    ) -> WorkerExecution:
        started = utc_now()
        try:
            prompt = build_worker_prompt(role=self.role, trace_view=trace_view, plan=plan)
            input_digest = digest_json(prompt)
            result = self.runner.run_turn(
                prompt,
                role=self.role,
                json_schema=self.json_schema,
                model=self.model,
                timeout_seconds=(
                    int(self.timeout_seconds) if self.timeout_seconds is not None else None
                ),
            )
        except (ClaudeCodeRuntimeError, ValueError) as exc:
            ended = utc_now()
            input_digest = digest_json({"role": self.role, "error": "prompt or turn failed"})
            tool_call = ToolCallRecord(
                call_id=f"LLM-{self.role.upper()}-ERROR",
                tool=f"llm-worker:{self.role}",
                purpose=f"Generate a proposal for {plan.focus_claim_id}; no proof authority.",
                status=ToolStatus.ERROR,
                input_digest_sha256=input_digest,
                output_digest_sha256="",
                linked_claim_ids=(plan.focus_claim_id,),
                independence_group=f"llm-worker:{self.role}",
                replay_command="",
                started_at=started,
                ended_at=ended,
                expected_discriminator="valid structured proposal JSON with no proof promotion",
            )
            return WorkerExecution(
                role=self.role,
                proposal=None,
                tool_call=tool_call,
                raw_stdout="",
                raw_stderr=str(exc),
            )
        output_text = canonical_json(result.structured_output)
        # The command already documents the exact reproduction path (model,
        # schema, disallowed tools); model output is not guaranteed
        # byte-identical between calls the way an exact tool's is, and the
        # command records that intent rather than promising determinism.
        replay_command = " ".join(json.dumps(item) for item in result.command)
        model_usage: dict[str, Any] = {
            "provider": "claude-code",
            "model": self.model,
            "input_tokens": int(result.usage.get("input_tokens", 0) or 0),
            "output_tokens": int(result.usage.get("output_tokens", 0) or 0),
            "cost_usd": result.cost_usd,
        }
        tool_call = ToolCallRecord(
            call_id=result.call_id,
            tool=f"llm-worker:{self.role}",
            purpose=f"Generate a proposal for {plan.focus_claim_id}; no proof authority.",
            status=ToolStatus.PASS,
            input_digest_sha256=result.prompt_sha256,
            output_digest_sha256=digest_json(output_text),
            linked_claim_ids=(plan.focus_claim_id,),
            independence_group=f"llm-worker:claude-code:{self.role}",
            replay_command=replay_command,
            started_at=result.started_at,
            ended_at=result.ended_at,
            expected_discriminator="valid structured proposal JSON with no proof promotion",
        )
        return WorkerExecution(
            role=self.role,
            proposal=dict(result.structured_output),
            tool_call=tool_call,
            raw_stdout=result.raw_result_text,
            raw_stderr=result.stderr,
            model_usage=model_usage,
        )
