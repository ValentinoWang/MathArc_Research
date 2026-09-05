"""HTTP adapter for the reverse-proxy-authenticated administrator API."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from .admin_auth import (
    AdminAuthError,
    AdminIdentityError,
    UntrustedProxyError,
    require_admin_identity,
    require_role,
)
from .admin_service import (
    AdminConflictError,
    AdminNotFoundError,
    AdminService,
    AdminServiceError,
    AdminStateError,
    AdminValidationError,
)


@dataclass(frozen=True, slots=True)
class AdminHTTPResponse:
    status: HTTPStatus
    payload: dict[str, Any] | None
    headers: tuple[tuple[str, str], ...] = ()


class AdminAPI:
    """Transport boundary; proxy identity is the only administrator credential."""

    def __init__(self, service: AdminService, *, trusted_proxy: bool = False) -> None:
        self.service = service
        self.trusted_proxy = trusted_proxy

    @staticmethod
    def handles(path: str) -> bool:
        return path == "/admin" or path == "/admin/" or path.startswith("/api/admin/")

    def get(self, path: str, headers: Mapping[str, Any], query: Mapping[str, list[str]] | None = None) -> AdminHTTPResponse:
        try:
            identity = require_admin_identity(headers, trusted_proxy=self.trusted_proxy)
            if path in {"/admin", "/admin/"}:
                return AdminHTTPResponse(HTTPStatus.OK, None, (("X-Admin-Page", "enabled"),))
            if path == "/api/admin/me":
                return AdminHTTPResponse(HTTPStatus.OK, {"admin": identity.to_dict()})
            if path == "/api/admin/applications":
                params = query or {}
                limit = _page_limit(params)
                page = _page_number(params)
                status = _query_one(params, "status")
                search = _query_one(params, "q")
                items = self.service.list_applications(
                    identity,
                    limit=limit,
                    offset=(page - 1) * limit,
                    status=status,
                    search=search,
                )
                total = self.service.count_applications(identity, status=status, search=search)
                return AdminHTTPResponse(HTTPStatus.OK, {"items": items, "page": page, "page_size": limit, "total": total})
            if path.startswith("/api/admin/applications/"):
                application_id = path[len("/api/admin/applications/"):].strip("/")
                items = self.service.list_applications(identity, limit=1000)
                item = next((entry for entry in items if entry.get("application_id") == application_id), None)
                return self._not_found() if item is None else AdminHTTPResponse(HTTPStatus.OK, {"application": item})
            if path == "/api/admin/invitations":
                params = query or {}
                limit = _page_limit(params)
                page = _page_number(params)
                status = _query_one(params, "status")
                search = _query_one(params, "q")
                items = [
                    item.to_dict()
                    for item in self.service.list_invitations(
                        identity,
                        limit=limit,
                        offset=(page - 1) * limit,
                        status=status,
                        search=search,
                    )
                ]
                total = self.service.count_invitations(identity, status=status, search=search)
                return AdminHTTPResponse(HTTPStatus.OK, {"items": items, "page": page, "page_size": limit, "total": total})
            if path == "/api/admin/access-sessions":
                params = query or {}
                status = _query_one(params, "status")
                items = self.service.list_access_sessions(identity, status=status)
                return AdminHTTPResponse(HTTPStatus.OK, {"items": items, "page": 1, "page_size": len(items), "total": len(items)})
            if path == "/api/admin/audit":
                return AdminHTTPResponse(HTTPStatus.OK, {"items": [item.to_dict() for item in self.service.audit_events(identity)]})
            return self._not_found()
        except AdminAuthError as exc:
            return self._auth_error(exc)
        except AdminServiceError as exc:
            return self._service_error(exc)

    def post(self, path: str, *, headers: Mapping[str, Any], body: bytes) -> AdminHTTPResponse:
        if path == "/api/admin/auth/login":
            return AdminHTTPResponse(HTTPStatus.UNAUTHORIZED, {"error": "proxy_auth_required", "message": "管理员身份由反向代理提供。"})
        try:
            identity = require_admin_identity(headers, trusted_proxy=self.trusted_proxy)
            if path == "/api/admin/auth/logout":
                return AdminHTTPResponse(HTTPStatus.NO_CONTENT, None)
            payload = self._decode_json(body)
            if path == "/api/admin/invitations":
                unknown = set(payload) - {"email", "topic_scopes", "ttl_seconds", "expires_in_seconds"}
                if unknown:
                    raise AdminValidationError("unknown invitation fields")
                key = self._idempotency_key(headers)
                grant = self.service.issue_invitation(identity, email=payload["email"], topic_scopes=payload["topic_scopes"], ttl_seconds=payload.get("ttl_seconds", payload.get("expires_in_seconds")), idempotency_key=key)
                result = grant.to_dict()
                result["one_time"] = True
                return AdminHTTPResponse(HTTPStatus.CREATED, result)
            if path.startswith("/api/admin/invitations/") and path.endswith("/revoke"):
                invitation_id = path[len("/api/admin/invitations/"):-len("/revoke")].rstrip("/")
                if set(payload) != {"reason"}:
                    raise AdminValidationError("reason is required")
                revoke_result = self.service.revoke_invitation(
                    identity,
                    invitation_id,
                    reason=payload["reason"],
                    idempotency_key=self._idempotency_key(headers),
                )
                return AdminHTTPResponse(HTTPStatus.OK, {"invitation": revoke_result.to_dict()})
            if path.startswith("/api/admin/access-sessions/") and path.endswith("/revoke"):
                require_role(identity, {"security_admin"})
                prefix = "/api/admin/access-sessions/"
                session_id = path[len(prefix):-len("/revoke")].rstrip("/")
                self.service.revoke_session(identity, session_id, idempotency_key=self._idempotency_key(headers))
                return AdminHTTPResponse(HTTPStatus.NO_CONTENT, None)
            return self._not_found()
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return AdminHTTPResponse(HTTPStatus.BAD_REQUEST, {"error": "invalid_request", "message": str(exc)})
        except AdminAuthError as exc:
            return self._auth_error(exc)
        except AdminServiceError as exc:
            return self._service_error(exc)

    @staticmethod
    def _decode_json(body: bytes) -> dict[str, Any]:
        if not body or len(body) > 32 * 1024:
            raise AdminValidationError("request body must contain 1 to 32768 bytes")
        value = json.loads(body.decode("utf-8"))
        if not isinstance(value, dict):
            raise AdminValidationError("request body must be an object")
        return value

    @staticmethod
    def _idempotency_key(headers: Mapping[str, Any]) -> str:
        value = headers.get("Idempotency-Key") or headers.get("idempotency-key")
        if not isinstance(value, str) or not value.strip():
            raise AdminValidationError("idempotency_key is required")
        return value.strip()

    @staticmethod
    def _unauthorized() -> AdminHTTPResponse:
        return AdminHTTPResponse(HTTPStatus.UNAUTHORIZED, {"error": "admin_auth_required"})

    @staticmethod
    def _auth_error(error: AdminAuthError) -> AdminHTTPResponse:
        if isinstance(error, (AdminIdentityError, UntrustedProxyError)):
            return AdminAPI._unauthorized()
        return AdminHTTPResponse(HTTPStatus.FORBIDDEN, {"error": "forbidden"})

    @staticmethod
    def _not_found() -> AdminHTTPResponse:
        return AdminHTTPResponse(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    @staticmethod
    def _service_error(error: AdminServiceError) -> AdminHTTPResponse:
        if isinstance(error, AdminNotFoundError):
            return AdminHTTPResponse(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        if isinstance(error, AdminConflictError):
            return AdminHTTPResponse(HTTPStatus.CONFLICT, {"error": "conflict", "message": str(error)})
        if isinstance(error, AdminValidationError):
            return AdminHTTPResponse(HTTPStatus.BAD_REQUEST, {"error": "invalid_request", "message": str(error)})
        if isinstance(error, AdminStateError):
            return AdminHTTPResponse(HTTPStatus.CONFLICT, {"error": "admin_state_invalid"})
        return AdminHTTPResponse(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "admin_service_unavailable"})


__all__ = ["AdminAPI", "AdminHTTPResponse"]


def _query_one(query: Mapping[str, list[str]], key: str) -> str | None:
    values = query.get(key, [])
    return values[0].strip() if values and values[0].strip() else None


def _page_number(query: Mapping[str, list[str]]) -> int:
    try:
        value = int(_query_one(query, "page") or "1")
    except ValueError:
        return 1
    return max(1, value)


def _page_limit(query: Mapping[str, list[str]]) -> int:
    try:
        value = int(_query_one(query, "page_size") or "25")
    except ValueError:
        return 25
    return min(1000, max(1, value))
