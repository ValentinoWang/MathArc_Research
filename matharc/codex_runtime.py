from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, cast

from .hashing import digest_json, digest_text
from .metrics import compute_metrics
from .models import ResearchRun


class CodexRuntimeError(RuntimeError):
    """Raised when Codex or its structured-output contract fails."""


PUBLIC_AGENT_ROLES: dict[str, dict[str, Any]] = {
    "strategist": {
        "label": "研究策略师",
        "mission": "Identify the next load-bearing obligation, open mechanism-distinct routes, and state a cheap falsification test.",
        "accent": "violet",
        "quick_prompts": [
            "给出当前最关键的下一证明义务，并解释它为什么是承重节点。",
            "审计现有路线是否只是换措辞，而没有真正的机制差异。",
            "设计三条互相独立、可被快速否证的推进路线。",
        ],
    },
    "prover": {
        "label": "证明构造器",
        "mission": "Construct one atomic lemma, derivation, certificate, or exact reduction; never promote from plausibility or finite testing.",
        "accent": "emerald",
        "quick_prompts": [
            "基于当前证明 DAG，尝试关闭一个最小但承重的引理。",
            "把下一步推导写成可交给独立检查器的证书合同。",
            "寻找一个比原目标严格更弱、但能产生真实增量的中间定理。",
        ],
    },
    "falsifier": {
        "label": "反例攻击者",
        "mission": "Attack scope, quantifiers, hidden assumptions, boundary cases, and checker semantics; prefer a minimal exact counterexample.",
        "accent": "rose",
        "quick_prompts": [
            "优先寻找当前候选引理的最小反例和隐藏假设。",
            "检查是否存在有限到全局、局部到全局或量词越级。",
            "给出最便宜的 kill test，并说明失败后应失效哪些节点。",
        ],
    },
    "verifier": {
        "label": "证据与验证工程师",
        "mission": "Design replayable exact checkers, statement correspondence, hashes, trust boundaries, and independent reconstruction.",
        "accent": "amber",
        "quick_prompts": [
            "把当前最强结论改写成精确、可冷重放的验证器合同。",
            "审计生成器与检查器是否存在同源错误或循环验证。",
            "列出证书债务、缺失哈希、重放命令和独立实现要求。",
        ],
    },
    "synthesizer": {
        "label": "研究综合器",
        "mission": "State the strongest verified result, all unresolved load-bearing obligations, and the exact claim boundary.",
        "accent": "cyan",
        "quick_prompts": [
            "给出最强严格结论、未闭合义务和不可越过的宣传边界。",
            "把本轮成功、失败和可复用经验整理为下一轮研究合同。",
            "生成一份面向数学家与投资人的双层研究摘要。",
        ],
    },
}


AGENT_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "status", "executive_summary", "public_reasoning", "claim_updates",
        "tool_requests", "risks", "next_actions", "claim_boundary",
    ],
    "properties": {
        "status": {"type": "string", "enum": ["progress", "blocked", "falsified", "candidate", "error"]},
        "executive_summary": {"type": "string"},
        "public_reasoning": {
            "type": "object", "additionalProperties": False,
            "required": ["objective", "premises", "proposed_move", "observation", "falsification", "decision"],
            "properties": {
                "objective": {"type": "string"},
                "premises": {"type": "array", "items": {"type": "string"}},
                "proposed_move": {"type": "string"},
                "observation": {"type": "string"},
                "falsification": {"type": "string"},
                "decision": {"type": "string"},
            },
        },
        "claim_updates": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["claim_id", "action", "statement", "scope", "evidence_needed"],
                "properties": {
                    "claim_id": {"type": "string"},
                    "action": {"type": "string", "enum": ["propose", "refine", "block", "refute", "keep_open"]},
                    "statement": {"type": "string"},
                    "scope": {"type": "string"},
                    "evidence_needed": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "tool_requests": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["tool", "purpose", "command", "expected_discriminator"],
                "properties": {
                    "tool": {"type": "string"}, "purpose": {"type": "string"},
                    "command": {"type": "string"}, "expected_discriminator": {"type": "string"},
                },
            },
        },
        "risks": {"type": "array", "items": {"type": "string"}},
        "next_actions": {"type": "array", "items": {"type": "string"}},
        "claim_boundary": {"type": "string"},
    },
}

_ALLOWED_SANDBOXES = {"read-only", "workspace-write"}
_MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,120}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class CodexConfig:
    executable: str = "codex"
    workspace: Path = field(default_factory=Path.cwd)
    model: str | None = None
    sandbox: str = "read-only"
    timeout_seconds: int = 900
    network_access: bool = False
    web_search: str = "disabled"
    approval_policy: str = "never"
    max_output_chars: int = 120_000

    @classmethod
    def from_env(cls, workspace: str | Path | None = None) -> "CodexConfig":
        selected_workspace = Path(workspace or os.environ.get("MATHARC_CODEX_WORKSPACE") or Path.cwd()).resolve()
        sandbox = os.environ.get("MATHARC_CODEX_SANDBOX", "read-only")
        if sandbox not in _ALLOWED_SANDBOXES:
            sandbox = "read-only"
        return cls(
            executable=os.environ.get("MATHARC_CODEX_EXECUTABLE", "codex"),
            workspace=selected_workspace,
            model=os.environ.get("MATHARC_CODEX_MODEL") or None,
            sandbox=sandbox,
            timeout_seconds=max(30, int(os.environ.get("MATHARC_CODEX_TIMEOUT", "900"))),
            network_access=os.environ.get("MATHARC_CODEX_NETWORK", "0") == "1",
            web_search=os.environ.get("MATHARC_CODEX_WEB_SEARCH", "disabled"),
        )

    def validate(self) -> None:
        if self.sandbox not in _ALLOWED_SANDBOXES:
            raise ValueError(f"unsupported sandbox: {self.sandbox}")
        if self.model and not _MODEL_RE.fullmatch(self.model):
            raise ValueError("model contains unsupported characters")
        self.workspace = self.workspace.resolve()
        if not self.workspace.is_dir():
            raise ValueError(f"Codex workspace does not exist: {self.workspace}")


@dataclass(slots=True)
class CodexEvent:
    sequence: int
    type: str
    timestamp: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CodexTurnResult:
    local_session_id: str
    thread_id: str | None
    role: str
    prompt_sha256: str
    command: list[str]
    started_at: str
    ended_at: str
    return_code: int
    final_response: dict[str, Any] | None
    raw_final_text: str
    usage: dict[str, Any]
    events: list[CodexEvent]
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["events"] = [event.to_dict() for event in self.events]
        return value


def codex_status(config: CodexConfig | None = None) -> dict[str, Any]:
    config = config or CodexConfig.from_env()
    executable = shutil.which(config.executable)
    if executable is None and Path(config.executable).is_file():
        executable = str(Path(config.executable).resolve())
    return {
        "available": executable is not None,
        "executable": executable or config.executable,
        "workspace": str(config.workspace),
        "default_model": config.model,
        "default_sandbox": config.sandbox,
        "network_access": config.network_access,
        "web_search": config.web_search,
        "roles": PUBLIC_AGENT_ROLES,
        "acceptance_authority": False,
        "message": (
            "Codex CLI is available. Agent output remains proposal evidence until MathArc gates accept it."
            if executable else
            "Codex CLI is not installed or not on PATH. Install @openai/codex and configure authentication."
        ),
    }


_RESEARCH_RULES_MARKER = "NON-NEGOTIABLE RESEARCH RULES:"


def _role_preamble(role: str) -> str:
    role_spec = PUBLIC_AGENT_ROLES[role]
    return (
        "You are an agent worker inside MathArc Research.\n"
        f"ROLE: {role_spec['label']} ({role})\nMISSION: {role_spec['mission']}\n\n"
        f"{_RESEARCH_RULES_MARKER}\n"
        "1. You may propose, investigate, falsify, or design evidence; you may not self-assign VERIFIED.\n"
        "2. Never lift finite, local, numerical, or restricted evidence to a stronger scope without an explicit bridge.\n"
        "3. Distinguish PASS, FAIL, COUNTEREXAMPLE, UNKNOWN, TIMEOUT, and ERROR.\n"
        "4. Prefer one atomic load-bearing increment over broad persuasive prose.\n"
        "5. State a cheap falsification test before expensive work.\n"
        "6. Treat generator/checker independence, statement correspondence, hashes, and replay commands as first-class.\n"
        "7. Expose only a concise public reasoning summary, not private token-level chain-of-thought.\n"
        "8. The final response must match the supplied JSON schema exactly.\n\n"
    )


def build_agent_prompt(run: ResearchRun, role: str, user_message: str, *, metrics: dict[str, Any] | None = None) -> str:
    if role not in PUBLIC_AGENT_ROLES:
        raise ValueError(f"unknown role: {role}")
    metrics = metrics or compute_metrics(run)
    claims = [
        {
            "claim_id": c.claim_id, "statement": c.statement, "scope": c.scope_level.name,
            "status": c.status.value, "critical": c.critical, "dependencies": c.dependencies,
            "evidence_ids": c.evidence_ids, "notes": c.notes,
        }
        for c in run.claims.values()
    ]
    routes = [
        {
            "route_id": r.route_id, "name": r.name, "mechanism": r.mechanism,
            "basin": r.basin, "status": r.status, "verified_gain": r.verified_gain,
            "rounds_without_gain": r.rounds_without_gain,
        }
        for r in run.routes.values()
    ]
    state = {
        "run_id": run.run_id,
        "release_state": run.release_state,
        "contract": {
            "theorem_id": run.contract.theorem_id, "title": run.contract.title,
            "statement": run.contract.statement, "scope": run.contract.scope_level.name,
            "quantifiers": run.contract.quantifiers, "assumptions": run.contract.assumptions,
            "root_claim_id": run.contract.root_claim_id, "status_date": run.contract.status_date,
        },
        "metrics": metrics,
        "claims": claims,
        "routes": routes,
        "recent_failures": [
            {
                "failure_id": f.failure_id, "claim_id": f.claim_id,
                "classification": f.classification, "root_cause": f.root_cause,
                "invalidated_claim_ids": f.invalidated_claim_ids,
            }
            for f in run.failures[-12:]
        ],
    }
    return (
        _role_preamble(role)
        + "FROZEN RESEARCH STATE:\n" + json.dumps(state, ensure_ascii=False, indent=2)
        + "\n\nUSER REQUEST:\n" + user_message.strip()
    )


def normalize_codex_event(sequence: int, raw: dict[str, Any]) -> CodexEvent:
    event_type = str(raw.get("type", "unknown"))
    payload: dict[str, Any] = {"raw_type": event_type}
    if event_type == "thread.started":
        payload.update({"thread_id": raw.get("thread_id"), "label": "Codex thread started"})
    elif event_type in {"turn.started", "turn.completed", "turn.failed"}:
        payload.update({k: v for k, v in raw.items() if k != "type"})
        payload["label"] = event_type.replace(".", " ").title()
    elif event_type in {"item.started", "item.updated", "item.completed"}:
        item = raw.get("item") or {}
        item_type = str(item.get("type", "unknown"))
        payload.update({"item_type": item_type, "item_id": item.get("id"), "phase": event_type.split(".", 1)[1]})
        if item_type == "reasoning":
            payload.update({"text": item.get("text", ""), "label": "Public reasoning summary"})
        elif item_type == "agent_message":
            payload.update({"text": item.get("text", ""), "label": "Agent response"})
        elif item_type == "command_execution":
            payload.update({
                "command": item.get("command", ""), "output": str(item.get("aggregated_output", ""))[-20_000:],
                "exit_code": item.get("exit_code"), "status": item.get("status"), "label": "Command execution",
            })
        elif item_type == "file_change":
            payload.update({"changes": item.get("changes", []), "status": item.get("status"), "label": "Workspace file change"})
        elif item_type == "mcp_tool_call":
            payload.update({
                "server": item.get("server"), "tool": item.get("tool"), "arguments": item.get("arguments"),
                "status": item.get("status"), "error": item.get("error"), "label": "MCP tool call",
            })
        elif item_type == "web_search":
            payload.update({"query": item.get("query", ""), "label": "Web search"})
        elif item_type == "todo_list":
            payload.update({"items": item.get("items", []), "label": "Research plan"})
        elif item_type == "error":
            payload.update({"message": item.get("message", ""), "label": "Codex item error"})
        else:
            payload.update({"item": item, "label": item_type.replace("_", " ").title()})
    elif event_type == "error":
        payload.update({"message": raw.get("message", ""), "label": "Codex stream error"})
    else:
        payload.update({"event": raw, "label": event_type})
    return CodexEvent(sequence=sequence, type=event_type, timestamp=utc_now(), payload=payload)


def parse_jsonl_event(line: str, sequence: int) -> CodexEvent:
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        raise CodexRuntimeError(f"Codex emitted invalid JSONL: {line[:400]}") from exc
    if not isinstance(raw, dict):
        raise CodexRuntimeError("Codex JSONL event must be an object")
    return normalize_codex_event(sequence, raw)


class CodexRunner:
    """Non-interactive Codex CLI adapter with structured final output and JSONL events."""

    def __init__(self, config: CodexConfig | None = None) -> None:
        self.config = config or CodexConfig.from_env()
        self.config.validate()

    def build_command(self, *, schema_path: Path, last_message_path: Path, thread_id: str | None = None,
                      model: str | None = None, sandbox: str | None = None) -> list[str]:
        selected_sandbox = sandbox or self.config.sandbox
        if selected_sandbox not in _ALLOWED_SANDBOXES:
            raise ValueError(f"unsupported sandbox: {selected_sandbox}")
        selected_model = model or self.config.model
        if selected_model and not _MODEL_RE.fullmatch(selected_model):
            raise ValueError("model contains unsupported characters")
        command = [
            self.config.executable, "exec", "--json", "--skip-git-repo-check",
            "--sandbox", selected_sandbox, "--cd", str(self.config.workspace),
            "--output-schema", str(schema_path), "--output-last-message", str(last_message_path),
            "--config", f"approval_policy=\"{self.config.approval_policy}\"",
            "--config", "sandbox_workspace_write.network_access=" + ("true" if self.config.network_access else "false"),
            "--config", f"web_search=\"{self.config.web_search}\"",
        ]
        if selected_model:
            command.extend(["--model", selected_model])
        command.extend(["resume", thread_id, "-"] if thread_id else ["-"])
        return command

    def stream_turn(self, prompt: str, *, role: str, thread_id: str | None = None,
                    model: str | None = None, sandbox: str | None = None,
                    timeout_seconds: int | None = None) -> Iterator[CodexEvent]:
        if role not in PUBLIC_AGENT_ROLES:
            raise ValueError(f"unknown role: {role}")
        if _RESEARCH_RULES_MARKER not in prompt:
            # A worker must never receive a turn without the research rules,
            # even when the caller bypasses build_agent_prompt.
            prompt = _role_preamble(role) + "USER REQUEST:\n" + prompt.strip() + "\n"
        timeout = timeout_seconds or self.config.timeout_seconds
        local_session_id = f"codex-{uuid.uuid4().hex[:16]}"
        started_at = utc_now()
        events: list[CodexEvent] = []
        usage: dict[str, Any] = {}
        observed_thread_id = thread_id
        stderr_lines: list[str] = []

        with tempfile.TemporaryDirectory(prefix="matharc-codex-") as temp_dir:
            temp = Path(temp_dir)
            schema_path = temp / "agent-output.schema.json"
            last_message_path = temp / "last-message.json"
            schema_path.write_text(json.dumps(AGENT_OUTPUT_SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")
            command = self.build_command(
                schema_path=schema_path, last_message_path=last_message_path,
                thread_id=thread_id, model=model, sandbox=sandbox,
            )
            executable = shutil.which(command[0])
            if executable is None and not Path(command[0]).is_file():
                raise CodexRuntimeError(
                    f"Codex executable not found: {command[0]}. Install @openai/codex or set MATHARC_CODEX_EXECUTABLE."
                )
            process = subprocess.Popen(
                command, cwd=self.config.workspace, env=dict(os.environ), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                errors="replace", bufsize=1,
            )
            if process.stdin is None or process.stdout is None or process.stderr is None:
                process.kill(); raise CodexRuntimeError("Codex process did not expose standard streams")
            process.stdin.write(prompt); process.stdin.close()
            stream_queue: queue.Queue[tuple[str, str | None]] = queue.Queue()

            def read_stream(name: str, stream: Any) -> None:
                try:
                    for line in stream:
                        stream_queue.put((name, line.rstrip("\n")))
                finally:
                    stream_queue.put((name, None))

            threading.Thread(target=read_stream, args=("stdout", process.stdout), daemon=True).start()
            threading.Thread(target=read_stream, args=("stderr", process.stderr), daemon=True).start()
            closed: set[str] = set(); deadline = time.monotonic() + timeout; sequence = 0
            while len(closed) < 2 or process.poll() is None:
                if time.monotonic() > deadline:
                    process.kill(); process.wait(timeout=5)
                    raise CodexRuntimeError(f"Codex turn exceeded {timeout} seconds")
                try:
                    source, line = stream_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                if line is None:
                    closed.add(source); continue
                if source == "stderr":
                    stderr_lines.append(line); continue
                if not line.strip():
                    continue
                sequence += 1
                event = parse_jsonl_event(line, sequence); events.append(event)
                if event.type == "thread.started":
                    observed_thread_id = event.payload.get("thread_id") or observed_thread_id
                if event.type == "turn.completed":
                    usage = event.payload.get("usage") or {}
                yield event

            return_code = process.wait(timeout=5)
            raw_final_text = last_message_path.read_text(encoding="utf-8", errors="replace") if last_message_path.exists() else ""
            raw_final_text = raw_final_text[: self.config.max_output_chars]
            final_response: dict[str, Any] | None = None
            if raw_final_text.strip():
                try:
                    parsed = json.loads(raw_final_text)
                    final_response = parsed if isinstance(parsed, dict) else None
                except json.JSONDecodeError:
                    pass
            if return_code != 0:
                detail = "\n".join(stderr_lines)[-12000:]
                raise CodexRuntimeError(f"Codex exited with code {return_code}: {detail}")
            if final_response is None:
                raise CodexRuntimeError("Codex completed without a valid structured final response")
            result = CodexTurnResult(
                local_session_id=local_session_id, thread_id=observed_thread_id, role=role,
                prompt_sha256=digest_text(prompt), command=_redact_command(command),
                started_at=started_at, ended_at=utc_now(), return_code=return_code,
                final_response=final_response, raw_final_text=raw_final_text, usage=usage,
                events=events, stderr="\n".join(stderr_lines)[-12_000:],
            )
            sequence += 1
            yield CodexEvent(sequence, "matharc.result", utc_now(), {"result": result.to_dict()})


def _redact_command(command: list[str]) -> list[str]:
    return ["<temporary-file>" if "matharc-codex-" in token else token for token in command]


class CodexSessionStore:
    """Append-only public Codex session store."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve(); self.root.mkdir(parents=True, exist_ok=True)

    def session_path(self, session_id: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id)[:160]
        if not safe:
            raise ValueError("empty session id")
        return self.root / f"{safe}.json"

    def write_result(self, result: dict[str, Any]) -> Path:
        session_id = str(result.get("local_session_id") or f"session-{uuid.uuid4().hex}")
        target = self.session_path(session_id)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    def list_sessions(self, limit: int = 30) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        paths = sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in paths[: max(1, min(limit, 200))]:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            final = raw.get("final_response") or {}
            rows.append({
                "local_session_id": raw.get("local_session_id"), "thread_id": raw.get("thread_id"),
                "role": raw.get("role"), "started_at": raw.get("started_at"), "ended_at": raw.get("ended_at"),
                "status": final.get("status"), "executive_summary": final.get("executive_summary"),
                "usage": raw.get("usage", {}), "result_sha256": raw.get("result_sha256"), "file": path.name,
            })
        return rows

    def load_session(self, session_id: str) -> dict[str, Any]:
        payload = json.loads(self.session_path(session_id).read_text(encoding="utf-8"))
        return cast("dict[str, Any]", payload)


def result_digest(result: dict[str, Any]) -> str:
    return digest_json(result)
