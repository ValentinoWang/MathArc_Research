"""HTTP write path for the expert review workflow (v0.3-review R6).

Scope decision, made explicit rather than silently narrowed (spelled out
fully in the traceability doc): the spec text lines R6 up with W4-3's
server integration ("与 W4-3 服务器整合同步"), and W4-3 (the multi-run
workspace server) does not exist. `_workspace_server_impl.py`'s
`WorkspaceHTTPServer` is shaped around `ResearchWorkspace` (object
registry, source registry, `EventLedger`, a commit/audit state machine
this session has not fully internalized well enough to extend safely
under time pressure). Rather than risk a subtly broken write path against
that state machine, this server stays at the same bare-`ResearchTrace`
layer R0-R4 already established and R3's CLI already uses -- it is a
second transport (HTTP) over the identical library calls the CLI makes,
not a new authority. True `ResearchWorkspace`/`EventLedger` integration
remains real future work once W4-3 exists, exactly as the spec's own
dependency line already anticipates.

Endpoints:
  POST /api/review        -- submit a ReviewRecord. Bearer roster token,
                              constant-time compared, 64KB body cap.
  GET  /api/review-queue  -- read-only: every nomination and whether it
                              already has a covering ACTIVE review.
  GET  /api/review-bundle/{claim_id} -- read-only: a view model, not the
                              domain ReviewBundle -- every backend enum
                              value is mapped to a Chinese label before
                              the response leaves this module.

All GET endpoints require no authentication (read access matches the
existing workspace observatory's own posture); the one write endpoint is
the only one gated at all, matching "唯一带鉴权写端点".
"""

from __future__ import annotations

import hmac
import json
import fcntl
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

from .review import (
    NominationError,
    ReviewAuthorizationError,
    ReviewContractError,
    ReviewDecision,
    ReviewRecord,
    all_nominations,
    review_to_evidence,
    reviews_for_claim,
    submit_review,
)
from .review_bundle import ReviewBundleError, RequiredAssurance, build_review_bundle
from .trace import ResearchTrace, load_trace, save_trace

_MAX_BODY_BYTES = 64 * 1024
_TRACE_LOCKS_GUARD = threading.Lock()
_TRACE_LOCKS: dict[Path, threading.RLock] = {}


def _local_trace_lock(path: Path) -> threading.RLock:
    """Return the one process-local lock for a canonical trace path."""

    with _TRACE_LOCKS_GUARD:
        return _TRACE_LOCKS.setdefault(path, threading.RLock())


@contextmanager
def _locked_trace(path: Path) -> Iterator[None]:
    """Serialize every review transaction for a trace across APIs/processes.

    Lock a stable sibling, never the trace itself: ``save_trace`` replaces the
    trace inode atomically.  The in-process lock covers same-process APIs and
    ``flock`` covers separately started review servers.
    """

    canonical = path.resolve()
    lock_path = canonical.with_name(f".{canonical.name}.review.lock")
    with _local_trace_lock(canonical):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

_EVIDENCE_KIND_VM: dict[str, str] = {
    "FORMAL_PROOF": "形式化证明",
    "CHECKED_DERIVATION": "经检查的推导",
    "EXACT_CERTIFICATE": "精确证书（含独立复核）",
    "EXACT_COMPUTATION": "精确计算（自校验）",
    "COUNTEREXAMPLE": "反例",
    "LITERATURE_RESULT": "引用外部文献",
    "HUMAN_AUDIT": "专家人工审核",
    "NUMERICAL_EXPERIMENT": "数值实验",
    "HEURISTIC": "启发式判断",
}
_EVIDENCE_STATUS_VM: dict[str, str] = {
    "PROPOSED": "已提出，未采信",
    "ACCEPTED": "已采信",
    "REJECTED": "已拒绝",
    "STALE": "已失效",
}
_CLAIM_STATUS_VM: dict[str, str] = {
    "PROPOSED": "已提出",
    "OPEN": "研究中",
    "CANDIDATE": "候选，待评审",
    "PROVED": "已证明",
    "REFUTED": "已否证",
    "BLOCKED": "被阻塞",
    "RETRACTED": "已撤回",
}
_REQUIRED_ASSURANCE_VM: dict[str, str] = {
    RequiredAssurance.MACHINE_SUFFICIENT.value: "机器判定即可",
    RequiredAssurance.HUMAN_SINGLE.value: "需一名评审人判断",
    RequiredAssurance.HUMAN_DOUBLE.value: "需两名独立评审人分别判断",
}


class ReviewServerError(ValueError):
    """Raised for a malformed server configuration."""


@dataclass(slots=True, frozen=True)
class ReviewHTTPResponse:
    """Transport-neutral response for the single review API contract."""

    status: HTTPStatus
    payload: dict[str, Any]


def bundle_view_model(bundle: Any) -> dict[str, Any]:
    """Transform a domain `ReviewBundle` into a response with no unmapped
    backend enum names anywhere in it -- the R6 acceptance criterion."""

    def evidence_row(item: dict[str, Any]) -> dict[str, Any]:
        kind = str(item.get("kind", ""))
        status = str(item.get("status", ""))
        return {
            "evidence_id": item.get("evidence_id"),
            "kind_label": _EVIDENCE_KIND_VM.get(kind, "其他证据类型"),
            "status_label": _EVIDENCE_STATUS_VM.get(status, "状态未知"),
            "summary": item.get("summary", ""),
            "producer": item.get("producer", ""),
            "verifier": item.get("verifier", ""),
            "replayable_command": item.get("replay_command", ""),
            "digest_sha256": item.get("digest_sha256", ""),
        }

    def dependency_row(item: dict[str, Any]) -> dict[str, Any]:
        status = str(item.get("status", ""))
        return {
            "claim_id": item.get("claim_id"),
            "statement": item.get("statement", ""),
            "status_label": _CLAIM_STATUS_VM.get(status, "状态未知"),
        }

    def obligation_row(item: Any) -> dict[str, Any]:
        required = item.required_assurance.value
        return {
            "obligation_id": item.obligation_id,
            "title": item.title,
            "ask": item.ask,
            "points": list(item.points),
            "ref": item.ref,
            "required_assurance_label": _REQUIRED_ASSURANCE_VM.get(required, required),
        }

    def attack_row(item: Any) -> dict[str, Any]:
        return {"summary": item.summary, "emphasis": list(item.emphasis)}

    return {
        "claim_id": bundle.claim_id,
        "claim_revision": bundle.claim_revision,
        "statement": bundle.statement,
        "scope": bundle.scope,
        "boundary": bundle.boundary,
        "bundle_digest_sha256": bundle.bundle_digest_sha256,
        "dependency_path": [dependency_row(item) for item in bundle.dependency_path],
        "evidence": [evidence_row(item) for item in bundle.evidence],
        "obligations": [obligation_row(item) for item in bundle.obligations],
        "attack_history": [attack_row(item) for item in bundle.attack_history],
    }


@dataclass(slots=True)
class ReviewServerConfig:
    trace_path: Path
    write_token: str

    def __post_init__(self) -> None:
        self.trace_path = Path(self.trace_path).resolve()
        if not self.write_token or len(self.write_token) < 16:
            raise ReviewServerError(
                "write_token must be a real secret of at least 16 characters, "
                "not a default or empty placeholder"
            )


class ReviewAPI:
    """The review HTTP contract, reusable by a dedicated or same-origin server.

    The review trace remains a distinct authority from a workspace snapshot.
    A host that wants the endpoints must opt in by constructing this API with
    the exact review trace path and a real roster token.
    """

    def __init__(self, config: ReviewServerConfig) -> None:
        self.config = config

    @staticmethod
    def handles(path: str) -> bool:
        return path in {"/api/review", "/api/review-queue"} or path.startswith(
            "/api/review-bundle/"
        )

    def load_trace_locked(self) -> ResearchTrace:
        with _locked_trace(self.config.trace_path):
            return load_trace(self.config.trace_path)

    def mutate_and_save(self, fn: Any) -> Any:
        """Serialize read-modify-write so submissions cannot lose updates."""

        with _locked_trace(self.config.trace_path):
            trace = load_trace(self.config.trace_path)
            result = fn(trace)
            save_trace(trace, self.config.trace_path)
            return result

    def get(self, path: str) -> ReviewHTTPResponse:
        try:
            if path == "/api/review":
                return self.method_not_allowed()
            if path == "/api/review-queue":
                return self._review_queue()
            if path.startswith("/api/review-bundle/"):
                return self._review_bundle(path[len("/api/review-bundle/") :])
            return ReviewHTTPResponse(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            return ReviewHTTPResponse(
                HTTPStatus.CONFLICT,
                {"error": type(exc).__name__, "message": str(exc)},
            )

    def preflight_post(
        self, path: str, authorization: str, content_length: str | None
    ) -> int | ReviewHTTPResponse:
        if path != "/api/review":
            return self.method_not_allowed()
        if not self._authorized(authorization):
            return ReviewHTTPResponse(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
        try:
            length = int(content_length or "0")
        except ValueError:
            return ReviewHTTPResponse(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_length", "max_bytes": _MAX_BODY_BYTES},
            )
        if length <= 0 or length > _MAX_BODY_BYTES:
            return ReviewHTTPResponse(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE if length > _MAX_BODY_BYTES else HTTPStatus.BAD_REQUEST,
                {"error": "invalid_length", "max_bytes": _MAX_BODY_BYTES},
            )
        return length

    def post(self, body: bytes) -> ReviewHTTPResponse:
        try:
            payload = json.loads(body.decode("utf-8"))
            record = ReviewRecord.from_dict(payload)
        except (json.JSONDecodeError, ReviewContractError, UnicodeDecodeError) as exc:
            return ReviewHTTPResponse(
                HTTPStatus.BAD_REQUEST,
                {"error": "malformed_review", "message": str(exc)},
            )

        def submit(trace: ResearchTrace) -> dict[str, Any]:
            submit_review(trace, record)
            result: dict[str, Any] = {
                "submitted": True,
                "review_id": record.review_id,
                "decision": record.overall_decision.value,
            }
            if record.overall_decision is ReviewDecision.APPROVE:
                evidence_id = f"EV-REVIEW-{record.review_id}"
                evidence = review_to_evidence(
                    trace,
                    record.review_id,
                    evidence_id=evidence_id,
                    artifact_uri=f"review-record:{record.review_id}",
                )
                trace.add_evidence(evidence)
                result["evidence_id"] = evidence_id
            return result

        try:
            return ReviewHTTPResponse(HTTPStatus.OK, self.mutate_and_save(submit))
        except (ReviewContractError, ReviewAuthorizationError) as exc:
            return ReviewHTTPResponse(
                HTTPStatus.CONFLICT,
                {"error": type(exc).__name__, "message": str(exc)},
            )

    @staticmethod
    def method_not_allowed() -> ReviewHTTPResponse:
        return ReviewHTTPResponse(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {"error": "method_not_allowed", "message": "only POST /api/review writes anything"},
        )

    def _authorized(self, authorization: str) -> bool:
        prefix = "Bearer "
        token = authorization[len(prefix) :] if authorization.startswith(prefix) else ""
        return bool(token) and hmac.compare_digest(token, self.config.write_token)

    def _review_queue(self) -> ReviewHTTPResponse:
        trace = self.load_trace_locked()
        rows = []
        for nomination in all_nominations(trace):
            claim = trace.claims.get(nomination.claim_id)
            active_reviews = [
                item
                for item in reviews_for_claim(trace, nomination.claim_id)
                if item.lifecycle_status.value == "ACTIVE"
                and claim is not None
                and item.claim_revision == claim.revision
            ]
            rows.append(
                {
                    "claim_id": nomination.claim_id,
                    "nomination_id": nomination.nomination_id,
                    "claim_revision": nomination.claim_revision,
                    "has_active_review": bool(active_reviews),
                    "active_review_count": len(active_reviews),
                }
            )
        return ReviewHTTPResponse(HTTPStatus.OK, {"queue": rows})

    def _review_bundle(self, claim_id: str) -> ReviewHTTPResponse:
        trace = self.load_trace_locked()
        try:
            bundle = build_review_bundle(trace, claim_id, bundle_id=f"live:{claim_id}")
        except ReviewBundleError as exc:
            return ReviewHTTPResponse(
                HTTPStatus.NOT_FOUND,
                {"error": "unknown_claim", "message": str(exc)},
            )
        return ReviewHTTPResponse(HTTPStatus.OK, bundle_view_model(bundle))


class ReviewHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int], config: ReviewServerConfig) -> None:
        self.config = config
        self.api = ReviewAPI(config)
        super().__init__(server_address, ReviewRequestHandler)

    def load_trace_locked(self) -> ResearchTrace:
        return self.api.load_trace_locked()

    def mutate_and_save(self, fn: Any) -> Any:
        """Run `fn(trace) -> result` under the write lock and persist the
        trace afterward, exactly once, so two concurrent submissions can
        never interleave a lost update."""

        return self.api.mutate_and_save(fn)


class ReviewRequestHandler(BaseHTTPRequestHandler):
    server: ReviewHTTPServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        response = self.server.api.get(parsed.path)
        self._json(response.status, response.payload)

    def do_PUT(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def _method_not_allowed(self) -> None:
        response = self.server.api.method_not_allowed()
        self._json(response.status, response.payload)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        preflight = self.server.api.preflight_post(
            parsed.path,
            self.headers.get("Authorization", ""),
            self.headers.get("Content-Length"),
        )
        if isinstance(preflight, ReviewHTTPResponse):
            self._json(preflight.status, preflight.payload)
            return
        response = self.server.api.post(self.rfile.read(preflight))
        self._json(response.status, response.payload)

    def _json(self, status: HTTPStatus, payload: Any) -> None:
        content = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)


def make_review_server(
    trace_path: str | Path,
    *,
    write_token: str,
    host: str = "127.0.0.1",
    port: int = 0,
) -> ReviewHTTPServer:
    config = ReviewServerConfig(trace_path=Path(trace_path).resolve(), write_token=write_token)
    return ReviewHTTPServer((host, port), config)
