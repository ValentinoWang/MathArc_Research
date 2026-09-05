from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .access import (
    AccessStateError,
    AccessValidationError,
    InvalidCredentialsError,
    InvitationAccessStore,
)
from .access_server import AccessAPI, AccessHTTPResponse
from .admin_server import AdminAPI, AdminHTTPResponse
from .console_export import ConsoleLocalProjectionConfig, build_console_export, campaign_snapshot
from .console_topic import TopicStoreConfig
from .review_server import ReviewAPI, ReviewHTTPResponse, ReviewServerConfig
from .runtime.contracts import ResearchRunSpec
from .runtime.run_store import RuntimeStore, RuntimeStoreError
from .runtime.service import ActionConflictError, ConsoleRuntimeService, PermissionDeniedError
from .runtime.view_model import redact_payload
from .topic_observation import TopicObservationRunner
from .workspace import ResearchWorkspace
from .workspace_visualization import workspace_dashboard_payload


class _HandledRequest(Exception):
    """Internal control flow after an HTTP error has been written."""


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
        access_api: AccessAPI | None = None,
        admin_api: AdminAPI | None = None,
        admin_dashboard_path: str | Path | None = None,
        runtime_store: RuntimeStore | None = None,
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
        self.access_api = access_api
        self.admin_api = admin_api
        self.admin_dashboard_path = Path(admin_dashboard_path).resolve() if admin_dashboard_path else None
        self.runtime_store = runtime_store
        self.runtime_service = ConsoleRuntimeService(
            repository.root,
            access_api=access_api,
            runtime_store=runtime_store,
            local_projection_config=local_projection_config,
        ) if runtime_store is not None else None
        super().__init__(server_address, WorkspaceRequestHandler)


class WorkspaceRequestHandler(BaseHTTPRequestHandler):
    server: WorkspaceHTTPServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if self._dispatch_admin_get(parsed.path, parse_qs(parsed.query)):
                return
            if self._dispatch_access_get(parsed.path):
                return
            if self._access_required(parsed.path) and not self._require_access_session():
                return
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
            if parsed.path == "/api/runtime/snapshot":
                self._runtime_required()
                query = parse_qs(parsed.query)
                snapshot = self.server.runtime_service.snapshot(
                    self.headers.get("Cookie", ""),
                    runtime_run_id=query.get("run_id", [None])[0],
                )
                self._json(HTTPStatus.OK, snapshot.to_dict())
                return
            if parsed.path == "/api/runtime/events":
                self._runtime_required()
                query = parse_qs(parsed.query)
                after = int(query.get("after", ["-1"])[0])
                store = self.server.runtime_store
                assert store is not None
                run_id = self._runtime_run_id(query.get("run_id", [None])[0])
                target_events = [
                    event for event in store.events
                    if event.payload.get("runtime_run_id") == run_id
                ]
                tail = max(0, max((event.sequence for event in target_events), default=-1))
                if after < -1 or after > tail:
                    self._json(HTTPStatus.CONFLICT, {"error": "reload_required", "reason": "cursor_out_of_range", "run_id": run_id, "cursor": tail})
                    return
                self._json(HTTPStatus.OK, {
                    "run_id": run_id, "after": after, "cursor": tail,
                    "events": [redact_payload(event.to_dict()) for event in target_events if event.sequence > after],
                    "head_hash": store.head_hash,
                })
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
        except _HandledRequest:
            return
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            self._json(
                HTTPStatus.CONFLICT,
                {"error": type(exc).__name__, "message": str(exc)},
            )

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if self._dispatch_admin_post(parsed.path):
            return
        if self._dispatch_access_post(parsed.path):
            return
        if self._access_required(parsed.path) and not self._require_access_session():
            return
        if self._dispatch_review_post(parsed.path):
            return
        if parsed.path == "/api/runtime/runs":
            self._runtime_create_run()
            return
        if parsed.path.startswith("/api/runtime/runs/") and parsed.path.endswith("/actions"):
            self._runtime_action(parsed.path)
            return
        self._json(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {
                "error": "read_only",
                "message": "The workspace observatory exposes no write endpoint.",
            },
        )

    def do_PUT(self) -> None:
        self._reject_non_post_review_or_observatory()

    def do_PATCH(self) -> None:
        self._reject_non_post_review_or_observatory()

    def do_DELETE(self) -> None:
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

    def _json(
        self,
        status: HTTPStatus,
        payload: Any,
        *,
        headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        content = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(content)

    def _empty(self, status: HTTPStatus, *, headers: tuple[tuple[str, str], ...] = ()) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()

    def _dispatch_access_get(self, path: str) -> bool:
        api = self.server.access_api
        if api is None or not api.handles(path):
            return False
        self._access_response(api.get(path, self.headers.get("Cookie", "")))
        return True

    def _dispatch_admin_get(self, path: str, query: dict[str, list[str]] | None = None) -> bool:
        api = self.server.admin_api
        if api is None or not api.handles(path):
            return False
        if path in {"/admin", "/admin/"}:
            response = api.get(path, self.headers, query)
            if response.status != HTTPStatus.OK:
                self._admin_response(response)
                return True
            dashboard = self.server.admin_dashboard_path
            if dashboard is None or not dashboard.is_file():
                self._json(HTTPStatus.NOT_FOUND, {"error": "admin_dashboard_not_found"})
                return True
            content = dashboard.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
            return True
        self._admin_response(api.get(path, self.headers, query))
        return True

    def _dispatch_admin_post(self, path: str) -> bool:
        api = self.server.admin_api
        if api is None or not api.handles(path):
            return False
        content_length = self.headers.get("Content-Length")
        try:
            length = int(content_length or "0")
        except ValueError:
            length = 0
        body = self.rfile.read(length) if 0 < length <= 32 * 1024 else b""
        self._admin_response(api.post(path, headers=self.headers, body=body))
        return True

    def _admin_response(self, response: AdminHTTPResponse) -> None:
        if response.payload is None:
            self._empty(response.status, headers=response.headers)
        else:
            self._json(response.status, response.payload, headers=response.headers)

    def _dispatch_access_post(self, path: str) -> bool:
        api = self.server.access_api
        if api is None or not api.handles(path):
            return False
        content_length = self.headers.get("Content-Length")
        try:
            length = int(content_length or "0")
        except ValueError:
            length = 0
        body = self.rfile.read(length) if 0 < length <= 32 * 1024 else b""
        self._access_response(
            api.post(
                path,
                content_type=self.headers.get("Content-Type", ""),
                content_length=content_length,
                body=body,
                cookie_header=self.headers.get("Cookie", ""),
            )
        )
        return True

    def _access_response(self, response: AccessHTTPResponse) -> None:
        if response.payload is None:
            self._empty(response.status, headers=response.headers)
            return
        self._json(response.status, response.payload, headers=response.headers)

    def _access_required(self, path: str) -> bool:
        if self.server.access_api is None:
            return False
        return path in {
            "/api/workspace",
            "/api/campaign",
            "/api/console",
            "/api/audit",
            "/api/events",
            "/api/artifacts",
            "/events",
        } or path == "/api/runtime/snapshot" or path == "/api/runtime/events" \
            or path == "/api/runtime/runs" or (path.startswith("/api/runtime/runs/") and path.endswith("/actions")) \
            or (self.server.review_api is not None and self.server.review_api.handles(path))

    def _runtime_required(self, *, operation: bool = False) -> Any:
        if self.server.runtime_service is None:
            self._json(HTTPStatus.NOT_FOUND, {"error": "runtime_not_configured"})
            raise _HandledRequest
        if self.server.access_api is not None:
            try:
                return self.server.runtime_service._authorize(self.headers.get("Cookie", ""), require_runtime=operation)
            except PermissionDeniedError as exc:
                self._json(HTTPStatus.FORBIDDEN, {"error": "permission_denied", "message": str(exc)})
                raise _HandledRequest

    def _runtime_run_id(self, requested: str | None = None) -> str | None:
        store = self.server.runtime_store
        if store is None:
            return None
        runs = store.state.get("runs", {})
        if requested is not None:
            if requested not in runs:
                raise ValueError("runtime_run_id is not present in runtime store")
            return requested
        if len(runs) == 1:
            return next(iter(runs), None)
        return min(runs) if runs else None

    def _read_json_body(self) -> dict[str, Any]:
        content_length = self.headers.get("Content-Length")
        try:
            length = int(content_length or "0")
        except ValueError as exc:
            raise ValueError("Content-Length is invalid") from exc
        if length <= 0 or length > 32 * 1024:
            raise ValueError("request body must contain 1 to 32768 bytes")
        if self.headers.get("Content-Type", "").partition(";")[0].strip().casefold() != "application/json":
            raise ValueError("Content-Type must be application/json")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise TypeError("request body must be a JSON object")
        return value

    def _runtime_create_run(self) -> None:
        try:
            session = self._runtime_required(operation=True)
            payload = self._read_json_body()
            spec = ResearchRunSpec.from_dict(payload)
            store = self.server.runtime_store
            assert store is not None
            run = store.create_run(spec)
            actor = session.email if session is not None else "console"
            self.server.runtime_service.create_run(spec.runtime_run_id, cookie_header=self.headers.get("Cookie", ""), actor=actor)
            self._json(HTTPStatus.CREATED, {"run": run})
        except _HandledRequest:
            return
        except PermissionDeniedError as exc:
            self._json(HTTPStatus.FORBIDDEN, {"error": "permission_denied", "message": str(exc)})
        except (ValueError, TypeError, RuntimeStoreError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_runtime_run", "message": str(exc)})

    def _runtime_action(self, path: str) -> None:
        try:
            session = self._runtime_required(operation=True)
            parts = path.split("/")
            runtime_run_id = parts[-2]
            if not runtime_run_id or "/" in runtime_run_id:
                raise ValueError("runtime_run_id is required")
            payload = self._read_json_body()
            allowed = {"action_id", "action", "actor", "payload"}
            unknown = set(payload) - allowed
            if unknown:
                raise ValueError(f"unknown runtime action fields: {sorted(unknown)}")
            action_id, action = payload.get("action_id"), payload.get("action")
            if not isinstance(action_id, str) or not action_id.strip() or not isinstance(action, str):
                raise ValueError("action_id and action are required")
            store = self.server.runtime_store
            service = self.server.runtime_service
            assert store is not None and service is not None
            prior = next((event.payload for event in store.events if event.event_type == "RUN_ACTION" and event.payload.get("runtime_run_id") == runtime_run_id and event.payload.get("action_id") == action_id), None)
            run = store.state.get("runs", {}).get(runtime_run_id)
            if run is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "runtime_run_not_found"})
                return
            actor = str(payload.get("actor") or (session.email if session is not None else "console"))
            receipt = service.runtime_action(runtime_run_id, action, action_id=action_id, actor=actor, cookie_header=self.headers.get("Cookie", ""), payload=payload.get("payload") or {})
            data = receipt.to_dict() if hasattr(receipt, "to_dict") else dict(receipt.payload or {})
            self._json(HTTPStatus.OK, {"receipt": data, "replayed": prior is not None})
        except _HandledRequest:
            return
        except PermissionDeniedError as exc:
            self._json(HTTPStatus.FORBIDDEN, {"error": "permission_denied", "message": str(exc)})
        except ActionConflictError as exc:
            self._json(HTTPStatus.CONFLICT, {"error": "action_conflict", "message": str(exc)})
        except (ValueError, TypeError, RuntimeStoreError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_runtime_action", "message": str(exc)})

    def _require_access_session(self) -> bool:
        api = self.server.access_api
        if api is None:
            return True
        try:
            api.authenticate(self.headers.get("Cookie", ""))
            return True
        except (InvalidCredentialsError, AccessValidationError):
            self._json(
                HTTPStatus.UNAUTHORIZED,
                {"error": "access_required", "message": "需要有效的研究预览会话。"},
            )
        except AccessStateError:
            self._json(
                HTTPStatus.CONFLICT,
                {"error": "access_state_invalid", "message": "访问状态暂时无法验证。"},
            )
        return False

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
        if self._access_required(path) and not self._require_access_session():
            return
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
                        f"id: {event.sequence}\nevent: research_event\ndata: {payload}\n\n".encode()
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
    access_store_root: str | Path | None = None,
    access_api: AccessAPI | None = None,
    access_cookie_secure: bool = False,
    admin_api: AdminAPI | None = None,
    admin_dashboard_path: str | Path | None = None,
    runtime_store_path: str | Path | None = None,
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
    if access_api is None and access_store_root is not None:
        access_api = AccessAPI(InvitationAccessStore(access_store_root), cookie_secure=access_cookie_secure)
    runtime_store = RuntimeStore(runtime_store_path or (root / ".runtime-store"))
    return WorkspaceHTTPServer(
        (host, port),
        repository,
        dashboard_path=dashboard,
        sse_poll_seconds=sse_poll_seconds,
        sse_lifetime_seconds=sse_lifetime_seconds,
        review_api=review_api,
        topic_store=topic_store,
        local_projection_config=local_projection_config,
        access_api=access_api,
        admin_api=admin_api,
        admin_dashboard_path=admin_dashboard_path,
        runtime_store=runtime_store,
    )
