"""Administrator identity and session primitives.

The application does not authenticate reverse-proxy headers itself.  A caller
must explicitly state that the request came through a configured, trusted
proxy before these headers are accepted.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

ADMIN_ROLES = frozenset({"access_admin", "access_reviewer", "security_admin"})
_HEADER_NAMES = {
    "x-admin-subject": "subject",
    "x-admin-email": "email",
    "x-admin-role": "role",
    "x-admin-auth-method": "auth_method",
}
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AdminAuthError(Exception):
    """Base class for administrator authentication failures."""


class UntrustedProxyError(AdminAuthError, PermissionError):
    """Raised when administrator headers arrive without proxy attestation."""


class AdminIdentityError(AdminAuthError, ValueError):
    """Raised when proxy identity headers are incomplete or malformed."""


class AdminSessionError(AdminAuthError, PermissionError):
    """Raised for an invalid or inactive administrator session."""


@dataclass(frozen=True, slots=True)
class AdminIdentity:
    subject: str
    email: str
    role: str
    auth_method: str

    def __post_init__(self) -> None:
        subject = _text(self.subject, "subject", 256)
        email = _email(self.email)
        role = _text(self.role, "role", 64)
        auth_method = _text(self.auth_method, "auth_method", 128)
        if role not in ADMIN_ROLES:
            raise AdminIdentityError(f"unsupported administrator role: {role}")
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "auth_method", auth_method)

    def to_dict(self) -> dict[str, str]:
        return {
            "subject": self.subject,
            "email": self.email,
            "role": self.role,
            "auth_method": self.auth_method,
        }


@dataclass(frozen=True, slots=True)
class AdminSession:
    session_id: str
    subject: str
    email: str
    role: str
    auth_method: str
    created_at: int
    expires_at: int
    revoked_at: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "subject": self.subject,
            "email": self.email,
            "role": self.role,
            "auth_method": self.auth_method,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
        }


def hash_session_token(token: str) -> str:
    """Return the only representation suitable for persistence."""

    if not isinstance(token, str) or not token or len(token) > 1024:
        raise AdminSessionError("session token is invalid")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def extract_proxy_identity(
    headers: Mapping[str, Any],
    *,
    trusted_proxy: bool = False,
) -> AdminIdentity | None:
    """Parse the four admin headers only after an upstream trust decision.

    Missing headers mean an anonymous request and return ``None``.  A partial
    set is rejected, preventing a caller from combining proxy and local data.
    Duplicate values are rejected because a proxy must emit one canonical
    identity per request.
    """

    values: dict[str, Any] = {}
    for raw_name, raw_value in headers.items():
        name = str(raw_name).strip().casefold()
        field = _HEADER_NAMES.get(name)
        if field is not None:
            if field in values:
                raise AdminIdentityError(f"duplicate {raw_name} header")
            values[field] = raw_value
    if not values:
        return None
    if not trusted_proxy:
        raise UntrustedProxyError("administrator headers require a trusted reverse proxy")
    required = set(_HEADER_NAMES.values())
    missing = required - set(values)
    if missing:
        raise AdminIdentityError(f"incomplete administrator identity: missing={sorted(missing)}")
    return AdminIdentity(
        subject=_single_header(values["subject"], "X-Admin-Subject"),
        email=_single_header(values["email"], "X-Admin-Email"),
        role=_single_header(values["role"], "X-Admin-Role"),
        auth_method=_single_header(values["auth_method"], "X-Admin-Auth-Method"),
    )


def require_admin_identity(
    headers: Mapping[str, Any], *, trusted_proxy: bool = False
) -> AdminIdentity:
    identity = extract_proxy_identity(headers, trusted_proxy=trusted_proxy)
    if identity is None:
        raise AdminIdentityError("administrator identity is required")
    return identity


def require_role(identity: AdminIdentity, allowed_roles: Iterable[str]) -> None:
    allowed = frozenset(str(role) for role in allowed_roles)
    if identity.role not in allowed:
        raise AdminAuthError(f"role {identity.role} is not allowed")


class AdminProxyAuthenticator:
    """Small adapter for HTTP servers that know whether the proxy is trusted."""

    def __init__(self, *, trusted_proxy: bool = False) -> None:
        self.trusted_proxy = trusted_proxy

    def authenticate(self, headers: Mapping[str, Any]) -> AdminIdentity | None:
        return extract_proxy_identity(headers, trusted_proxy=self.trusted_proxy)

    def require(self, headers: Mapping[str, Any]) -> AdminIdentity:
        return require_admin_identity(headers, trusted_proxy=self.trusted_proxy)


def _single_header(value: object, label: str) -> str:
    if isinstance(value, (list, tuple, set, frozenset)):
        raise AdminIdentityError(f"{label} must contain one value")
    return _text(value, label, 256)


def _text(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise AdminIdentityError(f"{label} must be a string")
    value = value.strip()
    if not value or len(value) > maximum or any(ord(char) < 32 for char in value):
        raise AdminIdentityError(f"{label} is invalid")
    return value


def _email(value: Any) -> str:
    normalized = _text(value, "email", 254).casefold()
    if not _EMAIL_RE.fullmatch(normalized):
        raise AdminIdentityError("email must be a valid address")
    return normalized


def constant_time_token_match(token: str, expected_hash: str) -> bool:
    """Compare a supplied token against a stored SHA-256 digest."""

    try:
        actual = hash_session_token(token)
    except AdminSessionError:
        return False
    return hmac.compare_digest(actual, expected_hash)


__all__ = [
    "ADMIN_ROLES",
    "AdminAuthError",
    "AdminIdentity",
    "AdminIdentityError",
    "AdminProxyAuthenticator",
    "AdminSession",
    "AdminSessionError",
    "UntrustedProxyError",
    "constant_time_token_match",
    "extract_proxy_identity",
    "hash_session_token",
    "new_session_token",
    "require_admin_identity",
    "require_role",
]
