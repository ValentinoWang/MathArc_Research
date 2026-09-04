"""Strict read-only observatory API.

The public package overrides the implementation cache: every dashboard, JSON
or SSE poll reloads the workspace and verifies every manifest hash.  This is
more expensive than mtime caching but prevents an attacker from mutating a
non-manifest file while leaving workspace.json unchanged.
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path

from .._workspace_server_impl import WorkspaceHTTPServer as _WorkspaceHTTPServerImpl
from .._workspace_server_impl import WorkspaceRepository as _WorkspaceRepositoryImpl
from .._workspace_server_impl import (
    WorkspaceRequestHandler as _WorkspaceRequestHandlerImpl,
)
from .._workspace_server_impl import WorkspaceSnapshot
from ..access import InvitationAccessStore
from ..access_server import AccessAPI
from ..console_export import ConsoleLocalProjectionConfig
from ..review_server import ReviewAPI, ReviewServerConfig
from ..topic_observation import TopicObservationRunner
from ..workspace import ResearchWorkspace
from ..runtime.run_store import RuntimeStore


class WorkspaceRepository(_WorkspaceRepositoryImpl):
    def load(self, *, force: bool = False) -> ResearchWorkspace:
        return super().load(force=True)


class WorkspaceRequestHandler(_WorkspaceRequestHandlerImpl):
    def _serve_dashboard(self) -> None:
        self.server.repository.load(force=True)
        super()._serve_dashboard()


class WorkspaceHTTPServer(_WorkspaceHTTPServerImpl):
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
        runtime_store: RuntimeStore | None = None,
    ) -> None:
        self.repository = repository
        self.dashboard_path = Path(dashboard_path).resolve()
        self.sse_poll_seconds = sse_poll_seconds
        self.sse_lifetime_seconds = sse_lifetime_seconds
        self.review_api = review_api
        self.topic_store = topic_store
        self.local_projection_config = local_projection_config
        self.access_api = access_api
        self.runtime_store = runtime_store
        from ..runtime.service import ConsoleRuntimeService
        self.runtime_service = ConsoleRuntimeService(
            repository.root,
            access_api=access_api,
            runtime_store=runtime_store,
            local_projection_config=local_projection_config,
        ) if runtime_store is not None else None
        ThreadingHTTPServer.__init__(
            self,
            server_address,
            WorkspaceRequestHandler,
        )


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
    access_cookie_secure: bool = False,
    runtime_store_path: str | Path | None = None,
) -> WorkspaceHTTPServer:
    from ..console_topic import TopicStoreConfig

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
    access_api = (
        AccessAPI(InvitationAccessStore(access_store_root), cookie_secure=access_cookie_secure)
        if access_store_root is not None
        else None
    )
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
        runtime_store=runtime_store,
    )


__all__ = [
    "WorkspaceHTTPServer",
    "WorkspaceRepository",
    "WorkspaceRequestHandler",
    "WorkspaceSnapshot",
    "make_server",
]
