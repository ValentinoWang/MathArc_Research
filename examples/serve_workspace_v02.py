from __future__ import annotations

import argparse
import ipaddress
import json
import signal
import sys
from pathlib import Path

try:
    from matharc.v02.access import InvitationAccessStore
    from matharc.v02.workspace_server import make_server
except ModuleNotFoundError as exc:
    # `python examples/serve_workspace_v02.py ...` sets sys.path[0] to the
    # examples directory.  In a source checkout where the package has not
    # been installed into the selected interpreter, that made the script fail
    # before it could even validate CLI arguments.  Fall back only for the
    # missing top-level project package; unrelated missing dependencies must
    # still fail normally.
    if exc.name != "matharc":
        raise
    project_root = Path(__file__).resolve().parents[1]
    project_root_text = str(project_root)
    if project_root_text not in sys.path:
        sys.path.insert(0, project_root_text)
    from matharc.v02.access import InvitationAccessStore
    from matharc.v02.workspace_server import make_server


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Serve a verified MathArc v0.2 workspace through a read-only HTTP/SSE "
            "observatory. Every request revalidates the workspace manifest and hashes."
        )
    )
    parser.add_argument(
        "--workspace",
        default="artifacts/v02-workspace",
        help="exported workspace directory containing workspace.json",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--dashboard")
    parser.add_argument(
        "--access-store",
        help="external directory for hashed invitation and session state",
    )
    parser.add_argument(
        "--issue-preview-email",
        help="issue one invitation for this email and print it once at startup",
    )
    parser.add_argument(
        "--topic-scope",
        action="append",
        default=[],
        help="scope metadata for the issued invitation; repeat for multiple values",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="explicitly allow a non-loopback bind; TLS remains an external responsibility",
    )
    parser.add_argument("--sse-poll-seconds", type=float, default=0.5)
    parser.add_argument("--sse-lifetime-seconds", type=float, default=30.0)
    args = parser.parse_args()

    if not (0 <= args.port <= 65535):
        raise SystemExit("--port must be between 0 and 65535")
    if args.sse_poll_seconds <= 0 or args.sse_lifetime_seconds <= 0:
        raise SystemExit("SSE timing values must be positive")
    if not _is_loopback_host(args.host) and not args.allow_remote:
        raise SystemExit(
            "Refusing a non-loopback bind without --allow-remote. The observatory "
            "does not provide a TLS layer."
        )
    if args.issue_preview_email and not args.access_store:
        raise SystemExit("--issue-preview-email requires --access-store")
    if args.topic_scope and not args.issue_preview_email:
        raise SystemExit("--topic-scope requires --issue-preview-email")

    workspace = Path(args.workspace).resolve()
    dashboard = Path(args.dashboard).resolve() if args.dashboard else None
    server = make_server(
        workspace,
        host=args.host,
        port=args.port,
        dashboard_path=dashboard,
        sse_poll_seconds=args.sse_poll_seconds,
        sse_lifetime_seconds=args.sse_lifetime_seconds,
        access_store_root=args.access_store,
    )
    invitation = None
    if args.issue_preview_email:
        invitation = InvitationAccessStore(args.access_store).issue_invitation(
            email=args.issue_preview_email,
            topic_scopes=args.topic_scope or ["research-preview"],
    )
    bound_host, bound_port = server.server_address[:2]
    bound_host_text = (
        bound_host.decode("ascii") if isinstance(bound_host, bytes) else str(bound_host)
    )
    startup = {
        "schema_version": "1.0",
        "workspace": str(workspace),
        "url": f"http://{bound_host_text}:{bound_port}/",
        "health": f"http://{bound_host_text}:{bound_port}/api/health",
        "events": f"http://{bound_host_text}:{bound_port}/events",
        "read_only": True,
        "authentication": bool(args.access_store),
        "access_store": str(Path(args.access_store).resolve()) if args.access_store else None,
        "preview_email": args.issue_preview_email,
        "preview_invitation_code": invitation.code if invitation else None,
        "topic_scopes": list(invitation.invitation.topic_scopes) if invitation else [],
        "tls": False,
        "remote_binding_explicitly_allowed": bool(args.allow_remote),
        "verification_policy": "full workspace reload and hash validation per request",
    }
    print(json.dumps(startup, ensure_ascii=False, indent=2, sort_keys=True), flush=True)

    def stop(_signum: int, _frame: object) -> None:
        # shutdown() must run outside the serve_forever call stack.
        import threading

        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
