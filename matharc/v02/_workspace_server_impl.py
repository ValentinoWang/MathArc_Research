from __future__ import annotations

import json
import mimetypes
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .console_export import ConsoleLocalProjectionConfig, campaign_snapshot, build_console_export
from .console_topic import TopicStoreConfig
from .topic_observation import TopicObservationRunner
from .review_server import ReviewAPI, ReviewHTTPResponse, ReviewServerConfig
from .workspace import ResearchWorkspace
from .workspace_visualization import workspace_dashboard_payload


@dataclass(slots=True)
class WorkspaceSnapshot:
    workspace: ResearchWorkspace
    loaded_at: float
    manifest_mtime_ns: int


class WorkspaceRepository:
    """Thread-safe loader that verifies the full workspace on every change."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self._lock = threading.RLock()
        self._snapshot: WorkspaceSnapshot | None = None

    def load(self, *, force: bool = False) -> ResearchWorkspace:
        manifest = self.root / "workspace.json"
        stat = manifest.stat()
        with self._lock:
            if (
                not force
                and self._snapshot is not None
                and self._snapshot.manifest_mtime_ns == stat.st_mtime_ns
            ):
                return self._snapshot.workspace
            workspace = ResearchWorkspace.load(self.root)
            self._snapshot = WorkspaceSnapshot(
                workspace=workspace,
                loaded_at=time.time(),
                manifest_mtime_ns=stat.st_mtime_ns,
            )
            return workspace

    def payload(self) -> dict[str, Any]:
        workspace = self.load()
        return workspace_dashboard_payload(workspace)


class WorkspaceHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        repository: WorkspaceRepository,
        *,
        dashboard_path: str | Path,
        sse_poll_seconds: float = 0.5,
        sse_lifetime_seconds: float = 30.0,
        review_api: ReviewAPI | None = None,
        topic_store: TopicObservationRunner | None = None,
        local_projection_config: ConsoleLocalProjectionConfig | None = None,
    ) -> None:
        self.repository = repository
        self.dashboard_path = Path(dashboard_path).resolve()
        self.sse_poll_seconds = sse_poll_seconds
        self.sse_lifetime_seconds = sse_lifetime_seconds
        # Explicitly opt-in: this is a transport adapter over a separate
        # review trace, never an implicit workspace mutation path.
        self.review_api = review_api
        self.topic_store = topic_store
        self.local_projection_config = local_projection_config
        super().__init__(server_address, WorkspaceRequestHandler)


class WorkspaceRequestHandler(BaseHTTPRequestHandler):
    server: WorkspaceHTTPServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if self._dispatch_review_get(parsed.path):
                return
            if parsed.path in {"/", "/index.html"}:
                self._serve_dashboard()
                return
            if parsed.path == "/api/health":
                workspace = self.server.repository.load()
                audit = workspace.audit()
                self._json(
                    HTTPStatus.OK if audit.valid else HTTPStatus.CONFLICT,
                    {
                        "status": "ok" if audit.valid else "invalid",
                        "run_id": workspace.trace.run_id,
                        "state_digest_sha256": workspace.state_digest(),
                        "event_head_hash": workspace.events.head_hash,
                        "audit_errors": audit.error_count,
                        "audit_warnings": audit.warning_count,
                    },
                )
                return
            if parsed.path == "/api/workspace":
                self._json(HTTPStatus.OK, self.server.repository.payload())
                return
            if parsed.path == "/api/campaign":
                self._json(HTTPStatus.OK, self._campaign_payload())
                return
            if parsed.path == "/api/console":
                self._json(
                    HTTPStatus.OK,
                    build_console_export(
                        self.server.repository.root,
                        topic_store=self.server.topic_store,
                        local_projection_config=self.server.local_projection_config,
                    ),
                )
                return
            if parsed.path == "/api/audit":
                workspace = self.server.repository.load()
                self._json(HTTPStatus.OK, workspace.audit().to_dict())
                return
            if parsed.path == "/api/events":
                query = parse_qs(parsed.query)
                after = int(query.get("after", ["-1"])[0])
                workspace = self.server.repository.load()
                events = [
                    item.to_dict()
                    for item in workspace.events.events
                    if item.sequence > after
                ]
                self._json(
                    HTTPStatus.OK,
                    {
                        "after": after,
                        "head_hash": workspace.events.head_hash,
                        "events": events,
                    },
                )
                return
            if parsed.path == "/api/artifacts":
                workspace = self.server.repository.load()
                self._json(
                    HTTPStatus.OK,
                    {
                        "records": [
                            item.to_dict() for item in workspace.artifacts.records
                        ],
                        "raw_download_enabled": False,
                    },
                )
                return
            if parsed.path == "/events":
                query = parse_qs(parsed.query)
                after = int(query.get("after", ["-1"])[0])
                self._sse(after)
                return
            self._json(
                HTTPStatus.NOT_FOUND,
                {"error": "not_found", "path": parsed.path},
            )
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            self._json(
                HTTPStatus.CONFLICT,
                {"error": type(exc).__name__, "message": str(exc)},
            )

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if self._dispatch_review_post(parsed.path):
            return
        self._json(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {
                "error": "read_only",
                "message": "The workspace observatory exposes no write endpoint.",
            },
        )

    def do_PUT(self) -> None:  # noqa: N802
        self._reject_non_post_review_or_observatory()

    def do_PATCH(self) -> None:  # noqa: N802
        self._reject_non_post_review_or_observatory()

    def do_DELETE(self) -> None:  # noqa: N802
        self._reject_non_post_review_or_observatory()

    def log_message(self, format: str, *args: object) -> None:
        # Keep startup demos quiet; callers can wrap the server for access logs.
        return

    def _serve_dashboard(self) -> None:
        if not self.server.dashboard_path.is_file():
            self._json(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "dashboard_not_found",
                    "message": "Generate or supply a dashboard before serving it.",
                },
            )
            return
        content = self.server.dashboard_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: HTTPStatus, payload: Any) -> None:
        content = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def _campaign_payload(self) -> dict[str, Any]:
        workspace = self.server.repository.load()
        return campaign_snapshot(workspace)

    def _dispatch_review_get(self, path: str) -> bool:
        api = self.server.review_api
        if api is None or not api.handles(path):
            return False
        response = api.get(path)
        self._json(response.status, response.payload)
        return True

    def _dispatch_review_post(self, path: str) -> bool:
        api = self.server.review_api
        if api is None or not api.handles(path):
            return False
        preflight = api.preflight_post(
            path,
            self.headers.get("Authorization", ""),
            self.headers.get("Content-Length"),
        )
        if isinstance(preflight, ReviewHTTPResponse):
            self._json(preflight.status, preflight.payload)
            return True
        response = api.post(self.rfile.read(preflight))
        self._json(response.status, response.payload)
        return True

    def _reject_non_post_review_or_observatory(self) -> None:
        path = urlparse(self.path).path
        api = self.server.review_api
        if api is not None and api.handles(path):
            response = api.method_not_allowed()
            self._json(response.status, response.payload)
            return
        self._json(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {
                "error": "read_only",
                "message": "The workspace observatory exposes no write endpoint.",
            },
        )

    def _sse(self, after: int) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        deadline = time.monotonic() + self.server.sse_lifetime_seconds
        cursor = after
        try:
            while time.monotonic() < deadline:
                workspace = self.server.repository.load(force=True)
                fresh = [
                    item for item in workspace.events.events if item.sequence > cursor
                ]
                for event in fresh:
                    payload = json.dumps(
                        event.to_dict(), ensure_ascii=False, sort_keys=True
                    )
                    self.wfile.write(
                        f"id: {event.sequence}\nevent: research_event\ndata: {payload}\n\n".encode(
                            "utf-8"
                        )
                    )
                    self.wfile.flush()
                    cursor = event.sequence
                if not fresh:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                time.sleep(self.server.sse_poll_seconds)
        except (BrokenPipeError, ConnectionResetError):
            return
        finally:
            # The stream has no Content-Length; the client only sees the end
            # of the SSE body if the connection closes when the lifetime ends.
            self.close_connection = True


def make_server(
    workspace_root: str | Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    dashboard_path: str | Path | None = None,
    sse_poll_seconds: float = 0.5,
    sse_lifetime_seconds: float = 30.0,
    review_trace_path: str | Path | None = None,
    review_write_token: str | None = None,
    topic_store_root: str | Path | None = None,
    topic_id: str | None = None,
    topic_initial_cursor: str | None = None,
    local_projection_config: ConsoleLocalProjectionConfig | None = None,
) -> WorkspaceHTTPServer:
    root = Path(workspace_root).resolve()
    topic_args = (topic_store_root, topic_id, topic_initial_cursor)
    if any(value is not None for value in topic_args) and not all(value is not None for value in topic_args):
        raise ValueError("topic_store_root, topic_id, and topic_initial_cursor must be supplied together")
    if topic_store_root is not None and topic_id is not None and topic_initial_cursor is not None:
        topic_store = TopicStoreConfig(
            Path(topic_store_root), topic_id, topic_initial_cursor
        ).open_read_only()
    else:
        topic_store = None
    repository = WorkspaceRepository(root)
    repository.load(force=True)
    dashboard = (
        Path(dashboard_path).resolve()
        if dashboard_path is not None
        else root / "workspace-dashboard.html"
    )
    if (review_trace_path is None) != (review_write_token is None):
        raise ValueError(
            "review_trace_path and review_write_token must be supplied together to enable same-origin review"
        )
    resolved_review_trace_path = Path(review_trace_path).resolve() if review_trace_path is not None else None
    if resolved_review_trace_path == (root / "research-trace.json").resolve():
        raise ValueError(
            "review_trace_path must not target the managed workspace research-trace.json"
        )
    review_api = (
        ReviewAPI(
            ReviewServerConfig(
                trace_path=resolved_review_trace_path, write_token=review_write_token
            )
        )
        if resolved_review_trace_path is not None and review_write_token is not None
        else None
    )
    return WorkspaceHTTPServer(
        (host, port),
        repository,
        dashboard_path=dashboard,
        sse_poll_seconds=sse_poll_seconds,
        sse_lifetime_seconds=sse_lifetime_seconds,
        review_api=review_api,
        topic_store=topic_store,
        local_projection_config=local_projection_config,
    )
