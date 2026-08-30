from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .orchestrator import ResearchRoundPlan
from .schema import ToolCallRecord, ToolStatus, canonical_json, utc_now


def _stream_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


@dataclass(slots=True)
class WorkerExecution:
    role: str
    proposal: dict[str, Any] | None
    tool_call: ToolCallRecord
    raw_stdout: str
    raw_stderr: str
    # Populated only by model-backed workers (model_workers.LLMProposalWorker);
    # None for subprocess/static workers.  Sidecar metering, not part of the
    # persisted trace schema -- a future UsageRecord in schema.py would make
    # it first-class and auditable rather than advisory.
    model_usage: dict[str, Any] | None = None


class ProposalWorker(Protocol):
    role: str

    def execute(
        self,
        plan: ResearchRoundPlan,
        trace_view: Mapping[str, Any],
    ) -> WorkerExecution: ...


def _sha(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _environment_digest(command: Sequence[str], cwd: Path) -> str:
    payload = {
        "python": sys.version,
        "platform": sys.platform,
        "command": list(command),
        "cwd": str(cwd.resolve()),
        "path": os.environ.get("PATH", ""),
    }
    return _sha(canonical_json(payload))


class SubprocessProposalWorker:
    """Run an external research worker through a bounded JSON protocol.

    Input is written to stdin.  Output must be one JSON object.  The adapter
    captures complete digests and a replay command, but its output is still a
    proposal.  ResearchSession passes it through ResearchOrchestrator rather
    than changing claim status directly.
    """

    def __init__(
        self,
        *,
        role: str,
        command: Sequence[str],
        cwd: str | Path,
        timeout_seconds: float = 120.0,
        max_output_bytes: int = 2_000_000,
        extra_env: Mapping[str, str] | None = None,
    ) -> None:
        if not command:
            raise ValueError("worker command cannot be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
        self.role = role
        self.command = tuple(str(item) for item in command)
        self.cwd = Path(cwd)
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.extra_env = dict(extra_env or {})

    def execute(
        self,
        plan: ResearchRoundPlan,
        trace_view: Mapping[str, Any],
    ) -> WorkerExecution:
        request = {
            "schema_version": "2.0",
            "role": self.role,
            "round_plan": plan.to_dict(),
            "trace_view": dict(trace_view),
            "output_contract": {
                "proposal_only": True,
                "required_public_reasoning": [
                    "objective",
                    "premises",
                    "proposed_move",
                    "observation",
                    "falsification",
                    "decision",
                ],
                "forbidden_fields": [
                    "chain_of_thought",
                    "private_chain_of_thought",
                    "scratchpad",
                    "private_reasoning",
                ],
            },
        }
        stdin_text = canonical_json(request)
        started = utc_now()
        environment = os.environ.copy()
        environment.update(self.extra_env)
        call_id = f"WORKER-{self.role.upper()}-{uuid.uuid4().hex[:12]}"
        status = ToolStatus.ERROR
        exit_code: int | None = None
        stdout = ""
        stderr = ""
        proposal: dict[str, Any] | None = None
        try:
            completed = subprocess.run(
                list(self.command),
                input=stdin_text,
                text=True,
                capture_output=True,
                cwd=self.cwd,
                env=environment,
                timeout=self.timeout_seconds,
                check=False,
            )
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            if len(stdout.encode("utf-8")) > self.max_output_bytes:
                stderr += "\nMathArc adapter rejected stdout larger than max_output_bytes."
                status = ToolStatus.FAIL
            elif completed.returncode != 0:
                status = ToolStatus.FAIL
            else:
                parsed = json.loads(stdout)
                if not isinstance(parsed, dict):
                    raise ValueError("worker JSON root must be an object")
                proposal = parsed
                status = ToolStatus.PASS
        except subprocess.TimeoutExpired as exc:
            stdout = _stream_text(exc.stdout)
            stderr = _stream_text(exc.stderr) + "\nworker timeout"
            status = ToolStatus.ERROR
        except Exception as exc:
            stderr += f"\n{type(exc).__name__}: {exc}"
            status = ToolStatus.ERROR

        ended = utc_now()
        replay_command = " ".join(json.dumps(item) for item in self.command)
        tool_call = ToolCallRecord(
            call_id=call_id,
            tool=f"subprocess-worker:{self.role}",
            purpose=f"Generate a proposal for {plan.focus_claim_id}; no proof authority.",
            status=status,
            input_digest_sha256=_sha(stdin_text),
            output_digest_sha256=_sha(stdout),
            linked_claim_ids=(plan.focus_claim_id,),
            independence_group=f"worker:{self.role}:{_sha(replay_command)[:12]}",
            replay_command=replay_command,
            started_at=started,
            ended_at=ended,
            exit_code=exit_code,
            environment_digest_sha256=_environment_digest(self.command, self.cwd),
            expected_discriminator="valid structured proposal JSON with no proof promotion",
        )
        return WorkerExecution(
            role=self.role,
            proposal=proposal,
            tool_call=tool_call,
            raw_stdout=stdout,
            raw_stderr=stderr,
        )


class StaticProposalWorker:
    """Deterministic worker for demos and adapter contract tests."""

    def __init__(self, role: str, proposal: Mapping[str, Any]) -> None:
        self.role = role
        self.proposal = dict(proposal)

    def execute(
        self,
        plan: ResearchRoundPlan,
        trace_view: Mapping[str, Any],
    ) -> WorkerExecution:
        request_digest = _sha(canonical_json({"plan": plan.to_dict(), "trace": trace_view}))
        output = canonical_json(self.proposal)
        timestamp = utc_now()
        call = ToolCallRecord(
            call_id=f"STATIC-{self.role.upper()}-{uuid.uuid4().hex[:12]}",
            tool=f"static-worker:{self.role}",
            purpose=f"Deterministic proposal for {plan.focus_claim_id}.",
            status=ToolStatus.PASS,
            input_digest_sha256=request_digest,
            output_digest_sha256=_sha(output),
            linked_claim_ids=(plan.focus_claim_id,),
            independence_group=f"static:{self.role}",
            replay_command="python -m unittest tests.test_v02_workers",
            started_at=timestamp,
            ended_at=timestamp,
            exit_code=0,
            environment_digest_sha256=_sha("static-worker-v0.2"),
            expected_discriminator="proposal remains below the proof-promotion boundary",
        )
        return WorkerExecution(self.role, dict(self.proposal), call, output, "")
