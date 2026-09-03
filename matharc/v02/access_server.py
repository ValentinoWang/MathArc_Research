"""HTTP adapter for invitation-based research preview access."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from typing import Any

from .access import (
    AccessStateError,
    AccessValidationError,
    InvalidCredentialsError,
    InvitationAccessStore,
    SessionView,
)

ACCESS_COOKIE_NAME = "matharc_access_session"
_MAX_BODY_BYTES = 32 * 1024
_APPLICATION_FIELDS = {
    "email",
    "institution",
    "research_role",
    "research_direction",
    "purpose",
}
_REDEEM_FIELDS = {"email", "code"}


@dataclass(frozen=True, slots=True)
class AccessHTTPResponse:
    status: HTTPStatus
    payload: dict[str, Any] | None
    headers: tuple[tuple[str, str], ...] = ()


class AccessAPI:
    """Transport-neutral access endpoint contract.

    Invitation issuance is deliberately absent: codes are administrative
    secrets and are never minted by the public preview server.
    """

    def __init__(
        self,
        store: InvitationAccessStore,
        *,
        cookie_secure: bool = False,
    ) -> None:
        self.store = store
        self.cookie_secure = cookie_secure

    @staticmethod
    def handles(path: str) -> bool:
        return path in {
            "/api/access/applications",
            "/api/access/redeem",
            "/api/access/session",
            "/api/access/logout",
        }

    def get(self, path: str, cookie_header: str) -> AccessHTTPResponse:
        if path != "/api/access/session":
            return self.method_not_allowed()
        try:
            session = self.authenticate(cookie_header)
        except (InvalidCredentialsError, AccessValidationError):
            return self._invalid_credentials()
        except AccessStateError:
            return self._state_invalid()
        return AccessHTTPResponse(
            HTTPStatus.OK,
            {"authenticated": True, "session": session.to_dict()},
        )

    def post(
        self,
        path: str,
        *,
        content_type: str,
        content_length: str | None,
        body: bytes,
        cookie_header: str,
    ) -> AccessHTTPResponse:
        if path == "/api/access/logout":
            return self._logout(cookie_header)
        if path not in {"/api/access/applications", "/api/access/redeem"}:
            return self.method_not_allowed()
        try:
            payload = self._decode_json(content_type, content_length, body)
            if path == "/api/access/applications":
                self._require_fields(payload, _APPLICATION_FIELDS)
                application = self.store.submit_application(**payload)
                return AccessHTTPResponse(
                    HTTPStatus.ACCEPTED,
                    {"application": application.to_dict()},
                )
            self._require_fields(payload, _REDEEM_FIELDS)
            token, session = self.store.redeem(
                email=payload["email"],
                code=payload["code"],
            )
            return AccessHTTPResponse(
                HTTPStatus.OK,
                {"authenticated": True, "session": session.to_dict()},
                (("Set-Cookie", self._session_cookie(token, session)),),
            )
        except InvalidCredentialsError:
            return self._invalid_credentials()
        except (AccessValidationError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return AccessHTTPResponse(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_request", "message": str(exc)},
            )
        except AccessStateError:
            return self._state_invalid()

    def authenticate(self, cookie_header: str) -> SessionView:
        token = self._session_token(cookie_header)
        return self.store.authenticate(token)

    @staticmethod
    def method_not_allowed() -> AccessHTTPResponse:
        return AccessHTTPResponse(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {"error": "method_not_allowed"},
        )

    @staticmethod
    def _decode_json(
        content_type: str,
        content_length: str | None,
        body: bytes,
    ) -> dict[str, Any]:
        media_type = content_type.partition(";")[0].strip().casefold()
        if media_type != "application/json":
            raise AccessValidationError("Content-Type must be application/json")
        try:
            declared_length = int(content_length or "0")
        except ValueError as exc:
            raise AccessValidationError("Content-Length is invalid") from exc
        if declared_length <= 0 or declared_length > _MAX_BODY_BYTES:
            raise AccessValidationError(
                f"request body must contain 1 to {_MAX_BODY_BYTES} bytes"
            )
        if len(body) != declared_length:
            raise AccessValidationError("request body length does not match Content-Length")
        value = json.loads(body.decode("utf-8"))
        if not isinstance(value, dict):
            raise AccessValidationError("request body must be a JSON object")
        return value

    @staticmethod
    def _require_fields(payload: Mapping[str, Any], expected: set[str]) -> None:
        missing = expected - set(payload)
        unknown = set(payload) - expected
        if missing or unknown:
            raise AccessValidationError(
                f"request fields mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}"
            )

    def _logout(self, cookie_header: str) -> AccessHTTPResponse:
        try:
            self.store.logout(self._session_token(cookie_header))
        except (InvalidCredentialsError, AccessValidationError):
            pass
        except AccessStateError:
            return self._state_invalid()
        return AccessHTTPResponse(
            HTTPStatus.NO_CONTENT,
            None,
            (("Set-Cookie", self._expired_cookie()),),
        )

    @staticmethod
    def _session_token(cookie_header: str) -> str:
        occurrences = sum(
            1
            for part in cookie_header.split(";")
            if part.strip().partition("=")[0].strip() == ACCESS_COOKIE_NAME
        )
        if occurrences != 1:
            raise InvalidCredentialsError("invalid or missing session cookie")
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
        except CookieError as exc:
            raise InvalidCredentialsError("invalid session cookie") from exc
        morsel = cookie.get(ACCESS_COOKIE_NAME)
        if morsel is None or not morsel.value:
            raise InvalidCredentialsError("invalid or missing session cookie")
        return morsel.value

    def _session_cookie(self, token: str, session: SessionView) -> str:
        max_age = max(1, session.expires_at - int(time.time()))
        attributes = [
            f"{ACCESS_COOKIE_NAME}={token}",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
            f"Max-Age={max_age}",
        ]
        if self.cookie_secure:
            attributes.append("Secure")
        return "; ".join(attributes)

    def _expired_cookie(self) -> str:
        attributes = [
            f"{ACCESS_COOKIE_NAME}=",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
            "Max-Age=0",
            "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
        ]
        if self.cookie_secure:
            attributes.append("Secure")
        return "; ".join(attributes)

    @staticmethod
    def _invalid_credentials() -> AccessHTTPResponse:
        return AccessHTTPResponse(
            HTTPStatus.UNAUTHORIZED,
            {
                "error": "invalid_credentials",
                "message": "邮箱或邀请码无效。",
            },
        )

    @staticmethod
    def _state_invalid() -> AccessHTTPResponse:
        return AccessHTTPResponse(
            HTTPStatus.CONFLICT,
            {
                "error": "access_state_invalid",
                "message": "访问状态暂时无法验证。",
            },
        )


__all__ = ["ACCESS_COOKIE_NAME", "AccessAPI", "AccessHTTPResponse"]
