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
from ..review_server import ReviewAPI, ReviewServerConfig
from ..workspace import ResearchWorkspace


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
    ) -> None:
        self.repository = repository
        self.dashboard_path = Path(dashboard_path).resolve()
        self.sse_poll_seconds = sse_poll_seconds
        self.sse_lifetime_seconds = sse_lifetime_seconds
        self.review_api = review_api
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
) -> WorkspaceHTTPServer:
    root = Path(workspace_root).resolve()
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
        if review_trace_path is not None and review_write_token is not None
        else None
    )
    return WorkspaceHTTPServer(
        (host, port),
        repository,
        dashboard_path=dashboard,
        sse_poll_seconds=sse_poll_seconds,
        sse_lifetime_seconds=sse_lifetime_seconds,
        review_api=review_api,
    )


__all__ = [
    "WorkspaceSnapshot",
    "WorkspaceRepository",
    "WorkspaceRequestHandler",
    "WorkspaceHTTPServer",
    "make_server",
]
