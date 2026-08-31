"""Append-only local operations ledger with no research-engine dependency."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, cast


class OperationsLedgerError(ValueError):
    pass


_KINDS = frozenset({"ACCOUNT_CREATED", "BALANCE_CREDITED", "SEAT_SET", "UPSTREAM_CONFIGURED", "USAGE_RECORDED"})
_RECORD_KEYS = frozenset(
    {"record_id", "kind", "payload", "previous_digest_sha256", "record_digest_sha256"}
)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require_digest(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
        raise OperationsLedgerError("research_replay_digest must be a lowercase SHA-256 digest")
    return value


class OperationsLedger:
    """A file-backed ledger that records operations without importing v0.2."""

    def __init__(self, path: str | Path, research_replay_digest: str) -> None:
        self.path = Path(path)
        self.research_replay_digest = _require_digest(research_replay_digest)
        self._state = self._load_or_create()

    def _load_or_create(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": "1.0", "research_replay_digest": self.research_replay_digest, "records": []}
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OperationsLedgerError("operations ledger is unreadable") from exc
        if not isinstance(state, dict) or set(state) != {"schema_version", "research_replay_digest", "records"}:
            raise OperationsLedgerError("operations ledger schema is invalid")
        if state["schema_version"] != "1.0" or state["research_replay_digest"] != self.research_replay_digest:
            raise OperationsLedgerError("operations ledger belongs to another research replay")
        if not isinstance(state["records"], list):
            raise OperationsLedgerError("operations ledger records are invalid")
        prior_records: list[dict[str, Any]] = []
        previous = _digest(prior_records)
        for item in state["records"]:
            self._validate_record(item, previous)
            prior_records.append(item)
            previous = _digest(prior_records)
        identifiers = [item["record_id"] for item in prior_records]
        if len(set(identifiers)) != len(identifiers):
            raise OperationsLedgerError("operations ledger has duplicate record ids")
        return state

    @staticmethod
    def _validate_record(item: object, previous: str) -> None:
        if not isinstance(item, dict) or set(item) != _RECORD_KEYS:
            raise OperationsLedgerError("operations ledger record schema is invalid")
        if not isinstance(item["record_id"], str) or not item["record_id"].strip():
            raise OperationsLedgerError("operations ledger record id is invalid")
        if (
            not isinstance(item["kind"], str)
            or item["kind"] not in _KINDS
            or not isinstance(item["payload"], dict)
        ):
            raise OperationsLedgerError("operations ledger record content is invalid")
        unsigned = {
            "record_id": item["record_id"],
            "kind": item["kind"],
            "payload": item["payload"],
            "previous_digest_sha256": item["previous_digest_sha256"],
        }
        if (
            item["previous_digest_sha256"] != previous
            or item["record_digest_sha256"] != _digest(unsigned)
        ):
            raise OperationsLedgerError("operations ledger history integrity check failed")

    @property
    def records(self) -> tuple[dict[str, Any], ...]:
        # A shallow copy would let a caller mutate ``payload`` in memory and
        # later persist a history that no longer matches its recorded digest.
        return tuple(json.loads(_canonical(item)) for item in self._state["records"])

    def append(self, *, record_id: str, kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(record_id, str) or not record_id.strip():
            raise OperationsLedgerError("record_id must be non-empty")
        if not isinstance(kind, str) or kind not in _KINDS:
            raise OperationsLedgerError("unsupported operations record kind")
        if not isinstance(payload, Mapping):
            raise OperationsLedgerError("operations payload must be an object")
        try:
            canonical_payload = json.loads(_canonical(dict(payload)))
        except (TypeError, ValueError) as exc:
            raise OperationsLedgerError("operations payload must be JSON-safe") from exc
        for name, value in canonical_payload.items():
            if name.endswith(("amount", "seats", "tokens")) and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise OperationsLedgerError(f"{name} must be a non-negative integer")
        with self._exclusive_lock():
            current = self._load_or_create()
            if any(item["record_id"] == record_id for item in current["records"]):
                raise OperationsLedgerError("duplicate operations record id")
            candidate = cast(dict[str, Any], json.loads(_canonical(current)))
            record = {
                "record_id": record_id,
                "kind": kind,
                "payload": canonical_payload,
                "previous_digest_sha256": _digest(candidate["records"]),
            }
            record["record_digest_sha256"] = _digest(record)
            candidate["records"].append(record)
            self._persist(candidate)
            self._state = candidate
        return cast(dict[str, Any], json.loads(_canonical(record)))

    @property
    def head_digest(self) -> str:
        return _digest(self._state["records"])

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "research_replay_digest": self.research_replay_digest,
            "operations_head_digest_sha256": self.head_digest,
            "record_count": len(self._state["records"]),
            "external_payment": "not_configured",
            "external_identity": "not_configured",
        }

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.parent / f".{self.path.name}.lock"
        descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _persist(self, state: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(_canonical(state) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)
