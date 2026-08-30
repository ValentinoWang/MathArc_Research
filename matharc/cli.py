from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent_service import CodexAgentService
from .api import serve
from .codex_runtime import CodexConfig, codex_status
from .demo import write_demo
from .metrics import compute_metrics
from .store import load_run
from .tools import FiniteOddSumTool, InductionCertificateTool, PolynomialIdentityTool
from .validator import validate_run


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="matharc", description="MathArc Research CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="generate the deterministic proof-carrying demo")
    demo.add_argument("--out-dir", default="artifacts/demo")

    validate = sub.add_parser("validate", help="validate a research run")
    validate.add_argument("--run", required=True)

    metrics = sub.add_parser("metrics", help="compute dashboard metrics")
    metrics.add_argument("--run", required=True)

    server = sub.add_parser("serve", help="serve the interactive research console")
    server.add_argument("--run", required=True)
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8000)
    server.add_argument("--workspace")
    server.add_argument("--session-dir")

    codex = sub.add_parser("codex", help="inspect or invoke Codex research workers")
    codex_sub = codex.add_subparsers(dest="codex_command", required=True)
    codex_status_cmd = codex_sub.add_parser("status")
    codex_status_cmd.add_argument("--workspace", default=".")
    codex_turn = codex_sub.add_parser("turn")
    codex_turn.add_argument("--run", required=True)
    codex_turn.add_argument("--role", default="strategist")
    codex_turn.add_argument("--message", required=True)
    codex_turn.add_argument("--sandbox", choices=["read-only", "workspace-write"], default="read-only")
    codex_turn.add_argument("--workspace", default=".")
    codex_turn.add_argument("--session-dir")
    codex_turn.add_argument("--model")
    codex_turn.add_argument("--thread-id")
    codex_turn.add_argument("--timeout-seconds", type=int, default=900)
    codex_sessions = codex_sub.add_parser("sessions")
    codex_sessions.add_argument("--run", required=True)
    codex_sessions.add_argument("--workspace", default=".")
    codex_sessions.add_argument("--session-dir")
    codex_sessions.add_argument("--limit", type=int, default=30)

    tool = sub.add_parser("tool", help="invoke a deterministic exact tool")
    tool_sub = tool.add_subparsers(dest="tool_name", required=True)
    polynomial = tool_sub.add_parser("polynomial")
    polynomial.add_argument("--lhs", required=True)
    polynomial.add_argument("--rhs", required=True)
    polynomial.add_argument("--variable", default="n")
    finite = tool_sub.add_parser("finite-odd-sum")
    finite.add_argument("--maximum", type=int, required=True)
    induction = tool_sub.add_parser("induction")
    induction.add_argument("--certificate-json", required=True)

    args = parser.parse_args(argv)
    if args.command == "demo":
        paths = write_demo(args.out_dir)
        print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))
    elif args.command == "validate":
        result = validate_run(load_run(args.run))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result["valid"] else 1)
    elif args.command == "metrics":
        print(json.dumps(compute_metrics(load_run(args.run)), ensure_ascii=False, indent=2))
    elif args.command == "serve":
        serve(
            args.run,
            args.host,
            args.port,
            workspace=args.workspace,
            session_dir=args.session_dir,
        )
    elif args.command == "codex":
        if args.codex_command == "status":
            print(
                json.dumps(
                    codex_status(CodexConfig.from_env(Path(args.workspace).resolve())),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            run = load_run(args.run)
            service = CodexAgentService(
                run,
                workspace=args.workspace,
                session_root=args.session_dir,
            )
            if args.codex_command == "sessions":
                print(json.dumps(service.list_sessions(args.limit), ensure_ascii=False, indent=2))
            else:
                result = service.run(
                    {
                        "role": args.role,
                        "message": args.message,
                        "sandbox": args.sandbox,
                        "model": args.model,
                        "thread_id": args.thread_id,
                        "timeout_seconds": args.timeout_seconds,
                    }
                )
                print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "tool":
        if args.tool_name == "polynomial":
            result = PolynomialIdentityTool().run("CLI", args.lhs, args.rhs, args.variable)
        elif args.tool_name == "finite-odd-sum":
            result = FiniteOddSumTool().run("CLI", args.maximum)
        else:
            result = InductionCertificateTool().run("CLI", json.loads(args.certificate_json))
        print(
            json.dumps(
                {
                    "call": {**result.call.__dict__, "status": result.call.status.value},
                    "output": result.output,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(0 if result.call.status.value == "PASS" else 1)


if __name__ == "__main__":
    main()
