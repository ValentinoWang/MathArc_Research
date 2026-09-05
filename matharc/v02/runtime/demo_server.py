"""Local HTTP server for the credential-free MathArc Agent demonstration."""
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .demo_runner import run_agent_demo


ROOT = Path(__file__).resolve().parents[3]
PAGE = ROOT / "docs" / "prototypes" / "problem-intel-console.html"
MAX_REQUEST_BYTES = 64 * 1024


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "MathArcAgentDemo/1.0"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html", "/problem-intel-console.html"}:
            self._send(HTTPStatus.OK, "text/html; charset=utf-8", PAGE.read_bytes())
            return
        if self.path == "/api/health":
            self._send_json(HTTPStatus.OK, {"ok": True, "service": "matharc-agent-demo", "deterministic": True})
            return
        if self.path.startswith("/api/demo/runs/"):
            run_id = self.path.removeprefix("/api/demo/runs/").strip("/")
            self._send_run_readback(run_id)
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/demo/run":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            payload = self._read_json()
            question = payload.get("question")
            if not isinstance(question, str) or not question.strip():
                raise ValueError("question is required")
            evidence_dir = getattr(self.server, "evidence_dir", None)
            # Derive the deterministic run id first, then persist under that id so
            # a later readback cannot accidentally return a different run.
            result = run_agent_demo(question)
            if evidence_dir is not None:
                result = run_agent_demo(question, output_dir=Path(evidence_dir) / result.run_id)
        except (ValueError, TypeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        payload = result.to_dict()
        # Host paths are an internal persistence detail and must not cross the
        # HTTP boundary or be copied into browser evidence.
        if payload.get("output_paths"):
            payload["output_paths"] = {"json": "agent-demo.json", "markdown": "agent-demo.md"}
        self._send_json(HTTPStatus.OK, payload)

    def _send_run_readback(self, run_id: str) -> None:
        evidence_dir = getattr(self.server, "evidence_dir", None)
        if evidence_dir is None or not run_id or "/" in run_id or "\\" in run_id:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "run readback is not configured"})
            return
        path = Path(evidence_dir) / run_id / "agent-demo.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "run not found"})
            return
        if payload.get("run_id") != run_id:
            self._send_json(HTTPStatus.CONFLICT, {"error": "run identity mismatch"})
            return
        if payload.get("output_paths"):
            payload["output_paths"] = {"json": "agent-demo.json", "markdown": "agent-demo.md"}
        self._send_json(HTTPStatus.OK, payload)

    def _read_json(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length is required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > MAX_REQUEST_BYTES:
            raise ValueError(f"request body must be <= {MAX_REQUEST_BYTES} bytes")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be a UTF-8 JSON object") from exc
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def _send_json(self, status: HTTPStatus, value: object) -> None:
        self._send(status, "application/json; charset=utf-8", (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8"))

    def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = "127.0.0.1", port: int = 4173, evidence_dir: str | Path | None = None) -> None:
    if not PAGE.is_file():
        raise FileNotFoundError(PAGE)
    server = ThreadingHTTPServer((host, port), DemoHandler)
    server.evidence_dir = Path(evidence_dir).resolve() if evidence_dir is not None else None
    if server.evidence_dir is not None:
        server.evidence_dir.mkdir(parents=True, exist_ok=True)
    print(f"MathArc Agent demo: http://{host}:{port}/problem-intel-console.html", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serve the local MathArc Agent demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--evidence-dir", default=None, help="persist demo runs for readback")
    args = parser.parse_args(argv)
    serve(args.host, args.port, args.evidence_dir)


if __name__ == "__main__":
    main()


__all__ = ["DemoHandler", "main", "serve"]

