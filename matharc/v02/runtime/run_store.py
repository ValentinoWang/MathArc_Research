"""Durable runtime event log, snapshot replay, and idempotent import ledger."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import fcntl

from ..schema import canonical_json, digest_json, utc_now
from .candidate import envelope_dict, source_identity

GENESIS_HASH = "0" * 64


def _generation_number(value: str) -> int | None:
    text = str(value)
    if text[:1].lower() == "g" and text[1:].isdigit():
        return int(text[1:])
    return None


class RuntimeStoreError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    sequence: int
    event_id: str
    event_type: str
    payload: Mapping[str, Any]
    previous_hash: str
    timestamp: str
    event_hash: str

    def unsigned(self) -> dict[str, Any]:
        return {"sequence": self.sequence, "event_id": self.event_id, "event_type": self.event_type,
                "payload": dict(self.payload), "previous_hash": self.previous_hash, "timestamp": self.timestamp}

    def to_dict(self) -> dict[str, Any]:
        value = self.unsigned()
        value["event_hash"] = self.event_hash
        return value

    @classmethod
    def create(cls, sequence: int, event_type: str, payload: Mapping[str, Any], previous_hash: str) -> "RuntimeEvent":
        unsigned = {"sequence": sequence, "event_id": str(uuid.uuid4()), "event_type": event_type,
                    "payload": dict(payload), "previous_hash": previous_hash, "timestamp": utc_now()}
        return cls(**unsigned, event_hash=digest_json(unsigned))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RuntimeEvent":
        required = {"sequence", "event_id", "event_type", "payload", "previous_hash", "timestamp", "event_hash"}
        unknown = set(value) - required
        if unknown or required - set(value):
            raise RuntimeStoreError(f"invalid runtime event fields: missing={sorted(required-set(value))}, unknown={sorted(unknown)}")
        event = cls(int(value["sequence"]), str(value["event_id"]), str(value["event_type"]), dict(value["payload"]),
                    str(value["previous_hash"]), str(value["timestamp"]), str(value["event_hash"]))
        if digest_json(event.unsigned()) != event.event_hash:
            raise RuntimeStoreError(f"runtime event {event.event_id} hash mismatch")
        return event


def _atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(value) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class RuntimeStore:
    """A single-run store backed by an append-only JSONL log and snapshot."""

    def __init__(self, path: str | Path, run_spec: Any | None = None) -> None:
        target = Path(path)
        self.root = target if target.suffix == "" else target.parent
        self.root.mkdir(parents=True, exist_ok=True)
        if target.suffix.lower() in {".jsonl", ".log"}:
            self.events_path = target
            self.snapshot_path = target.with_suffix(".snapshot.json")
        else:
            self.events_path = self.root / (target.name + ".events.jsonl" if target.suffix else "events.jsonl")
            self.snapshot_path = self.root / (target.name + ".snapshot.json" if target.suffix else "snapshot.json")
        self.lock_path = self.root / ".runtime.lock"
        self._mutex = threading.RLock()
        self._events: list[RuntimeEvent] = []
        self._state: dict[str, Any] = {"runs": {}, "candidates": {}, "executions": {}, "costs": {}, "commits": [], "late_results": []}
        self._load(run_spec)

    @classmethod
    def load(cls, path: str | Path) -> "RuntimeStore":
        return cls(path)

    @property
    def events(self) -> tuple[RuntimeEvent, ...]: return tuple(self._events)
    @property
    def state(self) -> dict[str, Any]: return json.loads(canonical_json(self._state))
    @property
    def head_hash(self) -> str: return self._events[-1].event_hash if self._events else GENESIS_HASH

    def _load(self, run_spec: Any | None) -> None:
        self._reload()
        if run_spec is not None:
            self.create_run(run_spec)

    def _reload(self) -> None:
        self._events = []
        self._state = {"runs": {}, "candidates": {}, "executions": {}, "costs": {}, "commits": [], "late_results": []}
        if self.events_path.exists():
            for line_no, line in enumerate(self.events_path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try: event = RuntimeEvent.from_dict(json.loads(line))
                except (json.JSONDecodeError, RuntimeStoreError, TypeError) as exc:
                    raise RuntimeStoreError(f"invalid or truncated runtime event at line {line_no}") from exc
                self._append_validated(event)
                self._apply(event)
        if self.snapshot_path.exists():
            try: snap = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc: raise RuntimeStoreError("runtime snapshot is unreadable") from exc
            snap_state = snap.get("state", {})
            if snap.get("state_digest_sha256") != digest_json(snap_state):
                raise RuntimeStoreError("runtime snapshot digest mismatch")
            snap_count = snap.get("event_count")
            if not isinstance(snap_count, int) or snap_count < 0:
                raise RuntimeStoreError("runtime snapshot event_count is invalid")
            if snap_count == len(self._events) and snap.get("head_hash") == self.head_hash:
                if snap_state != self._state:
                    raise RuntimeStoreError("runtime snapshot state does not match replay")
            elif 0 <= snap_count < len(self._events):
                # A crash can leave a durable log ahead of its snapshot.  The
                # prefix hash and digest still authenticate that this is a
                # stale snapshot, so replay the complete valid log and repair
                # the projection in place.
                prefix_head = GENESIS_HASH if snap_count == 0 else self._events[snap_count - 1].event_hash
                if snap.get("head_hash") != prefix_head:
                    raise RuntimeStoreError("runtime snapshot does not match event log")
                self.write_snapshot()
            else:
                raise RuntimeStoreError("runtime snapshot does not match event log")

    def _file_lock(self):
        class _Lock:
            def __init__(self, path: Path) -> None:
                self.path = path
                self.handle = None
            def __enter__(self):
                self.handle = self.path.open("a+", encoding="utf-8")
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
                return self
            def __exit__(self, exc_type, exc, tb):
                assert self.handle is not None
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
                self.handle.close()
        return _Lock(self.lock_path)

    def _append_validated(self, event: RuntimeEvent) -> None:
        expected = len(self._events)
        if event.sequence != expected or event.previous_hash != self.head_hash:
            raise RuntimeStoreError("runtime event sequence or previous hash mismatch")
        if any(item.event_id == event.event_id for item in self._events): raise RuntimeStoreError("duplicate runtime event id")
        self._events.append(event)

    def _apply(self, event: RuntimeEvent) -> None:
        data = dict(event.payload)
        if event.event_type == "RUN_CREATED": self._state["runs"][data["runtime_run_id"]] = data
        elif event.event_type == "CANDIDATE_IMPORTED": self._state["candidates"][data["candidate_id"]] = data
        elif event.event_type == "EXECUTION_IMPORTED": self._state["executions"][data["execution_id"]] = data
        elif event.event_type == "COST_IMPORTED": self._state["costs"][data["cost_id"]] = data
        elif event.event_type == "GENERATION_COMMITTED": self._state["commits"].append(data)
        elif event.event_type == "LATE_RESULT": self._state["late_results"].append(data)
        elif event.event_type == "RUN_ACTION":
            run_id = data.get("runtime_run_id")
            if run_id in self._state["runs"]: self._state["runs"][run_id]["status"] = data.get("resulting_state")

    def append_event(self, event_type: str, payload: Mapping[str, Any] | None = None) -> RuntimeEvent:
        with self._mutex, self._file_lock():
            self._reload()
            return self._append_event_unlocked(event_type, payload)

    def _append_event_unlocked(self, event_type: str, payload: Mapping[str, Any] | None = None) -> RuntimeEvent:
        event = RuntimeEvent.create(len(self._events), event_type, payload or {}, self.head_hash)
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(event.to_dict()) + "\n"); handle.flush(); os.fsync(handle.fileno())
        self._events.append(event); self._apply(event); self.write_snapshot()
        return event

    append = append_event

    def append_existing(self, event: RuntimeEvent | Mapping[str, Any]) -> RuntimeEvent:
        with self._mutex, self._file_lock():
            self._reload()
            value = event if isinstance(event, RuntimeEvent) else RuntimeEvent.from_dict(event)
            self._append_validated(value)
            self._apply(value)
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(canonical_json(value.to_dict()) + "\n"); handle.flush(); os.fsync(handle.fileno())
            self.write_snapshot()
            return value

    def write_snapshot(self) -> Path:
        payload = {"schema_version": "1.0", "event_count": len(self._events), "head_hash": self.head_hash,
                   "state": self._state, "state_digest_sha256": digest_json(self._state)}
        _atomic_write(self.snapshot_path, payload); return self.snapshot_path
    snapshot = write_snapshot

    def replay(self) -> dict[str, Any]:
        return self.state

    def validate(self) -> dict[str, Any]:
        # Loading performs all structural checks; expose the same shape as the
        # existing v02 ledgers for callers that use a validation gate.
        return {"valid": True, "event_count": len(self._events), "head_hash": self.head_hash,
                "state_digest_sha256": digest_json(self._state), "errors": []}

    def _validate_run_identity(self, data: Mapping[str, Any]) -> None:
        run_id = data.get("runtime_run_id")
        if not run_id:
            return
        run = self._state["runs"].get(run_id)
        if run is None:
            return
        for field in ("workspace_id", "trace_id"):
            if field in run and field in data and run[field] != data[field]:
                raise RuntimeStoreError(f"{field} does not match runtime run identity")

    @staticmethod
    def _require_identity(data: Mapping[str, Any], *, candidate: bool = False) -> None:
        required = ("workspace_id", "trace_id", "runtime_run_id", "generation_id")
        missing = [field for field in required if not data.get(field)]
        if candidate and not data.get("candidate_id"):
            missing.append("candidate_id")
        if missing:
            raise RuntimeStoreError(f"missing runtime identity fields: {sorted(set(missing))}")

    def create_run(self, run_spec: Any) -> dict[str, Any]:
        data = dict(run_spec.to_dict() if hasattr(run_spec, "to_dict") else run_spec)
        run_id = data.get("runtime_run_id")
        if not run_id: raise RuntimeStoreError("runtime_run_id is required")
        existing = self._state["runs"].get(run_id)
        if existing is not None:
            if existing != data: raise RuntimeStoreError("runtime_run_id already names a different run")
            return existing
        self.append_event("RUN_CREATED", data); return data

    def _idempotent(self, bucket: str, key: str, payload: Mapping[str, Any], event_type: str) -> dict[str, Any]:
        with self._mutex, self._file_lock():
            self._reload()
            existing = self._state[bucket].get(key)
            if existing is not None:
                if existing != dict(payload): raise RuntimeStoreError(f"{key} already imported with different source identity or payload")
                return existing
            self._append_event_unlocked(event_type, payload)
            return dict(payload)

    def import_candidate(self, candidate: Any) -> dict[str, Any]:
        data = envelope_dict(candidate); data["source_identity"] = source_identity(candidate)
        self._require_identity(data, candidate=True)
        self._validate_run_identity(data)
        return self._idempotent("candidates", data["candidate_id"], data, "CANDIDATE_IMPORTED")

    def import_execution_result(self, result: Any) -> dict[str, Any]:
        data = dict(result.to_dict() if hasattr(result, "to_dict") else result)
        key = data.get("execution_id")
        if not key: raise RuntimeStoreError("execution_id is required")
        self._require_identity(data)
        # Full execution envelopes must carry a worker identity.  Keep the
        # historical minimal ledger shape readable for old imports.
        if ("result_digest" in data or "worker_id" in data) and not data.get("worker_id"):
            raise RuntimeStoreError("worker_id is required for execution result")
        if "status" in data and not isinstance(data["status"], str):
            status = getattr(data["status"], "value", None)
            if status is None:
                raise RuntimeStoreError("execution status must be a string")
            data["status"] = status
        if data.get("status") in {"FAILED", "TIMED_OUT", "CANCELLED", "RETRYABLE_FAILURE"} and not (
                data.get("failure_class") or data.get("error")):
            raise RuntimeStoreError("failed execution requires failure_class or error")
        if data.get("worker_id"):
            try:
                from .contracts import WorkerExecutionResult
                WorkerExecutionResult.from_dict({key: value for key, value in data.items()
                                                 if key != "source_identity"})
            except Exception as exc:
                raise RuntimeStoreError("invalid execution result identity or summary") from exc
        data["source_identity"] = source_identity(data)
        self._validate_run_identity(data)
        return self._idempotent("executions", key, data, "EXECUTION_IMPORTED")

    def import_cost(self, cost_id: str | Mapping[str, Any], amount: Any = None,
                    source: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if isinstance(cost_id, Mapping):
            raw = dict(cost_id)
            source = dict(raw.get("source_identity") or source or raw)
            amount = raw.get("amount", raw.get("cost_usd", amount))
            cost_id = str(raw.get("cost_id", raw.get("id", "")))
        if not cost_id or source is None:
            raise RuntimeStoreError("cost_id and source identity are required")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(float(amount)) or float(amount) < 0:
            raise RuntimeStoreError("cost amount must be a finite non-negative number")
        self._require_identity(source)
        payload = {"cost_id": str(cost_id), "amount": amount, "source_identity": dict(source)}
        return self._idempotent("costs", cost_id, payload, "COST_IMPORTED")

    import_fee = import_cost

    def record_generation_commit(self, commit: Any) -> dict[str, Any]:
        data = dict(commit.to_dict() if hasattr(commit, "to_dict") else commit)
        if not data.get("runtime_run_id") or not data.get("generation_id"):
            raise RuntimeStoreError("runtime_run_id and generation_id are required")
        self._validate_run_identity(data)
        # A typed GenerationCommit validates every result identity and its
        # digest.  Mapping payloads with a results array receive equivalent
        # validation while preserving the small legacy commit envelope.
        if "results" in data:
            try:
                from .generation import GenerationCommit
                extensions = {key: data[key] for key in ("parent_generation_id", "parent_commit_digest", "complete") if key in data}
                typed_payload = {key: value for key, value in data.items() if key not in extensions}
                supplied_commit_digest = typed_payload.get("commit_digest")
                if extensions:
                    # Parent linkage is an extension owned by the store; let
                    # the store bind it into the final digest below.
                    typed_payload.pop("commit_digest", None)
                typed = GenerationCommit.from_dict(typed_payload)
                data = typed.to_dict()
                data.update(extensions)
                if supplied_commit_digest:
                    data["commit_digest"] = supplied_commit_digest
            except Exception as exc:
                raise RuntimeStoreError("invalid generation commit identity or digest") from exc
        # Typed generation commits carry a frozen input snapshot and must
        # include its digest.  Keep the compact legacy ledger envelope
        # readable for existing local records that predate that contract.
        if "results" in data and not data.get("snapshot_digest"):
            raise RuntimeStoreError("snapshot_digest is required")
        data.setdefault("complete", bool(data.get("closed", True)))
        data.setdefault("closed", data["complete"])
        generation = str(data["generation_id"])
        existing_generations = [item for item in self._state["commits"]
                                if item.get("runtime_run_id") == data["runtime_run_id"]]
        existing = next((item for item in existing_generations if item.get("generation_id") == generation), None)
        if existing is not None:
            if existing != data: raise RuntimeStoreError("generation commit conflict")
            return existing
        number = _generation_number(generation)
        if number is not None and existing_generations:
            previous_numbers = [_generation_number(str(item.get("generation_id", "")))
                                for item in existing_generations]
            previous_numbers = [value for value in previous_numbers if value is not None]
            if previous_numbers and number != max(previous_numbers) + 1:
                raise RuntimeStoreError("generation ids must be monotonic and contiguous")
            previous = max(existing_generations, key=lambda item: _generation_number(str(item.get("generation_id", "-1"))) or -1)
            parent_generation = data.get("parent_generation_id")
            parent_digest = data.get("parent_commit_digest")
            if parent_generation is not None and parent_generation != previous.get("generation_id"):
                raise RuntimeStoreError("parent_generation_id does not match previous generation")
            if parent_digest is not None and parent_digest != previous.get("commit_digest"):
                raise RuntimeStoreError("parent_commit_digest does not match previous commit")
        existing = next((item for item in self._state["commits"] if item.get("generation_id") == data["generation_id"]), None)
        if existing is not None:
            if existing != data: raise RuntimeStoreError("generation commit conflict")
            return existing
        supplied_digest = data.get("commit_digest")
        if "results" in data:
            # ``complete`` is a store projection flag, not part of the typed
            # GenerationCommit digest contract.
            expected_digest = digest_json({key: value for key, value in data.items()
                                           if key not in {"commit_digest", "complete"}})
            if supplied_digest and supplied_digest != expected_digest:
                raise RuntimeStoreError("generation commit digest mismatch")
            data["commit_digest"] = expected_digest
        else:
            data.setdefault("commit_digest", digest_json(data))
        self.append_event("GENERATION_COMMITTED", data); return data

    def record_late_result(self, result: Any) -> dict[str, Any]:
        data = dict(result.to_dict() if hasattr(result, "to_dict") else result)
        self._require_identity(data)
        execution_id = data.get("execution_id")
        if not execution_id:
            raise RuntimeStoreError("execution_id is required for late result")
        data["disposition"] = "LATE_RESULT_QUARANTINED"
        with self._mutex, self._file_lock():
            self._reload()
            for existing in self._state["late_results"]:
                if existing.get("execution_id") == execution_id:
                    if existing != data:
                        raise RuntimeStoreError(f"{execution_id} already quarantined with different payload")
                    return existing
            self._append_event_unlocked("LATE_RESULT", data)
            return data

    import_result = import_execution_result
    record_execution = import_execution_result


__all__ = ["GENESIS_HASH", "RuntimeEvent", "RuntimeStore", "RuntimeStoreError"]
