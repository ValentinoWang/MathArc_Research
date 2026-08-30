from __future__ import annotations

import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .agent_service import AgentRequestError, CodexAgentService, sse_encode
from .codex_runtime import CodexRuntimeError
from .dashboard import render_dashboard
from .metrics import compute_metrics
from .store import load_run
from .validator import validate_run


_MAX_REQUEST_BYTES = 64 * 1024


def serve(
    run_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    workspace: str | Path | None = None,
    session_dir: str | Path | None = None,
) -> None:
    run_file = Path(run_path).resolve()
    run = load_run(run_file)
    metrics = compute_metrics(run)
    dashboard = render_dashboard(run, metrics).encode("utf-8")
    project_workspace = Path(
        workspace
        or os.environ.get("MATHARC_CODEX_WORKSPACE")
        or Path.cwd()
    ).resolve()
    agent_service = CodexAgentService(
        run,
        workspace=project_workspace,
        session_root=session_dir,
    )

    def fresh_payloads() -> dict[str, bytes]:
        return {
            "/api/run": json.dumps(
                run.to_dict(), ensure_ascii=False, indent=2
            ).encode("utf-8"),
            "/api/metrics": json.dumps(
                compute_metrics(run), ensure_ascii=False, indent=2
            ).encode("utf-8"),
            "/api/validate": json.dumps(
                validate_run(run), ensure_ascii=False, indent=2
            ).encode("utf-8"),
            "/api/health": json.dumps(
                {
                    "ok": True,
                    "run_id": run.run_id,
                    "release_state": run.release_state,
                    "codex_available": agent_service.status()["available"],
                }
            ).encode("utf-8"),
            "/api/agent/status": json.dumps(
                agent_service.status(), ensure_ascii=False, indent=2
            ).encode("utf-8"),
            "/api/agent/roles": json.dumps(
                agent_service.roles(), ensure_ascii=False, indent=2
            ).encode("utf-8"),
        }

    class Handler(BaseHTTPRequestHandler):
        server_version = "MathArcResearch/0.1.0"

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self._common_headers()
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            if path in {"/", "/index.html"}:
                self._send(HTTPStatus.OK, "text/html; charset=utf-8", dashboard)
                return
            payloads = fresh_payloads()
            if path in payloads:
                self._send(
                    HTTPStatus.OK,
                    "application/json; charset=utf-8",
                    payloads[path],
                )
                return
            if path == "/api/agent/sessions":
                query = parse_qs(parsed.query)
                try:
                    limit = int((query.get("limit") or ["30"])[0])
                except ValueError:
                    limit = 30
                self._send_json(HTTPStatus.OK, agent_service.list_sessions(limit=limit))
                return
            prefix = "/api/agent/sessions/"
            if path.startswith(prefix):
                session_id = unquote(path[len(prefix) :])
                try:
                    payload = agent_service.load_session(session_id)
                except (FileNotFoundError, ValueError, json.JSONDecodeError):
                    self._send_json(
                        HTTPStatus.NOT_FOUND,
                        {"error": "session not found", "session_id": session_id},
                    )
                    return
                self._send_json(HTTPStatus.OK, payload)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                payload = self._read_json()
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            if path == "/api/agent/turn":
                try:
                    result = agent_service.run(payload)
                except AgentRequestError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                except CodexRuntimeError as exc:
                    self._send_json(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {"error": str(exc), "codex": agent_service.status()},
                    )
                    return
                self._send_json(HTTPStatus.OK, result)
                return
            if path == "/api/agent/stream":
                self._stream_agent(payload)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def _stream_agent(self, payload: dict[str, object]) -> None:
            self.send_response(HTTPStatus.OK)
            self._common_headers()
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            self.close_connection = True
            try:
                for event in agent_service.stream(payload):
                    self.wfile.write(sse_encode(event))
                    self.wfile.flush()
            except (AgentRequestError, CodexRuntimeError, ValueError) as exc:
                error = {
                    "sequence": -1,
                    "type": "matharc.error",
                    "timestamp": "",
                    "payload": {
                        "message": str(exc),
                        "codex": agent_service.status(),
                    },
                }
                body = (
                    "event: matharc_error\n"
                    + "data: "
                    + json.dumps(error, ensure_ascii=False, separators=(",", ":"))
                    + "\n\n"
                ).encode("utf-8")
                try:
                    self.wfile.write(body)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
            except (BrokenPipeError, ConnectionResetError):
                return

        def _read_json(self) -> dict[str, object]:
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise ValueError("Content-Length is required")
            try:
                length = int(raw_length)
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length < 0 or length > _MAX_REQUEST_BYTES:
                raise ValueError(f"request body must be <= {_MAX_REQUEST_BYTES} bytes")
            raw = self.rfile.read(length)
            try:
                value = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("request body must be a UTF-8 JSON object") from exc
            if not isinstance(value, dict):
                raise ValueError("request body must be a JSON object")
            return value

        def _send_json(self, status: HTTPStatus, value: object) -> None:
            self._send(
                status,
                "application/json; charset=utf-8",
                (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            )

        def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self._common_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _common_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; connect-src 'self'; "
                "img-src 'self' data:; font-src 'self'; frame-ancestors 'none'",
            )

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"MathArc Research Console: http://{host}:{port}")
    print(
        "Codex status:",
        "available" if agent_service.status()["available"] else "unavailable",
        "· workspace",
        project_workspace,
    )
    server.serve_forever()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--workspace")
    parser.add_argument("--session-dir")
    args = parser.parse_args(argv)
    serve(
        args.run,
        args.host,
        args.port,
        workspace=args.workspace,
        session_dir=args.session_dir,
    )


if __name__ == "__main__":
    main()
