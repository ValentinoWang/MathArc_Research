"""Import the legacy access-state JSON into PostgreSQL.

The source file is an input-only artifact.  This command never writes to it;
``--verify-only`` can therefore be used on an offline machine without
installing psycopg.  Database writes are transactional and repeatable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "1.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DEFAULT_SOURCE = "/var/lib/matharc-research/access/access-state.json"
_REQUIRED_TABLES = (
    "admin_users",
    "admin_sessions",
    "applications",
    "invitations",
    "access_sessions",
    "audit_events",
    "idempotency_records",
)


class MigrationError(RuntimeError):
    """Raised for invalid source state or unavailable migration resources."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Mapping[str, Any]) -> str:
    unsigned = dict(value)
    unsigned.pop("state_digest_sha256", None)
    return hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()


def _text(value: object, label: str, maximum: int = 2_000) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or value != value.strip():
        raise MigrationError(f"{label} must be a bounded non-empty string")
    if any(ord(char) < 32 for char in value):
        raise MigrationError(f"{label} contains a control character")
    return value


def _timestamp(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MigrationError(f"{label} must be a non-negative integer timestamp")
    return value


def _email(value: object, label: str) -> str:
    email = _text(value, label, 254).casefold()
    if email.count("@") != 1 or any(char.isspace() for char in email):
        raise MigrationError(f"{label} must be a canonical email address")
    local, domain = email.split("@")
    if not local or not domain or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise MigrationError(f"{label} must be a canonical email address")
    return email


def _hash(value: object, label: str) -> str:
    result = _text(value, label, 64)
    if not _SHA256_RE.fullmatch(result):
        raise MigrationError(f"{label} must be a lowercase SHA-256 digest")
    return result


def _scopes(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise MigrationError(f"{label} must be a non-empty array of strings")
    result = [_text(item, f"{label} item", 128) for item in value]
    if len(set(result)) != len(result):
        raise MigrationError(f"{label} contains duplicate entries")
    return result


def load_source(path: Path) -> dict[str, Any]:
    """Read and validate source JSON without changing its bytes or metadata."""

    if path.is_symlink():
        raise MigrationError(f"source JSON must not be a symbolic link: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationError(f"source JSON is unreadable: {path}") from exc
    if not isinstance(value, dict):
        raise MigrationError("source JSON must be an object")
    required = {"schema_version", "applications", "invitations", "sessions", "state_digest_sha256"}
    if set(value) != required:
        raise MigrationError(
            f"source JSON fields mismatch: missing={sorted(required - set(value))}, "
            f"unknown={sorted(set(value) - required)}"
        )
    if value["schema_version"] != _SCHEMA_VERSION:
        raise MigrationError(f"unsupported access-state schema version: {value['schema_version']!r}")
    if value["state_digest_sha256"] != _digest(value):
        raise MigrationError("source JSON state digest mismatch")
    for field in ("applications", "invitations", "sessions"):
        if not isinstance(value[field], list):
            raise MigrationError(f"source JSON {field} must be an array")

    applications: list[dict[str, Any]] = []
    application_ids: set[str] = set()
    app_fields = {"application_id", "status", "email", "institution", "research_role", "research_direction", "purpose", "submitted_at"}
    for index, raw in enumerate(value["applications"]):
        if not isinstance(raw, dict) or set(raw) != app_fields:
            raise MigrationError(f"applications[{index}] fields mismatch")
        item = dict(raw)
        item["application_id"] = _text(item["application_id"], "application_id", 128)
        if item["application_id"] in application_ids:
            raise MigrationError("duplicate application_id")
        application_ids.add(item["application_id"])
        if item["status"] != "PENDING":
            raise MigrationError("application status must be PENDING")
        item["email"] = _email(item["email"], "application email")
        for field, maximum in (("institution", 300), ("research_role", 200), ("research_direction", 500), ("purpose", 2_000)):
            item[field] = _text(item[field], field, maximum)
        item["submitted_at"] = _timestamp(item["submitted_at"], "submitted_at")
        applications.append(item)

    invitations: list[dict[str, Any]] = []
    invitation_by_id: dict[str, dict[str, Any]] = {}
    hashes: set[str] = set()
    invite_fields = {"invitation_id", "email", "topic_scopes", "code_hash_sha256", "issued_at", "expires_at", "redeemed_at", "revoked_at"}
    for index, raw in enumerate(value["invitations"]):
        if not isinstance(raw, dict) or set(raw) != invite_fields:
            raise MigrationError(f"invitations[{index}] fields mismatch")
        item = dict(raw)
        item["invitation_id"] = _text(item["invitation_id"], "invitation_id", 128)
        if item["invitation_id"] in invitation_by_id:
            raise MigrationError("duplicate invitation_id")
        item["email"] = _email(item["email"], "invitation email")
        item["topic_scopes"] = _scopes(item["topic_scopes"], "topic_scopes")
        item["code_hash_sha256"] = _hash(item["code_hash_sha256"], "code_hash_sha256")
        if item["code_hash_sha256"] in hashes:
            raise MigrationError("duplicate invitation code hash")
        hashes.add(item["code_hash_sha256"])
        item["issued_at"] = _timestamp(item["issued_at"], "issued_at")
        item["expires_at"] = _timestamp(item["expires_at"], "expires_at")
        if item["expires_at"] <= item["issued_at"]:
            raise MigrationError("invitation must expire after issuance")
        for field in ("redeemed_at", "revoked_at"):
            if item[field] is not None:
                item[field] = _timestamp(item[field], field)
        if item["redeemed_at"] is not None and not item["issued_at"] <= item["redeemed_at"] < item["expires_at"]:
            raise MigrationError("invitation redemption timestamp is invalid")
        if item["revoked_at"] is not None and item["revoked_at"] < item["issued_at"]:
            raise MigrationError("invitation revocation timestamp is invalid")
        if item["redeemed_at"] is not None and item["revoked_at"] is not None:
            raise MigrationError("invitation cannot be both redeemed and revoked")
        invitation_by_id[item["invitation_id"]] = item
        invitations.append(item)

    sessions: list[dict[str, Any]] = []
    session_ids: set[str] = set()
    token_hashes: set[str] = set()
    session_invites: set[str] = set()
    session_fields = {"session_id", "invitation_id", "email", "topic_scopes", "token_hash_sha256", "created_at", "expires_at", "logged_out_at"}
    for index, raw in enumerate(value["sessions"]):
        if not isinstance(raw, dict) or set(raw) != session_fields:
            raise MigrationError(f"sessions[{index}] fields mismatch")
        item = dict(raw)
        item["session_id"] = _text(item["session_id"], "session_id", 128)
        item["invitation_id"] = _text(item["invitation_id"], "invitation_id", 128)
        if item["session_id"] in session_ids or item["invitation_id"] in session_invites:
            raise MigrationError("duplicate session_id or invitation session")
        invitation = invitation_by_id.get(item["invitation_id"])
        if invitation is None:
            raise MigrationError("session refers to an unknown invitation")
        item["email"] = _email(item["email"], "session email")
        item["topic_scopes"] = _scopes(item["topic_scopes"], "session topic_scopes")
        item["token_hash_sha256"] = _hash(item["token_hash_sha256"], "token_hash_sha256")
        if item["token_hash_sha256"] in token_hashes:
            raise MigrationError("duplicate session token hash")
        token_hashes.add(item["token_hash_sha256"])
        item["created_at"] = _timestamp(item["created_at"], "created_at")
        item["expires_at"] = _timestamp(item["expires_at"], "expires_at")
        if item["expires_at"] <= item["created_at"]:
            raise MigrationError("session must expire after creation")
        if item["logged_out_at"] is not None:
            item["logged_out_at"] = _timestamp(item["logged_out_at"], "logged_out_at")
            if item["logged_out_at"] < item["created_at"]:
                raise MigrationError("session logout timestamp is invalid")
        if (invitation["redeemed_at"] != item["created_at"] or invitation["revoked_at"] is not None or invitation["email"] != item["email"] or invitation["topic_scopes"] != item["topic_scopes"]):
            raise MigrationError("session does not match its redeemed invitation")
        session_ids.add(item["session_id"])
        session_invites.add(item["invitation_id"])
        sessions.append(item)
    return {"applications": applications, "invitations": invitations, "sessions": sessions, "state_digest_sha256": value["state_digest_sha256"]}


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ImportError as exc:
        raise MigrationError("psycopg is required for database migration; install psycopg[binary]>=3.1") from exc
    try:
        return psycopg.connect(dsn)
    except Exception as exc:  # psycopg exposes several connection error subclasses
        raise MigrationError(f"could not connect to PostgreSQL: {exc}") from exc


def _schema_sql() -> str:
    path = Path(__file__).resolve().parents[2] / "migrations" / "001_admin_access.sql"
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MigrationError(f"migration SQL is unreadable: {path}") from exc


def _json(value: object) -> str:
    return _canonical(value)


def migrate(source: Mapping[str, Any], dsn: str) -> None:
    connection = _connect(dsn)
    try:
        with connection.transaction():
            # Keep statements separate so this works with psycopg's extended
            # protocol as well as DB-compatible connection wrappers.
            for statement in _schema_sql().split(";"):
                if statement.strip():
                    connection.execute(statement)
            for item in source["applications"]:
                connection.execute(
                    """INSERT INTO applications (application_id, status, email, institution, research_role, research_direction, purpose, submitted_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (application_id) DO NOTHING""",
                    (item["application_id"], item["status"], item["email"], item["institution"], item["research_role"], item["research_direction"], item["purpose"], item["submitted_at"]),
                )
            for item in source["invitations"]:
                connection.execute(
                    """INSERT INTO invitations (invitation_id, email, topic_scopes, code_hash_sha256, issued_at, expires_at, redeemed_at, revoked_at)
                    VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s) ON CONFLICT (invitation_id) DO NOTHING""",
                    (item["invitation_id"], item["email"], _json(item["topic_scopes"]), item["code_hash_sha256"], item["issued_at"], item["expires_at"], item["redeemed_at"], item["revoked_at"]),
                )
            for item in source["sessions"]:
                connection.execute(
                    """INSERT INTO access_sessions (access_session_id, invitation_id, email, topic_scopes, token_hash_sha256, created_at, expires_at, logged_out_at)
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s) ON CONFLICT (access_session_id) DO NOTHING""",
                    (item["session_id"], item["invitation_id"], item["email"], _json(item["topic_scopes"]), item["token_hash_sha256"], item["created_at"], item["expires_at"], item["logged_out_at"]),
                )
    except MigrationError:
        raise
    except Exception as exc:
        raise MigrationError(f"PostgreSQL migration failed; transaction rolled back: {exc}") from exc
    finally:
        connection.close()


def verify_database(source: Mapping[str, Any], dsn: str) -> None:
    connection = _connect(dsn)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = current_schema() AND tablename = ANY(%s)",
                (list(_REQUIRED_TABLES),),
            )
            present = {row[0] for row in cursor.fetchall()}
            missing = sorted(set(_REQUIRED_TABLES) - present)
            if missing:
                raise MigrationError(f"database schema is missing tables: {', '.join(missing)}")
            expected = {"applications": len(source["applications"]), "invitations": len(source["invitations"]), "access_sessions": len(source["sessions"])}
            for table, count in expected.items():
                cursor.execute(f"SELECT count(*) FROM {table}")
                actual = int(cursor.fetchone()[0])
                if actual < count:
                    raise MigrationError(f"database table {table} has {actual} rows; source requires at least {count}")
    except MigrationError:
        raise
    except Exception as exc:
        raise MigrationError(f"database verification failed: {exc}") from exc
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_positional", nargs="?", type=Path, help="legacy access-state JSON path")
    parser.add_argument("--source", "--source-json", dest="source", type=Path, help="legacy access-state JSON path")
    parser.add_argument("--database-url", "--dsn", dest="dsn", help="PostgreSQL DSN (or MATHARC_DATABASE_URL)")
    parser.add_argument("--verify-only", action="store_true", help="validate source and optionally verify database without writes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_path = args.source or args.source_positional or Path(os.getenv("MATHARC_ACCESS_SOURCE", _DEFAULT_SOURCE))
    try:
        source = load_source(source_path)
        dsn = args.dsn or os.getenv("MATHARC_ADMIN_DATABASE_URL") or os.getenv("MATHARC_DATABASE_URL") or os.getenv("DATABASE_URL")
        if args.verify_only:
            if dsn:
                verify_database(source, dsn)
                print(f"verified source and PostgreSQL schema: {source_path}")
            else:
                print(f"verified source JSON (database not checked; no DSN supplied): {source_path}")
            return 0
        if not dsn:
            raise MigrationError("a PostgreSQL DSN is required (use --database-url or MATHARC_DATABASE_URL)")
        migrate(source, dsn)
        print(f"migrated access JSON to PostgreSQL without modifying source: {source_path}")
        return 0
    except MigrationError as exc:
        print(f"admin migration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
