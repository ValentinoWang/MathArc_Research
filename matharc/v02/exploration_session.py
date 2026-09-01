"""Append-only local exploration sessions, isolated from research workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .local_store import (
    LocalStoreError,
    exclusive_lock,
    external_root,
    read_json,
    require_digest,
    state_digest,
    strict_mapping,
    write_json_atomic,
)
from .schema import canonical_json, digest_json, utc_now


_PROVENANCE = {"run_id", "state_digest_sha256", "event_head_hash"}


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LocalStoreError(f"{label} must be non-empty text")
    return value


def _json_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise LocalStoreError(f"{label} must be an object")
    try:
        return __import__("json").loads(canonical_json(dict(value)))
    except (TypeError, ValueError) as exc:
        raise LocalStoreError(f"{label} must be JSON-safe") from exc


@dataclass(frozen=True, slots=True)
class ExplorationEntry:
    entry_id: str
    kind: str
    payload: Mapping[str, Any]
    created_at: str

    def __post_init__(self) -> None:
        _text(self.entry_id, "entry_id")
        if self.kind not in {"CONJECTURE", "EXPERIMENT"}:
            raise LocalStoreError("entry kind must be CONJECTURE or EXPERIMENT")
        _json_object(self.payload, "entry payload")
        _text(self.created_at, "created_at")

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "entry_id": self.entry_id,
            "kind": self.kind,
            "payload": _json_object(self.payload, "entry payload"),
            "created_at": self.created_at,
        }
        if include_digest:
            result["entry_digest_sha256"] = self.digest_sha256
        return result

    @classmethod
    def from_dict(cls, value: object) -> "ExplorationEntry":
        data = strict_mapping(
            value,
            {"entry_id", "kind", "payload", "created_at", "entry_digest_sha256"},
            "exploration entry",
        )
        entry = cls(
            entry_id=_text(data["entry_id"], "entry_id"),
            kind=_text(data["kind"], "kind"),
            payload=_json_object(data["payload"], "entry payload"),
            created_at=_text(data["created_at"], "created_at"),
        )
        if data["entry_digest_sha256"] != entry.digest_sha256:
            raise LocalStoreError("exploration entry digest mismatch")
        return entry


@dataclass(frozen=True, slots=True)
class ExplorationSession:
    session_id: str
    workspace_provenance: Mapping[str, str]
    created_at: str
    entries: tuple[ExplorationEntry, ...] = ()

    def __post_init__(self) -> None:
        _text(self.session_id, "session_id")
        if set(self.workspace_provenance) != _PROVENANCE:
            raise LocalStoreError("workspace provenance fields mismatch")
        _text(self.workspace_provenance["run_id"], "run_id")
        require_digest(self.workspace_provenance["state_digest_sha256"], "state_digest_sha256")
        require_digest(self.workspace_provenance["event_head_hash"], "event_head_hash")
        if tuple(item.entry_id for item in self.entries) != tuple(sorted(item.entry_id for item in self.entries)):
            raise LocalStoreError("session entries must be ordered by entry_id")
        if len({item.entry_id for item in self.entries}) != len(self.entries):
            raise LocalStoreError("session entry ids must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "workspace_provenance": dict(self.workspace_provenance),
            "created_at": self.created_at,
            "entries": [item.to_dict() for item in self.entries],
        }

    @classmethod
    def from_dict(cls, value: object) -> "ExplorationSession":
        data = strict_mapping(value, {"session_id", "workspace_provenance", "created_at", "entries"}, "exploration session")
        entries = data["entries"]
        if not isinstance(entries, list):
            raise LocalStoreError("session entries must be an array")
        provenance = _json_object(data["workspace_provenance"], "workspace provenance")
        if not all(isinstance(item, str) for item in provenance.values()):
            raise LocalStoreError("workspace provenance values must be text")
        return cls(
            _text(data["session_id"], "session_id"),
            provenance,
            _text(data["created_at"], "created_at"),
            tuple(ExplorationEntry.from_dict(item) for item in entries),
        )


class ExplorationSessionStore:
    """A lock-safe session collection that never writes into a workspace."""

    _FILENAME = "exploration-sessions.json"

    def __init__(self, root: str) -> None:
        self.root = external_root(root)
        self.path = self.root / self._FILENAME

    def _load_state(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": "1.0", "sessions": [], "state_digest_sha256": ""}
        data = strict_mapping(read_json(self.path, "exploration session state"), {"schema_version", "sessions", "state_digest_sha256"}, "exploration session state")
        if data["schema_version"] != "1.0" or not isinstance(data["sessions"], list):
            raise LocalStoreError("unsupported exploration session state")
        if data["state_digest_sha256"] != state_digest(data):
            raise LocalStoreError("exploration session state digest mismatch")
        sessions = [ExplorationSession.from_dict(item) for item in data["sessions"]]
        if [item.session_id for item in sessions] != sorted(item.session_id for item in sessions):
            raise LocalStoreError("sessions must be ordered by session_id")
        return {"schema_version": "1.0", "sessions": [item.to_dict() for item in sessions], "state_digest_sha256": data["state_digest_sha256"]}

    def _save(self, sessions: list[ExplorationSession]) -> None:
        payload: dict[str, Any] = {"schema_version": "1.0", "sessions": [item.to_dict() for item in sorted(sessions, key=lambda item: item.session_id)]}
        payload["state_digest_sha256"] = state_digest(payload)
        write_json_atomic(self.path, payload)

    def create(self, session_id: str, workspace_provenance: Mapping[str, str], *, created_at: str | None = None) -> ExplorationSession:
        session = ExplorationSession(session_id, dict(workspace_provenance), created_at or utc_now())
        with exclusive_lock(self.root, self._FILENAME):
            sessions = [ExplorationSession.from_dict(item) for item in self._load_state()["sessions"]]
            existing = next((item for item in sessions if item.session_id == session_id), None)
            if existing is not None:
                if existing.to_dict() == session.to_dict():
                    return existing
                raise LocalStoreError("duplicate exploration session id")
            sessions.append(session)
            self._save(sessions)
        return session

    def load(self, session_id: str) -> ExplorationSession:
        for item in self.list():
            if item.session_id == session_id:
                return item
        raise KeyError(f"unknown exploration session: {session_id}")

    def list(self) -> tuple[ExplorationSession, ...]:
        return tuple(ExplorationSession.from_dict(item) for item in self._load_state()["sessions"])

    def append(self, session_id: str, entry: ExplorationEntry) -> ExplorationSession:
        with exclusive_lock(self.root, self._FILENAME):
            sessions = [ExplorationSession.from_dict(item) for item in self._load_state()["sessions"]]
            for index, session in enumerate(sessions):
                if session.session_id != session_id:
                    continue
                prior = next((item for item in session.entries if item.entry_id == entry.entry_id), None)
                if prior is not None:
                    if prior.to_dict() == entry.to_dict():
                        return session
                    raise LocalStoreError("duplicate exploration entry id")
                updated = ExplorationSession(session.session_id, session.workspace_provenance, session.created_at, tuple(sorted((*session.entries, entry), key=lambda item: item.entry_id)))
                sessions[index] = updated
                self._save(sessions)
                return updated
        raise KeyError(f"unknown exploration session: {session_id}")
