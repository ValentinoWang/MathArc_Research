"""Persistent invitation access primitives for institutional previews.

This module is transport-neutral.  In particular, invitation issuance is a
programmatic administration operation and is not exposed as an HTTP route.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
import time
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from .local_store import LocalStoreError, exclusive_lock, external_root, state_digest
from .schema import canonical_json

_SCHEMA_VERSION = "1.0"
_STATE_FILENAME = "access-state.json"
_DEFAULT_INVITATION_TTL_SECONDS = 7 * 24 * 60 * 60
_MAX_INVITATION_TTL_SECONDS = 365 * 24 * 60 * 60
_MAX_SESSION_TTL_SECONDS = 31 * 24 * 60 * 60


class AccessError(Exception):
    """Base class for access-domain failures."""


class AccessValidationError(AccessError, ValueError):
    """Raised when a caller supplies an invalid request."""


class InvalidCredentialsError(AccessError, PermissionError):
    """Raised for invalid, inactive, or expired credentials."""


class AccessConflictError(AccessError):
    """Raised when a requested state transition has already occurred."""


class AccessStateError(AccessError):
    """Raised when persisted access state cannot be trusted."""


@dataclass(frozen=True, slots=True)
class ApplicationView:
    application_id: str
    status: str
    email: str
    submitted_at: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "status": self.status,
            "email": self.email,
            "submitted_at": self.submitted_at,
        }


@dataclass(frozen=True, slots=True)
class InvitationView:
    invitation_id: str
    email: str
    topic_scopes: tuple[str, ...]
    issued_at: int
    expires_at: int
    redeemed_at: int | None
    revoked_at: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "invitation_id": self.invitation_id,
            "email": self.email,
            "topic_scopes": list(self.topic_scopes),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "redeemed_at": self.redeemed_at,
            "revoked_at": self.revoked_at,
        }


@dataclass(frozen=True, slots=True)
class IssuedInvitation:
    """One-time administrative result; ``code`` is never persisted."""

    code: str
    invitation: InvitationView


@dataclass(frozen=True, slots=True)
class SessionView:
    email: str
    topic_scopes: tuple[str, ...]
    expires_at: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "topic_scopes": list(self.topic_scopes),
            "expires_at": self.expires_at,
        }


def _exact_mapping(value: object, fields: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AccessStateError(f"{label} must be an object")
    missing = fields - set(value)
    unknown = set(value) - fields
    if missing or unknown:
        raise AccessStateError(
            f"{label} fields mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    return value


def _stored_string(value: object, label: str, *, maximum: int = 1_000) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise AccessStateError(f"{label} must be a non-empty bounded string")
    if value != value.strip() or any(ord(character) < 32 for character in value):
        raise AccessStateError(f"{label} contains invalid whitespace or control characters")
    return value


def _stored_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise AccessStateError(f"{label} must be a non-negative integer")
    return value


def _stored_optional_integer(value: object, label: str) -> int | None:
    if value is None:
        return None
    return _stored_integer(value, label)


def _stored_digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or set(value) - set("0123456789abcdef")
    ):
        raise AccessStateError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _request_text(value: object, label: str, *, maximum: int) -> str:
    if not isinstance(value, str):
        raise AccessValidationError(f"{label} must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise AccessValidationError(f"{label} must contain 1 to {maximum} characters")
    if any(ord(character) < 32 for character in normalized):
        raise AccessValidationError(f"{label} cannot contain control characters")
    return normalized


def _normalize_email(value: object) -> str:
    email = _request_text(value, "email", maximum=254).casefold()
    if email.count("@") != 1 or any(character.isspace() for character in email):
        raise AccessValidationError("email must be a valid address")
    local, domain = email.split("@")
    if not local or not domain or domain.startswith(".") or domain.endswith(".") or "." not in domain:
        raise AccessValidationError("email must be a valid address")
    return email


def _request_topics(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise AccessValidationError("topic_scopes must be an iterable of strings")
    try:
        topics = tuple(
            _request_text(value, "topic scope", maximum=128) for value in values
        )
    except TypeError as exc:
        raise AccessValidationError("topic_scopes must be an iterable of strings") from exc
    if not topics:
        raise AccessValidationError("topic_scopes cannot be empty")
    if len(topics) > 100:
        raise AccessValidationError("topic_scopes cannot contain more than 100 entries")
    if len(set(topics)) != len(topics):
        raise AccessValidationError("topic_scopes cannot contain duplicates")
    return topics


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class InvitationAccessStore:
    """Locked JSON store for preview applications, invitations, and sessions."""

    def __init__(
        self,
        root: str | Path,
        *,
        clock: Callable[[], int | float] = time.time,
        session_ttl_seconds: int = 12 * 60 * 60,
    ) -> None:
        try:
            self.root = external_root(root)
        except LocalStoreError as exc:
            raise AccessStateError(str(exc)) from exc
        self._clock = clock
        self._session_ttl_seconds = self._request_ttl(
            session_ttl_seconds,
            label="session_ttl_seconds",
            maximum=_MAX_SESSION_TTL_SECONDS,
        )
        try:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as exc:
            raise AccessStateError("access store root could not be created") from exc
        if not self.root.is_dir():
            raise AccessStateError("access store root must be a directory")
        self.path = self.root / _STATE_FILENAME
        with exclusive_lock(self.root, _STATE_FILENAME):
            if self.path.exists():
                self._load_state()
            else:
                self._write_state(self._empty_state())

    def submit_application(
        self,
        *,
        email: str,
        institution: str,
        research_role: str,
        research_direction: str,
        purpose: str,
    ) -> ApplicationView:
        normalized_email = _normalize_email(email)
        normalized_institution = _request_text(institution, "institution", maximum=300)
        normalized_role = _request_text(research_role, "research_role", maximum=200)
        normalized_direction = _request_text(
            research_direction,
            "research_direction",
            maximum=500,
        )
        normalized_purpose = _request_text(purpose, "purpose", maximum=2_000)
        now = self._now()
        application = {
            "application_id": uuid.uuid4().hex,
            "status": "PENDING",
            "email": normalized_email,
            "institution": normalized_institution,
            "research_role": normalized_role,
            "research_direction": normalized_direction,
            "purpose": normalized_purpose,
            "submitted_at": now,
        }
        with exclusive_lock(self.root, _STATE_FILENAME):
            state = self._load_state()
            state["applications"].append(application)
            self._write_state(state)
        return self._application_view(application)

    def issue_invitation(
        self,
        *,
        email: str,
        topic_scopes: Iterable[str],
        ttl_seconds: int | None = None,
    ) -> IssuedInvitation:
        normalized_email = _normalize_email(email)
        normalized_topics = _request_topics(topic_scopes)
        ttl = self._request_ttl(
            _DEFAULT_INVITATION_TTL_SECONDS if ttl_seconds is None else ttl_seconds,
            label="ttl_seconds",
            maximum=_MAX_INVITATION_TTL_SECONDS,
        )
        now = self._now()
        code = secrets.token_urlsafe(32)
        invitation = {
            "invitation_id": uuid.uuid4().hex,
            "email": normalized_email,
            "topic_scopes": list(normalized_topics),
            "code_hash_sha256": _hash_secret(code),
            "issued_at": now,
            "expires_at": now + ttl,
            "redeemed_at": None,
            "revoked_at": None,
        }
        with exclusive_lock(self.root, _STATE_FILENAME):
            state = self._load_state()
            if any(
                hmac.compare_digest(item["code_hash_sha256"], invitation["code_hash_sha256"])
                for item in state["invitations"]
            ):
                raise AccessStateError("secure random invitation collision")
            state["invitations"].append(invitation)
            self._write_state(state)
        return IssuedInvitation(code=code, invitation=self._invitation_view(invitation))

    def revoke_invitation(self, invitation_id: str) -> InvitationView:
        normalized_id = _request_text(invitation_id, "invitation_id", maximum=128)
        now = self._now()
        with exclusive_lock(self.root, _STATE_FILENAME):
            state = self._load_state()
            invitation = next(
                (
                    item
                    for item in state["invitations"]
                    if item["invitation_id"] == normalized_id
                ),
                None,
            )
            if invitation is None:
                raise AccessValidationError("unknown invitation_id")
            if invitation["redeemed_at"] is not None:
                raise AccessConflictError("a redeemed invitation cannot be revoked")
            if invitation["revoked_at"] is not None:
                raise AccessConflictError("invitation is already revoked")
            invitation["revoked_at"] = now
            self._write_state(state)
            return self._invitation_view(invitation)

    def redeem(self, *, email: str, code: str) -> tuple[str, SessionView]:
        normalized_email = _normalize_email(email)
        normalized_code = _request_text(code, "code", maximum=1_024)
        code_hash = _hash_secret(normalized_code)
        now = self._now()
        with exclusive_lock(self.root, _STATE_FILENAME):
            state = self._load_state()
            invitation = next(
                (
                    item
                    for item in state["invitations"]
                    if hmac.compare_digest(item["code_hash_sha256"], code_hash)
                ),
                None,
            )
            valid = (
                invitation is not None
                and hmac.compare_digest(invitation["email"], normalized_email)
                and invitation["redeemed_at"] is None
                and invitation["revoked_at"] is None
                and now < invitation["expires_at"]
            )
            if not valid:
                raise InvalidCredentialsError("invalid or inactive invitation credentials")
            assert invitation is not None
            invitation["redeemed_at"] = now
            session_token = secrets.token_urlsafe(32)
            session = {
                "session_id": uuid.uuid4().hex,
                "invitation_id": invitation["invitation_id"],
                "email": invitation["email"],
                "topic_scopes": list(invitation["topic_scopes"]),
                "token_hash_sha256": _hash_secret(session_token),
                "created_at": now,
                "expires_at": now + self._session_ttl_seconds,
                "logged_out_at": None,
            }
            if any(
                hmac.compare_digest(item["token_hash_sha256"], session["token_hash_sha256"])
                for item in state["sessions"]
            ):
                raise AccessStateError("secure random session collision")
            state["sessions"].append(session)
            self._write_state(state)
            return session_token, self._session_view(session)

    def authenticate(self, session_token: str) -> SessionView:
        normalized_token = _request_text(session_token, "session_token", maximum=1_024)
        token_hash = _hash_secret(normalized_token)
        now = self._now()
        with exclusive_lock(self.root, _STATE_FILENAME):
            state = self._load_state()
            session = next(
                (
                    item
                    for item in state["sessions"]
                    if hmac.compare_digest(item["token_hash_sha256"], token_hash)
                ),
                None,
            )
            if (
                session is None
                or session["logged_out_at"] is not None
                or now >= session["expires_at"]
            ):
                raise InvalidCredentialsError("invalid or inactive session")
            return self._session_view(session)

    def logout(self, session_token: str) -> None:
        normalized_token = _request_text(session_token, "session_token", maximum=1_024)
        token_hash = _hash_secret(normalized_token)
        now = self._now()
        with exclusive_lock(self.root, _STATE_FILENAME):
            state = self._load_state()
            session = next(
                (
                    item
                    for item in state["sessions"]
                    if hmac.compare_digest(item["token_hash_sha256"], token_hash)
                ),
                None,
            )
            if (
                session is None
                or session["logged_out_at"] is not None
                or now >= session["expires_at"]
            ):
                raise InvalidCredentialsError("invalid or inactive session")
            session["logged_out_at"] = now
            self._write_state(state)

    def _load_state(self) -> dict[str, Any]:
        if self.path.is_symlink():
            raise AccessStateError("access state cannot be a symbolic link")
        try:
            raw = self.path.read_text(encoding="utf-8")
            value = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise AccessStateError("access state is unreadable") from exc
        state = dict(
            _exact_mapping(
                value,
                {
                    "schema_version",
                    "applications",
                    "invitations",
                    "sessions",
                    "state_digest_sha256",
                },
                "access state",
            )
        )
        if state["schema_version"] != _SCHEMA_VERSION:
            raise AccessStateError("unsupported access-state schema version")
        expected_digest = state_digest(state)
        actual_digest = _stored_digest(
            state["state_digest_sha256"],
            "state_digest_sha256",
        )
        if not hmac.compare_digest(actual_digest, expected_digest):
            raise AccessStateError("access-state digest mismatch")
        for field in ("applications", "invitations", "sessions"):
            if not isinstance(state[field], list):
                raise AccessStateError(f"{field} must be an array")
        self._validate_applications(state["applications"])
        invitations = self._validate_invitations(state["invitations"])
        self._validate_sessions(state["sessions"], invitations)
        return state

    def _write_state(self, state: dict[str, Any]) -> None:
        state["state_digest_sha256"] = state_digest(state)
        content = (canonical_json(state) + "\n").encode("utf-8")
        temporary_path: Path | None = None
        descriptor = -1
        renamed = False
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{_STATE_FILENAME}.",
                suffix=".tmp",
                dir=self.root,
            )
            temporary_path = Path(temporary_name)
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as temporary_file:
                descriptor = -1
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
            renamed = True
            _fsync_directory(self.root)
        except OSError as exc:
            raise AccessStateError("access state could not be persisted") from exc
        finally:
            if descriptor != -1:
                os.close(descriptor)
            if not renamed and temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass

    def _validate_applications(self, applications: list[object]) -> None:
        identifiers: set[str] = set()
        fields = {
            "application_id",
            "status",
            "email",
            "institution",
            "research_role",
            "research_direction",
            "purpose",
            "submitted_at",
        }
        for index, value in enumerate(applications):
            item = _exact_mapping(value, fields, f"applications[{index}]")
            identifier = _stored_string(item["application_id"], "application_id", maximum=128)
            if identifier in identifiers:
                raise AccessStateError("duplicate application_id")
            identifiers.add(identifier)
            if item["status"] != "PENDING":
                raise AccessStateError("application status must be PENDING")
            self._validate_stored_email(item["email"])
            _stored_string(item["institution"], "institution", maximum=300)
            _stored_string(item["research_role"], "research_role", maximum=200)
            _stored_string(item["research_direction"], "research_direction", maximum=500)
            _stored_string(item["purpose"], "purpose", maximum=2_000)
            _stored_integer(item["submitted_at"], "submitted_at")

    def _validate_invitations(
        self,
        invitations: list[object],
    ) -> dict[str, Mapping[str, Any]]:
        by_id: dict[str, Mapping[str, Any]] = {}
        code_hashes: set[str] = set()
        fields = {
            "invitation_id",
            "email",
            "topic_scopes",
            "code_hash_sha256",
            "issued_at",
            "expires_at",
            "redeemed_at",
            "revoked_at",
        }
        for index, value in enumerate(invitations):
            item = _exact_mapping(value, fields, f"invitations[{index}]")
            identifier = _stored_string(item["invitation_id"], "invitation_id", maximum=128)
            if identifier in by_id:
                raise AccessStateError("duplicate invitation_id")
            by_id[identifier] = item
            self._validate_stored_email(item["email"])
            self._validate_stored_topics(item["topic_scopes"])
            code_hash = _stored_digest(item["code_hash_sha256"], "code_hash_sha256")
            if code_hash in code_hashes:
                raise AccessStateError("duplicate invitation code hash")
            code_hashes.add(code_hash)
            issued_at = _stored_integer(item["issued_at"], "issued_at")
            expires_at = _stored_integer(item["expires_at"], "expires_at")
            redeemed_at = _stored_optional_integer(item["redeemed_at"], "redeemed_at")
            revoked_at = _stored_optional_integer(item["revoked_at"], "revoked_at")
            if expires_at <= issued_at:
                raise AccessStateError("invitation must expire after issuance")
            if redeemed_at is not None and not issued_at <= redeemed_at < expires_at:
                raise AccessStateError("invitation redemption timestamp is invalid")
            if revoked_at is not None and revoked_at < issued_at:
                raise AccessStateError("invitation revocation timestamp is invalid")
            if redeemed_at is not None and revoked_at is not None:
                raise AccessStateError("invitation cannot be both redeemed and revoked")
        return by_id

    def _validate_sessions(
        self,
        sessions: list[object],
        invitations: Mapping[str, Mapping[str, Any]],
    ) -> None:
        identifiers: set[str] = set()
        invitation_ids: set[str] = set()
        token_hashes: set[str] = set()
        fields = {
            "session_id",
            "invitation_id",
            "email",
            "topic_scopes",
            "token_hash_sha256",
            "created_at",
            "expires_at",
            "logged_out_at",
        }
        for index, value in enumerate(sessions):
            item = _exact_mapping(value, fields, f"sessions[{index}]")
            identifier = _stored_string(item["session_id"], "session_id", maximum=128)
            invitation_id = _stored_string(
                item["invitation_id"],
                "invitation_id",
                maximum=128,
            )
            if identifier in identifiers or invitation_id in invitation_ids:
                raise AccessStateError("duplicate session or invitation session")
            identifiers.add(identifier)
            invitation_ids.add(invitation_id)
            invitation = invitations.get(invitation_id)
            if invitation is None:
                raise AccessStateError("session refers to an unknown invitation")
            email = self._validate_stored_email(item["email"])
            topics = self._validate_stored_topics(item["topic_scopes"])
            token_hash = _stored_digest(item["token_hash_sha256"], "token_hash_sha256")
            if token_hash in token_hashes:
                raise AccessStateError("duplicate session token hash")
            token_hashes.add(token_hash)
            created_at = _stored_integer(item["created_at"], "created_at")
            expires_at = _stored_integer(item["expires_at"], "expires_at")
            logged_out_at = _stored_optional_integer(item["logged_out_at"], "logged_out_at")
            if expires_at <= created_at:
                raise AccessStateError("session must expire after creation")
            if logged_out_at is not None and logged_out_at < created_at:
                raise AccessStateError("session logout timestamp is invalid")
            if (
                invitation["redeemed_at"] != created_at
                or invitation["revoked_at"] is not None
                or invitation["email"] != email
                or tuple(invitation["topic_scopes"]) != topics
            ):
                raise AccessStateError("session does not match its redeemed invitation")

    @staticmethod
    def _validate_stored_email(value: object) -> str:
        email = _stored_string(value, "email", maximum=254)
        try:
            normalized = _normalize_email(email)
        except AccessValidationError as exc:
            raise AccessStateError("stored email is invalid") from exc
        if normalized != email:
            raise AccessStateError("stored email is not canonical")
        return email

    @staticmethod
    def _validate_stored_topics(value: object) -> tuple[str, ...]:
        if not isinstance(value, list):
            raise AccessStateError("topic_scopes must be an array")
        try:
            topics = _request_topics(value)
        except AccessValidationError as exc:
            raise AccessStateError("stored topic scopes are invalid") from exc
        return topics

    @staticmethod
    def _request_ttl(value: object, *, label: str, maximum: int) -> int:
        if type(value) is not int or not 1 <= value <= maximum:
            raise AccessValidationError(f"{label} must be an integer from 1 to {maximum}")
        return value

    def _now(self) -> int:
        try:
            value = self._clock()
        except Exception as exc:
            raise AccessStateError("clock failed") from exc
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise AccessStateError("clock must return a non-negative timestamp")
        return int(value)

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "applications": [],
            "invitations": [],
            "sessions": [],
            "state_digest_sha256": "",
        }

    @staticmethod
    def _application_view(item: Mapping[str, Any]) -> ApplicationView:
        return ApplicationView(
            application_id=item["application_id"],
            status=item["status"],
            email=item["email"],
            submitted_at=item["submitted_at"],
        )

    @staticmethod
    def _invitation_view(item: Mapping[str, Any]) -> InvitationView:
        return InvitationView(
            invitation_id=item["invitation_id"],
            email=item["email"],
            topic_scopes=tuple(item["topic_scopes"]),
            issued_at=item["issued_at"],
            expires_at=item["expires_at"],
            redeemed_at=item["redeemed_at"],
            revoked_at=item["revoked_at"],
        )

    @staticmethod
    def _session_view(item: Mapping[str, Any]) -> SessionView:
        return SessionView(
            email=item["email"],
            topic_scopes=tuple(item["topic_scopes"]),
            expires_at=item["expires_at"],
        )


class _DatabaseConnection(Protocol):
    def cursor(self) -> Any: ...
    def commit(self) -> Any: ...
    def rollback(self) -> Any: ...
    def close(self) -> Any: ...


DatabaseConnectionFactory = Callable[[], _DatabaseConnection]


class PostgresInvitationAccessStore:
    """PostgreSQL implementation of the public invitation access contract.

    The administrator service is the authority for invitation issuance.  This
    adapter intentionally only consumes the shared ``invitations`` table and
    records public sessions in ``access_sessions``.  Schema creation remains an
    explicit migration/deployment operation.
    """

    def __init__(
        self,
        connection_factory: DatabaseConnectionFactory,
        *,
        clock: Callable[[], int | float] = time.time,
        session_ttl_seconds: int = 12 * 60 * 60,
    ) -> None:
        if not callable(connection_factory):
            raise AccessValidationError("connection_factory must be callable")
        self.connection_factory = connection_factory
        self._clock = clock
        self._session_ttl_seconds = InvitationAccessStore._request_ttl(
            session_ttl_seconds,
            label="session_ttl_seconds",
            maximum=_MAX_SESSION_TTL_SECONDS,
        )

    def submit_application(
        self,
        *,
        email: str,
        institution: str,
        research_role: str,
        research_direction: str,
        purpose: str,
    ) -> ApplicationView:
        normalized_email = _normalize_email(email)
        normalized_institution = _request_text(institution, "institution", maximum=300)
        normalized_role = _request_text(research_role, "research_role", maximum=200)
        normalized_direction = _request_text(research_direction, "research_direction", maximum=500)
        normalized_purpose = _request_text(purpose, "purpose", maximum=2_000)
        now = self._now()
        application = {
            "application_id": uuid.uuid4().hex,
            "status": "PENDING",
            "email": normalized_email,
            "institution": normalized_institution,
            "research_role": normalized_role,
            "research_direction": normalized_direction,
            "purpose": normalized_purpose,
            "submitted_at": now,
        }
        try:
            with self._transaction() as cursor:
                cursor.execute(
                    "INSERT INTO applications "
                    "(application_id,status,email,institution,research_role,research_direction,purpose,submitted_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    tuple(application.values()),
                )
        except AccessError:
            raise
        except Exception as exc:
            raise AccessStateError("PostgreSQL access state is unavailable") from exc
        return ApplicationView(
            str(application["application_id"]),
            str(application["status"]),
            str(application["email"]),
            cast(int, application["submitted_at"]),
        )

    def issue_invitation(
        self,
        *,
        email: str,
        topic_scopes: Iterable[str],
        ttl_seconds: int | None = None,
    ) -> IssuedInvitation:
        normalized_email = _normalize_email(email)
        normalized_topics = _request_topics(topic_scopes)
        ttl = InvitationAccessStore._request_ttl(
            _DEFAULT_INVITATION_TTL_SECONDS if ttl_seconds is None else ttl_seconds,
            label="ttl_seconds",
            maximum=_MAX_INVITATION_TTL_SECONDS,
        )
        now = self._now()
        code = secrets.token_urlsafe(32)
        invitation = {
            "invitation_id": uuid.uuid4().hex,
            "email": normalized_email,
            "topic_scopes": list(normalized_topics),
            "code_hash_sha256": _hash_secret(code),
            "issued_at": now,
            "expires_at": now + ttl,
            "redeemed_at": None,
            "revoked_at": None,
        }
        try:
            with self._transaction() as cursor:
                cursor.execute(
                    "INSERT INTO invitations "
                    "(invitation_id,email,topic_scopes,code_hash_sha256,issued_at,expires_at,redeemed_at,revoked_at) "
                    "VALUES (%s,%s,%s::jsonb,%s,%s,%s,%s,%s)",
                    (
                        invitation["invitation_id"],
                        invitation["email"],
                        json.dumps(invitation["topic_scopes"]),
                        invitation["code_hash_sha256"],
                        invitation["issued_at"],
                        invitation["expires_at"],
                        None,
                        None,
                    ),
                )
        except Exception as exc:
            raise AccessStateError("PostgreSQL access state is unavailable") from exc
        return IssuedInvitation(code, InvitationAccessStore._invitation_view(invitation))

    def revoke_invitation(self, invitation_id: str) -> InvitationView:
        identifier = _request_text(invitation_id, "invitation_id", maximum=128)
        now = self._now()
        try:
            with self._transaction() as cursor:
                cursor.execute(
                    "SELECT invitation_id,email,topic_scopes,issued_at,expires_at,redeemed_at,revoked_at "
                    "FROM invitations WHERE invitation_id=%s FOR UPDATE",
                    (identifier,),
                )
                row = cursor.fetchone()
                if row is None:
                    raise AccessValidationError("unknown invitation_id")
                item = _access_row(row, ("invitation_id", "email", "topic_scopes", "issued_at", "expires_at", "redeemed_at", "revoked_at"))
                if item["redeemed_at"] is not None:
                    raise AccessConflictError("a redeemed invitation cannot be revoked")
                if item["revoked_at"] is not None:
                    raise AccessConflictError("invitation is already revoked")
                cursor.execute("UPDATE invitations SET revoked_at=%s WHERE invitation_id=%s", (now, identifier))
                item["revoked_at"] = now
                item["topic_scopes"] = _json_topics(item["topic_scopes"])
                return InvitationView(
                    str(item["invitation_id"]), str(item["email"]), tuple(item["topic_scopes"]),
                    int(item["issued_at"]), int(item["expires_at"]), item["redeemed_at"], item["revoked_at"],
                )
        except (AccessValidationError, AccessConflictError, AccessStateError):
            raise
        except Exception as exc:
            raise AccessStateError("PostgreSQL access state is unavailable") from exc

    def redeem(self, *, email: str, code: str) -> tuple[str, SessionView]:
        normalized_email = _normalize_email(email)
        normalized_code = _request_text(code, "code", maximum=1_024)
        code_hash = _hash_secret(normalized_code)
        now = self._now()
        try:
            with self._transaction() as cursor:
                cursor.execute(
                    "SELECT invitation_id,email,topic_scopes,issued_at,expires_at,redeemed_at,revoked_at,code_hash_sha256 "
                    "FROM invitations WHERE code_hash_sha256=%s FOR UPDATE",
                    (code_hash,),
                )
                row = cursor.fetchone()
                if row is None:
                    raise InvalidCredentialsError("invalid or inactive invitation credentials")
                item = _access_row(row, ("invitation_id", "email", "topic_scopes", "issued_at", "expires_at", "redeemed_at", "revoked_at", "code_hash_sha256"))
                valid = (
                    hmac.compare_digest(str(item["code_hash_sha256"]), code_hash)
                    and hmac.compare_digest(str(item["email"]), normalized_email)
                    and item["redeemed_at"] is None
                    and item["revoked_at"] is None
                    and now < int(item["expires_at"])
                )
                if not valid:
                    raise InvalidCredentialsError("invalid or inactive invitation credentials")
                topics = _json_topics(item["topic_scopes"])
                session_token = secrets.token_urlsafe(32)
                session = {
                    "session_id": uuid.uuid4().hex,
                    "invitation_id": str(item["invitation_id"]),
                    "email": str(item["email"]),
                    "topic_scopes": topics,
                    "token_hash_sha256": _hash_secret(session_token),
                    "created_at": now,
                    "expires_at": now + self._session_ttl_seconds,
                    "logged_out_at": None,
                }
                cursor.execute("UPDATE invitations SET redeemed_at=%s WHERE invitation_id=%s", (now, session["invitation_id"]))
                cursor.execute(
                    "INSERT INTO access_sessions "
                    "(access_session_id,invitation_id,email,topic_scopes,token_hash_sha256,created_at,expires_at,logged_out_at) "
                    "VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s,%s)",
                    (
                        session["session_id"], session["invitation_id"], session["email"], json.dumps(topics),
                        session["token_hash_sha256"], session["created_at"], session["expires_at"], None,
                    ),
                )
                return session_token, SessionView(
                    str(session["email"]), tuple(topics), cast(int, session["expires_at"])
                )
        except (InvalidCredentialsError, AccessValidationError, AccessStateError):
            raise
        except Exception as exc:
            raise AccessStateError("PostgreSQL access state is unavailable") from exc

    def authenticate(self, session_token: str) -> SessionView:
        normalized_token = _request_text(session_token, "session_token", maximum=1_024)
        token_hash = _hash_secret(normalized_token)
        now = self._now()
        try:
            with self._transaction() as cursor:
                cursor.execute(
                    "SELECT email,topic_scopes,expires_at,logged_out_at,token_hash_sha256 "
                    "FROM access_sessions WHERE token_hash_sha256=%s",
                    (token_hash,),
                )
                row = cursor.fetchone()
                if row is None:
                    raise InvalidCredentialsError("invalid or inactive session")
                item = _access_row(row, ("email", "topic_scopes", "expires_at", "logged_out_at", "token_hash_sha256"))
                if (
                    not hmac.compare_digest(str(item["token_hash_sha256"]), token_hash)
                    or item["logged_out_at"] is not None
                    or now >= int(item["expires_at"])
                ):
                    raise InvalidCredentialsError("invalid or inactive session")
                return SessionView(str(item["email"]), tuple(_json_topics(item["topic_scopes"])), int(item["expires_at"]))
        except (InvalidCredentialsError, AccessValidationError, AccessStateError):
            raise
        except Exception as exc:
            raise AccessStateError("PostgreSQL access state is unavailable") from exc

    def logout(self, session_token: str) -> None:
        normalized_token = _request_text(session_token, "session_token", maximum=1_024)
        token_hash = _hash_secret(normalized_token)
        now = self._now()
        try:
            with self._transaction() as cursor:
                cursor.execute(
                    "UPDATE access_sessions SET logged_out_at=%s "
                    "WHERE token_hash_sha256=%s AND logged_out_at IS NULL AND expires_at>%s",
                    (now, token_hash, now),
                )
                if getattr(cursor, "rowcount", 1) == 0:
                    raise InvalidCredentialsError("invalid or inactive session")
        except (InvalidCredentialsError, AccessValidationError, AccessStateError):
            raise
        except Exception as exc:
            raise AccessStateError("PostgreSQL access state is unavailable") from exc

    @contextmanager
    def _transaction(self) -> Iterator[Any]:
        connection = self.connection_factory()
        if connection is None:
            raise AccessStateError("connection_factory returned None")
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            finally:
                if hasattr(cursor, "close"):
                    cursor.close()
            raise
        else:
            if hasattr(cursor, "close"):
                cursor.close()
        finally:
            if hasattr(connection, "close"):
                connection.close()

    def _now(self) -> int:
        try:
            value = self._clock()
        except Exception as exc:
            raise AccessStateError("clock failed") from exc
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise AccessStateError("clock must return a non-negative timestamp")
        return int(value)


def _access_row(row: Any, names: tuple[str, ...]) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return {name: row[name] for name in names}
    try:
        return dict(zip(names, row, strict=True))
    except (TypeError, ValueError) as exc:
        raise AccessStateError("PostgreSQL returned an invalid access row") from exc


def _json_topics(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise AccessStateError("stored topic scopes are invalid") from exc
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        raise AccessStateError("stored topic scopes are invalid")
    try:
        return list(_request_topics(value))
    except AccessValidationError as exc:
        raise AccessStateError("stored topic scopes are invalid") from exc


def psycopg_access_connection_factory(dsn: str) -> DatabaseConnectionFactory:
    """Return a lazy psycopg connection factory for public access storage."""

    if not isinstance(dsn, str) or not dsn.strip():
        raise AccessValidationError("dsn is required")

    def connect() -> _DatabaseConnection:
        try:
            import psycopg
        except ImportError as exc:
            raise AccessStateError("psycopg is required for PostgreSQL access") from exc
        return cast(_DatabaseConnection, psycopg.connect(dsn))

    return connect
