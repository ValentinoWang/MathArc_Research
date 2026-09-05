"""PostgreSQL-backed administrator access and audit domain service.

``connection_factory`` is deliberately injected so the module has no hard
dependency on psycopg and can be exercised with a transaction-aware test
connection.  The factory must return a DB-API connection; psycopg is imported
only by the optional :func:`psycopg_connection_factory` helper.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Protocol, cast

from .admin_auth import (
    ADMIN_ROLES,
    AdminIdentity,
    AdminSession,
    AdminSessionError,
    constant_time_token_match,
    hash_session_token,
    new_session_token,
    require_role,
)
from .schema import digest_json


class AdminServiceError(Exception):
    """Base class for administrator service failures."""


class AdminValidationError(AdminServiceError, ValueError):
    """Invalid administrator input."""


class AdminNotFoundError(AdminServiceError, LookupError):
    """Requested invitation or session does not exist."""


class AdminConflictError(AdminServiceError):
    """A state transition or idempotency key conflicts with prior state."""


class AdminStateError(AdminServiceError):
    """Persisted state or audit-chain integrity is invalid."""


class Connection(Protocol):
    def cursor(self) -> Any: ...
    def commit(self) -> Any: ...
    def rollback(self) -> Any: ...
    def close(self) -> Any: ...


ConnectionFactory = Callable[[], Connection]


@dataclass(frozen=True, slots=True)
class InvitationGrant:
    invitation_id: str
    email: str
    topic_scopes: tuple[str, ...]
    issued_at: int
    expires_at: int
    code: str | None
    replayed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "invitation_id": self.invitation_id,
            "email": self.email,
            "topic_scopes": list(self.topic_scopes),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "code": self.code,
            "replayed": self.replayed,
        }


@dataclass(frozen=True, slots=True)
class InvitationRecord:
    invitation_id: str
    email: str
    topic_scopes: tuple[str, ...]
    issued_at: int
    expires_at: int
    redeemed_at: int | None
    revoked_at: int | None
    status_value: str | None = None

    @property
    def status(self) -> str:
        if self.status_value is not None:
            return self.status_value
        if self.revoked_at is not None:
            return "revoked"
        if self.redeemed_at is not None:
            return "redeemed"
        if int(time.time()) >= self.expires_at:
            return "expired"
        return "active"

    def to_dict(self) -> dict[str, Any]:
        return {
            "invitation_id": self.invitation_id,
            "email": self.email,
            "topic_scopes": list(self.topic_scopes),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "redeemed_at": self.redeemed_at,
            "revoked_at": self.revoked_at,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    event_type: str
    actor_subject: str
    payload: dict[str, Any]
    idempotency_key: str
    previous_hash: str
    event_hash: str
    created_at: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "actor_subject": self.actor_subject,
            "payload": dict(self.payload),
            "idempotency_key": self.idempotency_key,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
            "created_at": self.created_at,
        }


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS admin_users (
  subject TEXT PRIMARY KEY, email TEXT NOT NULL, role TEXT NOT NULL,
  auth_method TEXT NOT NULL, created_at BIGINT NOT NULL, disabled_at BIGINT
);
CREATE TABLE IF NOT EXISTS admin_sessions (
  session_id TEXT PRIMARY KEY, subject TEXT NOT NULL, email TEXT NOT NULL,
  role TEXT NOT NULL, auth_method TEXT NOT NULL, token_hash_sha256 TEXT NOT NULL UNIQUE,
  created_at BIGINT NOT NULL, expires_at BIGINT NOT NULL, revoked_at BIGINT
);
CREATE TABLE IF NOT EXISTS invitations (
  invitation_id TEXT PRIMARY KEY, email TEXT NOT NULL, topic_scopes JSONB NOT NULL,
  code_hash_sha256 TEXT NOT NULL UNIQUE, issued_by TEXT NOT NULL, issued_at BIGINT NOT NULL,
  expires_at BIGINT NOT NULL, redeemed_at BIGINT, revoked_at BIGINT
);
CREATE TABLE IF NOT EXISTS audit_events (
  sequence BIGSERIAL PRIMARY KEY, event_id TEXT NOT NULL UNIQUE, event_type TEXT NOT NULL,
  actor_subject TEXT NOT NULL, payload JSONB NOT NULL, idempotency_key TEXT NOT NULL UNIQUE,
  previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE, created_at BIGINT NOT NULL
);
-- Idempotency is represented by the unique key on audit_events.  This table
-- name remains reserved for deployments that split operational receipts out.
CREATE TABLE IF NOT EXISTS idempotency_records (
  idempotency_key TEXT PRIMARY KEY, event_id TEXT NOT NULL, created_at BIGINT NOT NULL
);
"""


class AdminService:
    """Permission-checked administrator operations over PostgreSQL."""

    def __init__(
        self,
        connection_factory: ConnectionFactory,
        *,
        clock: Callable[[], int | float] = time.time,
        session_ttl_seconds: int = 12 * 60 * 60,
        invitation_ttl_seconds: int = 7 * 24 * 60 * 60,
    ) -> None:
        if not callable(connection_factory):
            raise AdminValidationError("connection_factory must be callable")
        if type(session_ttl_seconds) is not int or not 1 <= session_ttl_seconds <= 31 * 86400:
            raise AdminValidationError("session_ttl_seconds is out of range")
        if (
            type(invitation_ttl_seconds) is not int
            or not 1 <= invitation_ttl_seconds <= 365 * 86400
        ):
            raise AdminValidationError("invitation_ttl_seconds is out of range")
        self.connection_factory = connection_factory
        self.clock = clock
        self.session_ttl_seconds = session_ttl_seconds
        self.invitation_ttl_seconds = invitation_ttl_seconds

    def ensure_schema(self) -> None:
        with self._transaction() as cursor:
            for statement in SCHEMA_SQL.split(";"):
                if statement.strip():
                    cursor.execute(statement)

    def create_session(
        self,
        identity: AdminIdentity,
        *,
        ttl_seconds: int | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[str, AdminSession]:
        key = _require_key(idempotency_key) if idempotency_key is not None else None
        ttl = self.session_ttl_seconds if ttl_seconds is None else _ttl(ttl_seconds, 31 * 86400)
        now = self._now()
        token = new_session_token()
        session_id = uuid.uuid4().hex
        with self._transaction() as cursor:
            if key:
                prior = self._find_idempotency(cursor, key)
                if prior:
                    payload = prior["payload"]
                    return "", _session_from_payload(payload)
            cursor.execute(
                "INSERT INTO admin_sessions "
                "(admin_session_id, admin_user_id, session_token_hash_sha256, last_activity_at, "
                "session_id, subject, email, role, auth_method, token_hash_sha256, created_at, expires_at) "
                "VALUES (%s,NULL,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    session_id,
                    hash_session_token(token),
                    now,
                    session_id,
                    identity.subject,
                    identity.email,
                    identity.role,
                    identity.auth_method,
                    hash_session_token(token),
                    now,
                    now + ttl,
                ),
            )
            payload = {
                "session_id": session_id,
                "subject": identity.subject,
                "email": identity.email,
                "role": identity.role,
                "auth_method": identity.auth_method,
                "created_at": now,
                "expires_at": now + ttl,
            }
            self._append_audit(
                cursor, identity, "ADMIN_SESSION_CREATED", payload, key or uuid.uuid4().hex, now
            )
        return token, AdminSession(
            session_id,
            identity.subject,
            identity.email,
            identity.role,
            identity.auth_method,
            now,
            now + ttl,
        )

    def authenticate_session(self, token: str) -> AdminSession:
        token_hash = hash_session_token(token)
        now = self._now()
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT session_id, subject, email, role, auth_method, created_at, expires_at, revoked_at, token_hash_sha256 "
                "FROM admin_sessions WHERE token_hash_sha256=%s",
                (token_hash,),
            )
            row = cursor.fetchone()
        if row is None:
            raise AdminSessionError("invalid or inactive administrator session")
        item = _row(
            row,
            (
                "session_id",
                "subject",
                "email",
                "role",
                "auth_method",
                "created_at",
                "expires_at",
                "revoked_at",
                "token_hash_sha256",
            ),
        )
        if (
            not constant_time_token_match(token, str(item["token_hash_sha256"]))
            or item["revoked_at"] is not None
            or now >= int(item["expires_at"])
        ):
            raise AdminSessionError("invalid or inactive administrator session")
        return AdminSession(
            item["session_id"],
            item["subject"],
            item["email"],
            item["role"],
            item["auth_method"],
            int(item["created_at"]),
            int(item["expires_at"]),
            item["revoked_at"],
        )

    def revoke_session(
        self, identity: AdminIdentity, session_id: str, *, idempotency_key: str
    ) -> None:
        require_role(identity, {"security_admin"})
        key = _require_key(idempotency_key)
        with self._transaction() as cursor:
            cursor.execute(
                "UPDATE admin_sessions SET revoked_at=%s WHERE session_id=%s AND revoked_at IS NULL",
                (self._now(), _text(session_id, "session_id", 128)),
            )
            if getattr(cursor, "rowcount", 1) == 0:
                raise AdminNotFoundError("session not found or already revoked")
            self._append_audit(
                cursor,
                identity,
                "ADMIN_SESSION_REVOKED",
                {"session_id": session_id},
                key,
                self._now(),
            )

    def issue_invitation(
        self,
        identity: AdminIdentity,
        *,
        email: str,
        topic_scopes: Iterable[str],
        ttl_seconds: int | None = None,
        idempotency_key: str,
    ) -> InvitationGrant:
        require_role(identity, {"access_admin", "security_admin"})
        key = _require_key(idempotency_key)
        normalized_email = _email(email)
        topics = _topics(topic_scopes)
        ttl = self.invitation_ttl_seconds if ttl_seconds is None else _ttl(ttl_seconds, 365 * 86400)
        now = self._now()
        code = secrets.token_urlsafe(32)
        invitation_id = uuid.uuid4().hex
        request_hash = digest_json(
            {"email": normalized_email, "topic_scopes": list(topics), "ttl_seconds": ttl}
        )
        with self._transaction() as cursor:
            prior = self._find_idempotency(cursor, key)
            if prior:
                if prior["payload"].get("request_hash_sha256") != request_hash:
                    raise AdminConflictError("idempotency key conflicts with another request")
                return self._replayed_invitation(cursor, prior)
            cursor.execute(
                "INSERT INTO invitations "
                "(invitation_id,email,topic_scopes,code_hash_sha256,issued_by,issued_at,expires_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (
                    invitation_id,
                    normalized_email,
                    json.dumps(list(topics)),
                    hashlib.sha256(code.encode()).hexdigest(),
                    identity.subject,
                    now,
                    now + ttl,
                ),
            )
            payload = {
                "invitation_id": invitation_id,
                "email": normalized_email,
                "topic_scopes": list(topics),
                "issued_at": now,
                "expires_at": now + ttl,
                "request_hash_sha256": request_hash,
            }
            self._append_audit(cursor, identity, "INVITATION_ISSUED", payload, key, now)
        return InvitationGrant(invitation_id, normalized_email, topics, now, now + ttl, code)

    def revoke_invitation(
        self, identity: AdminIdentity, invitation_id: str, *, reason: str, idempotency_key: str
    ) -> InvitationRecord:
        require_role(identity, {"access_admin", "security_admin"})
        key = _require_key(idempotency_key)
        identifier = _text(invitation_id, "invitation_id", 128)
        normalized_reason = _text(reason, "reason", 1_000)
        now = self._now()
        request_hash = digest_json({"invitation_id": identifier, "reason": normalized_reason})
        with self._transaction() as cursor:
            prior = self._find_idempotency(cursor, key)
            if prior:
                if prior["payload"].get("request_hash_sha256") != request_hash:
                    raise AdminConflictError("idempotency key conflicts with another request")
                return _invitation_from_payload(prior["payload"])
            cursor.execute(
                "SELECT invitation_id,email,topic_scopes,issued_at,expires_at,redeemed_at,revoked_at FROM invitations WHERE invitation_id=%s FOR UPDATE",
                (identifier,),
            )
            row = cursor.fetchone()
            if row is None:
                raise AdminNotFoundError("invitation not found")
            item = _row(
                row,
                (
                    "invitation_id",
                    "email",
                    "topic_scopes",
                    "issued_at",
                    "expires_at",
                    "redeemed_at",
                    "revoked_at",
                ),
            )
            if item["redeemed_at"] is not None:
                raise AdminConflictError("a redeemed invitation cannot be revoked")
            if item["revoked_at"] is not None:
                raise AdminConflictError("invitation is already revoked")
            cursor.execute(
                "UPDATE invitations SET revoked_at=%s WHERE invitation_id=%s",
                (now, identifier),
            )
            record = InvitationRecord(
                identifier,
                item["email"],
                tuple(_json_list(item["topic_scopes"])),
                int(item["issued_at"]),
                int(item["expires_at"]),
                item["redeemed_at"],
                now,
            )
            audit_payload = {**record.to_dict(), "reason": normalized_reason, "request_hash_sha256": request_hash}
            self._append_audit(cursor, identity, "INVITATION_REVOKED", audit_payload, key, now)
            return record

    def audit_events(self, identity: AdminIdentity, *, limit: int = 100) -> list[AuditEvent]:
        require_role(identity, ADMIN_ROLES)
        if type(limit) is not int or not 1 <= limit <= 1_000:
            raise AdminValidationError("limit must be from 1 to 1000")
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT event_id,event_type,actor_subject,payload,idempotency_key,previous_hash,event_hash,created_at FROM audit_events ORDER BY sequence DESC LIMIT %s",
                (limit,),
            )
            rows = cursor.fetchall() or []
        return [_audit_from_row(row) for row in reversed(rows)]

    def list_invitations(
        self,
        identity: AdminIdentity,
        *,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
    ) -> list[InvitationRecord]:
        """Return invitation metadata; code hashes and plaintext codes are never exposed."""
        require_role(identity, ADMIN_ROLES)
        if type(limit) is not int or not 1 <= limit <= 1_000:
            raise AdminValidationError("limit must be from 1 to 1000")
        if type(offset) is not int or offset < 0:
            raise AdminValidationError("offset must be a non-negative integer")
        now = self._now()
        clauses, params = _invitation_filters(status=status, search=search, now=now)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT invitation_id,email,topic_scopes,issued_at,expires_at,redeemed_at,revoked_at "
                "FROM invitations" + where + " ORDER BY issued_at DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = cursor.fetchall() or []
        return [
            InvitationRecord(
                str(item["invitation_id"]),
                str(item["email"]),
                tuple(_json_list(item["topic_scopes"])),
                int(item["issued_at"]),
                int(item["expires_at"]),
                item["redeemed_at"],
                item["revoked_at"],
                _invitation_status(
                    int(item["expires_at"]), item["redeemed_at"], item["revoked_at"], now
                ),
            )
            for item in (
                _row(
                    row,
                    (
                        "invitation_id",
                        "email",
                        "topic_scopes",
                        "issued_at",
                        "expires_at",
                        "redeemed_at",
                        "revoked_at",
                    ),
                )
                for row in rows
            )
        ]

    def count_invitations(
        self,
        identity: AdminIdentity,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        require_role(identity, ADMIN_ROLES)
        clauses, params = _invitation_filters(status=status, search=search, now=self._now())
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM invitations" + where, tuple(params))
            row = cursor.fetchone()
        return int(row[0] if not isinstance(row, Mapping) else row["count"])

    def list_access_sessions(
        self,
        identity: AdminIdentity,
        *,
        limit: int = 100,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        require_role(identity, ADMIN_ROLES)
        if type(limit) is not int or not 1 <= limit <= 1_000:
            raise AdminValidationError("limit must be from 1 to 1000")
        now = self._now()
        clauses, params = _access_session_filters(status=status, now=now)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT access_session_id,invitation_id,email,topic_scopes,created_at,expires_at,logged_out_at "
                "FROM access_sessions" + where + " ORDER BY created_at DESC LIMIT %s",
                (*params, limit),
            )
            rows = cursor.fetchall() or []
        return [
            {
                "session_id": str(item["access_session_id"]),
                "invitation_id": str(item["invitation_id"]),
                "email": str(item["email"]),
                "topic_scopes": _json_list(item["topic_scopes"]),
                "created_at": int(item["created_at"]),
                "expires_at": int(item["expires_at"]),
                "logged_out_at": item["logged_out_at"],
                "status": _access_session_status(
                    int(item["expires_at"]), item["logged_out_at"], now
                ),
            }
            for item in (
                _row(
                    row,
                    (
                        "access_session_id",
                        "invitation_id",
                        "email",
                        "topic_scopes",
                        "created_at",
                        "expires_at",
                        "logged_out_at",
                    ),
                )
                for row in rows
            )
        ]

    def list_applications(
        self,
        identity: AdminIdentity,
        *,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        require_role(identity, ADMIN_ROLES)
        if type(limit) is not int or not 1 <= limit <= 1_000:
            raise AdminValidationError("limit must be from 1 to 1000")
        if type(offset) is not int or offset < 0:
            raise AdminValidationError("offset must be a non-negative integer")
        clauses, params = _application_filters(status=status, search=search)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT application_id,status,email,institution,research_role,research_direction,submitted_at FROM applications"
                + where + " ORDER BY submitted_at DESC LIMIT %s OFFSET %s", (*params, limit, offset),
            )
            rows = cursor.fetchall() or []
        return [_row(row, ("application_id", "status", "email", "institution", "research_role", "research_direction", "submitted_at")) for row in rows]

    def count_applications(
        self,
        identity: AdminIdentity,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        require_role(identity, ADMIN_ROLES)
        clauses, params = _application_filters(status=status, search=search)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM applications" + where, tuple(params))
            row = cursor.fetchone()
        return int(row[0] if not isinstance(row, Mapping) else row["count"])

    def _replayed_invitation(self, cursor: Any, prior: Mapping[str, Any]) -> InvitationGrant:
        payload = prior["payload"]
        cursor.execute(
            "SELECT invitation_id,email,topic_scopes,issued_at,expires_at FROM invitations WHERE invitation_id=%s",
            (payload["invitation_id"],),
        )
        row = cursor.fetchone()
        if row is None:
            raise AdminStateError("idempotency record references missing invitation")
        item = _row(row, ("invitation_id", "email", "topic_scopes", "issued_at", "expires_at"))
        return InvitationGrant(
            item["invitation_id"],
            item["email"],
            tuple(_json_list(item["topic_scopes"])),
            int(item["issued_at"]),
            int(item["expires_at"]),
            None,
            True,
        )

    def _append_audit(
        self,
        cursor: Any,
        identity: AdminIdentity,
        event_type: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
        created_at: int,
    ) -> AuditEvent:
        prior = self._find_idempotency(cursor, idempotency_key)
        if prior:
            return _audit_from_mapping(prior)
        cursor.execute(
            "SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1 FOR UPDATE"
        )
        row = cursor.fetchone()
        previous = str(_row(row, ("event_hash",))["event_hash"]) if row is not None else "0" * 64
        event_id = uuid.uuid4().hex
        unsigned = {
            "event_id": event_id,
            "event_type": event_type,
            "actor_subject": identity.subject,
            "payload": dict(payload),
            "idempotency_key": idempotency_key,
            "previous_hash": previous,
            "created_at": created_at,
        }
        event_hash = digest_json(unsigned)
        cursor.execute(
            "INSERT INTO audit_events (audit_event_id,chain_sequence,occurred_at,action,object_type,object_id,result,event_summary,previous_event_hash_sha256,event_hash_sha256,event_id,event_type,actor_subject,payload,idempotency_key,previous_hash,event_hash,created_at) "
            "VALUES (%s,(SELECT COALESCE(MAX(chain_sequence),0)+1 FROM audit_events),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                event_id,
                created_at,
                event_type,
                "admin",
                str(payload.get("invitation_id") or payload.get("session_id") or "admin"),
                "success",
                json.dumps(dict(payload)),
                previous,
                event_hash,
                event_id,
                event_type,
                identity.subject,
                json.dumps(dict(payload)),
                idempotency_key,
                previous,
                event_hash,
                created_at,
            ),
        )
        return AuditEvent(
            event_id,
            event_type,
            identity.subject,
            dict(payload),
            idempotency_key,
            previous,
            event_hash,
            created_at,
        )

    def _find_idempotency(self, cursor: Any, key: str) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT event_id,event_type,actor_subject,payload,idempotency_key,previous_hash,event_hash,created_at FROM audit_events WHERE idempotency_key=%s",
            (key,),
        )
        row = cursor.fetchone()
        return None if row is None else _audit_mapping(row)

    @contextmanager
    def _transaction(self) -> Iterator[Any]:
        connection = self.connection_factory()
        if connection is None:
            raise AdminStateError("connection_factory returned None")
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            finally:
                cursor.close() if hasattr(cursor, "close") else None
            raise
        else:
            cursor.close() if hasattr(cursor, "close") else None
        finally:
            connection.close() if hasattr(connection, "close") else None

    def _now(self) -> int:
        value = self.clock()
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise AdminStateError("clock must return a non-negative timestamp")
        return int(value)


def psycopg_connection_factory(dsn: str) -> ConnectionFactory:
    """Build a factory while keeping psycopg an optional runtime dependency."""

    if not isinstance(dsn, str) or not dsn.strip():
        raise AdminValidationError("dsn is required")

    def connect() -> Connection:
        try:
            import psycopg
        except ImportError as exc:
            raise AdminStateError("psycopg is required for PostgreSQL access") from exc
        return cast(Connection, psycopg.connect(dsn))

    return connect


def _require_key(value: str | None) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 256
        or any(ord(c) < 32 for c in value)
    ):
        raise AdminValidationError("idempotency_key is required")
    return value.strip()


def _ttl(value: int, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise AdminValidationError("ttl_seconds is out of range")
    return value


def _text(value: Any, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.strip()) > maximum
        or any(ord(c) < 32 for c in value)
    ):
        raise AdminValidationError(f"{label} is invalid")
    return value.strip()


def _email(value: Any) -> str:
    normalized = _text(value, "email", 254).casefold()
    if (
        normalized.count("@") != 1
        or "." not in normalized.rsplit("@", 1)[1]
        or any(c.isspace() for c in normalized)
    ):
        raise AdminValidationError("email must be a valid address")
    return normalized


def _topics(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise AdminValidationError("topic_scopes must be an iterable")
    try:
        result = tuple(_text(value, "topic scope", 128) for value in values)
    except TypeError as exc:
        raise AdminValidationError("topic_scopes must be an iterable") from exc
    if not result or len(result) > 100 or len(set(result)) != len(result):
        raise AdminValidationError("topic_scopes must be non-empty and unique")
    return result


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise AdminStateError("stored topic scopes are invalid")
    return value


_INVITATION_STATUSES = frozenset({"active", "redeemed", "revoked", "expired"})
_ACCESS_SESSION_STATUSES = frozenset({"active", "logged_out", "expired"})


def _access_session_filters(
    *, status: str | None, now: int
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status is not None:
        normalized = _text(status, "status", 32).casefold()
        if normalized not in _ACCESS_SESSION_STATUSES:
            raise AdminValidationError("status is invalid")
        if normalized == "active":
            clauses.append("logged_out_at IS NULL AND expires_at > %s")
            params.append(now)
        elif normalized == "logged_out":
            clauses.append("logged_out_at IS NOT NULL")
        else:
            clauses.append("logged_out_at IS NULL AND expires_at <= %s")
            params.append(now)
    return clauses, params


def _access_session_status(expires_at: int, logged_out_at: Any, now: int) -> str:
    if logged_out_at is not None:
        return "logged_out"
    return "expired" if now >= expires_at else "active"


def _invitation_filters(
    *, status: str | None, search: str | None, now: int
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status is not None:
        normalized = _text(status, "status", 32).casefold()
        if normalized not in _INVITATION_STATUSES:
            raise AdminValidationError("status is invalid")
        if normalized == "active":
            clauses.append("revoked_at IS NULL AND redeemed_at IS NULL AND expires_at > %s")
            params.append(now)
        elif normalized == "redeemed":
            clauses.append("redeemed_at IS NOT NULL")
        elif normalized == "revoked":
            clauses.append("revoked_at IS NOT NULL")
        else:
            clauses.append("revoked_at IS NULL AND redeemed_at IS NULL AND expires_at <= %s")
            params.append(now)
    if search is not None:
        search_value = _text(search, "search", 254).casefold()
        clauses.append("(lower(email) LIKE %s OR lower(invitation_id) LIKE %s)")
        params.extend([f"%{search_value}%", f"%{search_value}%"])
    return clauses, params


def _invitation_status(
    expires_at: int, redeemed_at: Any, revoked_at: Any, now: int
) -> str:
    if revoked_at is not None:
        return "revoked"
    if redeemed_at is not None:
        return "redeemed"
    return "expired" if now >= expires_at else "active"


def _application_filters(
    *, status: str | None, search: str | None
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status is not None:
        clauses.append("status=%s")
        params.append(_text(status, "status", 32))
    if search is not None:
        search_value = _text(search, "search", 254).casefold()
        clauses.append("(lower(email) LIKE %s OR lower(institution) LIKE %s)")
        params.extend([f"%{search_value}%", f"%{search_value}%"])
    return clauses, params


def _row(row: Any, names: tuple[str, ...]) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return {name: row[name] for name in names}
    return dict(zip(names, row, strict=True))


def _audit_mapping(row: Any) -> dict[str, Any]:
    item = _row(
        row,
        (
            "event_id",
            "event_type",
            "actor_subject",
            "payload",
            "idempotency_key",
            "previous_hash",
            "event_hash",
            "created_at",
        ),
    )
    payload = item["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise AdminStateError("audit payload is invalid")
    item["payload"] = payload
    return item


def _audit_from_mapping(item: Mapping[str, Any]) -> AuditEvent:
    return AuditEvent(
        str(item["event_id"]),
        str(item["event_type"]),
        str(item["actor_subject"]),
        dict(item["payload"]),
        str(item["idempotency_key"]),
        str(item["previous_hash"]),
        str(item["event_hash"]),
        int(item["created_at"]),
    )


def _audit_from_row(row: Any) -> AuditEvent:
    return _audit_from_mapping(_audit_mapping(row))


def _session_from_payload(payload: Mapping[str, Any]) -> AdminSession:
    return AdminSession(
        str(payload["session_id"]),
        str(payload["subject"]),
        str(payload["email"]),
        str(payload["role"]),
        str(payload["auth_method"]),
        int(payload["created_at"]),
        int(payload["expires_at"]),
    )


def _invitation_from_payload(payload: Mapping[str, Any]) -> InvitationRecord:
    return InvitationRecord(
        str(payload["invitation_id"]),
        str(payload["email"]),
        tuple(_json_list(payload["topic_scopes"])),
        int(payload["issued_at"]),
        int(payload["expires_at"]),
        payload.get("redeemed_at"),
        payload.get("revoked_at"),
    )


__all__ = [
    "SCHEMA_SQL",
    "AdminConflictError",
    "AdminNotFoundError",
    "AdminService",
    "AdminServiceError",
    "AdminStateError",
    "AdminValidationError",
    "AuditEvent",
    "ConnectionFactory",
    "InvitationGrant",
    "InvitationRecord",
    "psycopg_connection_factory",
]
