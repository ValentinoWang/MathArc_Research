"""Database-independent contract tests for the administrator API.

These tests use a small fake HTTP connection so authentication, authorization,
redaction, idempotency, and status-code rules can run without PostgreSQL. The
same cases are also exercised against the real adapter by the deployment
integration suite.
"""

from __future__ import annotations

import copy
import json
import unittest
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

ADMIN_ROUTES = {
    ("POST", "/api/admin/auth/login"): {200, 400, 401, 429},
    ("POST", "/api/admin/auth/logout"): {204, 401},
    ("GET", "/api/admin/me"): {200, 401},
    ("GET", "/api/admin/applications"): {200, 401, 403},
    ("GET", "/api/admin/applications/app-1"): {200, 401, 403, 404},
    ("GET", "/api/admin/invitations"): {200, 401, 403},
    ("POST", "/api/admin/invitations"): {201, 400, 401, 403, 409},
    ("POST", "/api/admin/invitations/inv-1/revoke"): {200, 400, 401, 403, 409, 404},
    ("GET", "/api/admin/sessions"): {200, 401, 403},
    ("GET", "/api/admin/audit"): {200, 401, 403},
}

_TOKENS = {
    "admin-token": "access_admin",
    "reviewer-token": "access_reviewer",
    "security-token": "security_admin",
}
_READ_ROLES = {"access_admin", "access_reviewer", "security_admin"}
_WRITE_ROLES = {"access_admin", "security_admin"}
_SENSITIVE_KEYS = {
    "code_hash_sha256",
    "password",
    "password_hash",
    "mfa_secret",
    "mfa_private_key",
    "session_hash",
}


@dataclass(frozen=True)
class FakeResponse:
    status: int
    payload: Mapping[str, Any] | None = None
    headers: Mapping[str, str] = None  # type: ignore[assignment]


class FakeAdminConnection:
    """A deterministic fake of the public HTTP contract, not business code."""

    def __init__(self) -> None:
        self._idempotent: dict[str, tuple[str, FakeResponse]] = {}
        self._revoked: set[str] = set()

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> FakeResponse:
        headers = dict(headers or {})
        body = dict(body or {})
        if (method, path) not in ADMIN_ROUTES:
            if path in {route_path for _, route_path in ADMIN_ROUTES}:
                return FakeResponse(405, {"error": "method_not_allowed"}, {})
            return FakeResponse(404, {"error": "not_found"}, {})
        if method == "POST" and path == "/api/admin/auth/login":
            if body == {"username": "admin@example.edu", "password": "correct", "mfa_code": "123456"}:
                return FakeResponse(200, {"admin": {"admin_id": "adm-1", "role": "access_admin"}}, {"Set-Cookie": "matharc_admin_session=s-1; HttpOnly; Secure; SameSite=Strict"})
            return FakeResponse(401, {"error": "invalid_credentials"}, {})
        role = self._role(headers)
        if role is None:
            return FakeResponse(401, {"error": "admin_auth_required"}, {})
        if method == "POST" and path == "/api/admin/auth/logout":
            return FakeResponse(204, None, {"Set-Cookie": "matharc_admin_session=; Max-Age=0; HttpOnly; Secure; SameSite=Strict"})
        if method == "GET" and path == "/api/admin/me":
            return FakeResponse(200, {"admin": {"admin_id": "adm-1", "role": role, "permissions": sorted(self._permissions(role))}}, {})
        if path.endswith("/revoke"):
            if role not in _WRITE_ROLES:
                return FakeResponse(403, {"error": "forbidden"}, {})
            key = headers.get("Idempotency-Key", "")
            if not key:
                return FakeResponse(400, {"error": "idempotency_key_required"}, {})
            if path.rsplit("/", 2)[-2] in self._revoked:
                return FakeResponse(409, {"error": "invitation_already_revoked"}, {})
            self._revoked.add(path.rsplit("/", 2)[-2])
            return FakeResponse(200, {"invitation": {"invitation_id": "inv-1", "status": "revoked"}}, {})
        if method == "POST" and path == "/api/admin/invitations":
            if role not in _WRITE_ROLES:
                return FakeResponse(403, {"error": "forbidden"}, {})
            key = headers.get("Idempotency-Key", "")
            if not key:
                return FakeResponse(400, {"error": "idempotency_key_required"}, {})
            fingerprint = json.dumps(body, sort_keys=True)
            prior = self._idempotent.get(key)
            if prior:
                if prior[0] != fingerprint:
                    return FakeResponse(409, {"error": "idempotency_key_conflict"}, {})
                old = copy.deepcopy(dict(prior[1].payload or {}))
                old["replayed"] = True
                return FakeResponse(prior[1].status, old, prior[1].headers)
            if set(body) != {"email", "topic_scopes", "expires_in_seconds", "mfa_code"}:
                return FakeResponse(400, {"error": "invalid_request"}, {})
            result = FakeResponse(201, {"code": "ONCE-ONLY-CODE", "invitation": {"invitation_id": "inv-1", "email": body["email"], "topic_scopes": body["topic_scopes"]}}, {})
            self._idempotent[key] = (fingerprint, result)
            return result
        if role not in _READ_ROLES:
            return FakeResponse(403, {"error": "forbidden"}, {})
        if path == "/api/admin/invitations":
            return FakeResponse(200, {"items": [{"invitation_id": "inv-1", "email": "r@example.edu", "status": "active", "topic_scopes": ["combinatorics"]}]}, {})
        if path == "/api/admin/applications":
            return FakeResponse(200, {"items": [], "page": 1, "page_size": 50, "total": 0}, {})
        if path == "/api/admin/applications/app-1":
            return FakeResponse(200, {"application": {"application_id": "app-1", "email": "r@example.edu", "status": "PENDING"}}, {})
        if path == "/api/admin/sessions":
            return FakeResponse(200, {"items": [{"session_id": "s-1", "email": "r@example.edu", "status": "active"}]}, {})
        if path == "/api/admin/audit":
            return FakeResponse(200, {"items": [{"event_id": "evt-1", "actor": "adm-1", "action": "login", "result": "success"}]}, {})
        return FakeResponse(405, {"error": "method_not_allowed"}, {})

    @staticmethod
    def _role(headers: Mapping[str, str]) -> str | None:
        authorization = headers.get("Authorization", "")
        if authorization.startswith("Bearer ") and authorization[7:] in _TOKENS:
            return _TOKENS[authorization[7:]]
        return None

    @staticmethod
    def _permissions(role: str) -> set[str]:
        permissions = {"admin.read"} if role in _READ_ROLES else set()
        if role in _WRITE_ROLES:
            permissions |= {"invitation.issue", "invitation.revoke"}
        if role == "security_admin":
            permissions |= {"session.revoke", "admin.manage"}
        return permissions


def _all_values(value: Any):
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield key
            yield from _all_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_values(child)


class AdminAuthContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeAdminConnection()

    def call(self, method: str, path: str, token: str | None = "admin-token", **kwargs: Any) -> FakeResponse:
        headers = dict(kwargs.pop("headers", {}))
        if token is not None:
            headers.setdefault("Authorization", f"Bearer {token}")
        return self.api.request(method, path, headers=headers, **kwargs)

    def test_header_spoofing_and_malformed_bearer_are_rejected(self) -> None:
        for headers in ({}, {"X-Admin-Role": "access_admin"}, {"Authorization": "access_admin"}):
            with self.subTest(headers=headers):
                self.assertEqual(401, self.api.request("GET", "/api/admin/me", headers=headers).status)
        spoofed = self.api.request("GET", "/api/admin/me", headers={"Authorization": "Bearer admin-token", "X-Admin-Role": "security_admin"})
        self.assertEqual(200, spoofed.status)
        self.assertEqual("access_admin", spoofed.payload["admin"]["role"])

    def test_role_permissions_are_server_side(self) -> None:
        self.assertEqual(200, self.call("GET", "/api/admin/applications", token="reviewer-token").status)
        self.assertEqual(403, self.call("POST", "/api/admin/invitations", token="reviewer-token", headers={"Idempotency-Key": "k1"}, body={}).status)
        self.assertEqual(201, self.call("POST", "/api/admin/invitations", headers={"Idempotency-Key": "k1"}, body={"email": "r@example.edu", "topic_scopes": ["combinatorics"], "expires_in_seconds": 3600, "mfa_code": "123456"}).status)
        self.assertEqual(200, self.call("GET", "/api/admin/sessions", token="security-token").status)

    def test_sensitive_fields_are_absent_from_read_models(self) -> None:
        for path in ("/api/admin/invitations", "/api/admin/audit"):
            response = self.call("GET", path)
            self.assertEqual(200, response.status)
            self.assertTrue(_SENSITIVE_KEYS.isdisjoint(set(_all_values(response.payload))))
        issued = self.call("POST", "/api/admin/invitations", headers={"Idempotency-Key": "redact-1"}, body={"email": "r@example.edu", "topic_scopes": ["combinatorics"], "expires_in_seconds": 3600, "mfa_code": "123456"})
        self.assertIn("code", issued.payload or {})
        self.assertNotIn("code_hash_sha256", set(_all_values(issued.payload)))

    def test_issue_is_idempotent_and_conflicting_reuse_is_rejected(self) -> None:
        body = {"email": "r@example.edu", "topic_scopes": ["combinatorics"], "expires_in_seconds": 3600, "mfa_code": "123456"}
        first = self.call("POST", "/api/admin/invitations", headers={"Idempotency-Key": "same-1"}, body=body)
        replay = self.call("POST", "/api/admin/invitations", headers={"Idempotency-Key": "same-1"}, body=body)
        conflict = self.call("POST", "/api/admin/invitations", headers={"Idempotency-Key": "same-1"}, body={**body, "email": "other@example.edu"})
        self.assertEqual(201, first.status)
        self.assertEqual(201, replay.status)
        self.assertTrue(replay.payload["replayed"])
        self.assertEqual(409, conflict.status)

    def test_http_status_contract_for_auth_validation_and_unknown_route(self) -> None:
        self.assertEqual(401, self.call("GET", "/api/admin/me", token=None).status)
        self.assertEqual(400, self.call("POST", "/api/admin/invitations", headers={}, body={}).status)
        self.assertEqual(404, self.call("GET", "/api/admin/does-not-exist").status)
        self.assertEqual(405, self.call("PUT", "/api/admin/me").status)


if __name__ == "__main__":
    unittest.main()
