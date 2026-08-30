from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from matharc.v02.claude_code_runtime import ClaudeCodeRunner, claude_code_status
from matharc.v02.model_workers import LLMProposalWorker
from matharc.v02.orchestrator import ResearchOrchestrator
from matharc.v02.prompting import build_trace_view
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolStatus,
    utc_now,
)
from matharc.v02.trace import ResearchTrace


def _synthetic_trace() -> ResearchTrace:
    trace = ResearchTrace(
        run_id="SMOKE-CLAUDE-SYNTHETIC",
        contract=TheoremContract(
            contract_id="SMOKE-CLAUDE-CONTRACT",
            problem="Assess the synthetic claim that every odd integer squared is odd.",
            target_claim_ids=("C-SMOKE",),
            scope="All odd integers; synthetic smoke-test data only.",
        ),
    )
    trace.add_claim(
        ClaimRecord(
            claim_id="C-SMOKE",
            statement="For every odd integer n, n^2 is odd.",
            scope="All odd integers.",
            status=ClaimStatus.OPEN,
            critical=False,
            boundary="This smoke run is not a research novelty claim.",
        )
    )
    trace.add_route(
        ResearchRoute(
            route_id="R-PARITY",
            name="Parity normalization",
            hypothesis="Write n=2k+1 and normalize the square modulo 2.",
            mechanism_signature=("parity", "algebraic normalization"),
            kill_test="Check the smallest odd boundary cases and the symbolic parity expansion.",
            status=RouteStatus.ACTIVE,
            claim_ids=("C-SMOKE",),
            expected_discriminator="Any even square of an odd input kills the route.",
        )
    )
    return trace


def _safe_component(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return normalized[:96] or "turn"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one real Claude Code proposal turn and persist sanitized evidence."
    )
    parser.add_argument("--output", default="artifacts/smoke/claude-code.json")
    parser.add_argument(
        "--publish-dir",
        help=(
            "optional tracked directory for a commit-ready sanitized copy; "
            "recommended: docs/baselines/smoke"
        ),
    )
    args = parser.parse_args(argv)

    status = claude_code_status()
    if not status["available"]:
        print(status["message"])
        return 2

    trace = _synthetic_trace()
    orchestrator = ResearchOrchestrator(trace)
    plan = orchestrator.plan_round()
    trace_view = build_trace_view(trace, plan)
    worker = LLMProposalWorker("falsifier", runner=ClaudeCodeRunner())
    execution = worker.execute(plan, trace_view)

    if execution.tool_call.status is not ToolStatus.PASS or execution.proposal is None:
        print("Claude smoke failed:", execution.raw_stderr)
        return 3

    trace.add_tool_call(execution.tool_call)
    orchestrator.accept_agent_proposal(role=worker.role, payload=execution.proposal)

    generated_at = utc_now()
    artifact = {
        "schema": "matharc.claude-smoke-evidence.1",
        "generated_at": generated_at,
        "synthetic_input_only": True,
        "acceptance_authority": False,
        "provider_status": {
            "available": status["available"],
            "executable": Path(str(status["executable"])).name,
            "default_model": status["default_model"],
        },
        "model_usage": execution.model_usage or {},
        "tool_call": execution.tool_call.to_dict(),
        "proposal": execution.proposal,
        "trace": trace.to_dict(),
        "claim_boundary": (
            "This proves only that the authenticated Claude Code CLI completed one "
            "synthetic proposal-only turn through the current MathArc contract. It is "
            "not proof evidence for any open mathematical problem."
        ),
    }
    serialized = json.dumps(artifact, indent=2, sort_keys=True) + "\n"

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding="utf-8")
    print(f"Claude smoke evidence written: {output}")

    if args.publish_dir:
        publish_dir = Path(args.publish_dir)
        publish_dir.mkdir(parents=True, exist_ok=True)
        call_component = _safe_component(execution.tool_call.call_id)
        publish_path = publish_dir / f"{generated_at[:10]}-{call_component}.json"
        if publish_path.exists():
            print(f"Refusing to overwrite existing published smoke evidence: {publish_path}")
            return 4
        publish_path.write_text(serialized, encoding="utf-8")
        print(f"Commit-ready sanitized smoke evidence written: {publish_path}")

    print(
        "The evidence contains no raw prompt/stdout, uses synthetic mathematical input only, "
        "and carries no theorem-acceptance authority."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
