"""Fail-closed view models for the research console runtime.

This layer deliberately projects existing read-only workspace exports.  It
does not invent business state and it never exposes process credentials,
commands, environments, or tracebacks to a browser client.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..console_export import ConsoleLocalProjectionConfig, build_console_export

SENSITIVE_KEYS = frozenset({
    "command", "commands", "cmd", "argv", "args", "environment", "env",
    "stack", "stacktrace", "traceback", "exception", "stderr", "stdout",
    "cwd", "working_directory", "path", "root", "workspace_root", "source_path",
    "source_identity", "secret", "secret_key", "api_key", "access_key",
    "private_key", "authorization", "bearer", "full_command", "executable_path",
    "token", "password", "cookie",
})


def redact_payload(value: Any, *, sensitive_keys: set[str] | frozenset[str] = SENSITIVE_KEYS) -> Any:
    """Recursively redact operational data while preserving JSON shape.

    Keys are compared case-insensitively and punctuation-insensitively.  This
    catches nested records and list entries without relying on a fixed schema.
    """
    def norm(key: object) -> str:
        # Treat punctuation (including underscore) as presentation only so
        # api-key, api.key and api_key cannot bypass the disclosure boundary.
        return "".join(ch for ch in str(key).casefold() if ch.isalnum())

    keyset = {norm(key) for key in sensitive_keys}
    def walk(item: Any, key: str | None = None) -> Any:
        if key is not None and norm(key) in keyset:
            return "[REDACTED]"
        if isinstance(item, Mapping):
            return {str(k): walk(v, str(k)) for k, v in item.items()}
        if isinstance(item, list):
            return [walk(v) for v in item]
        if isinstance(item, tuple):
            return [walk(v) for v in item]
        if isinstance(item, str):
            # Error text and free-form diagnostics can contain paths even when
            # their field name is innocuous.
            return re.sub(r"(?<![A-Za-z0-9])/(?:Users|private|tmp|var|home|opt|workspace)/[^\s\"']+", "[REDACTED_PATH]", item)
        return item
    return walk(value)


def _digest(value: object) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ConsoleSnapshot:
    """Immutable, redacted console payload and its stream cursor."""

    run_id: str
    sequence: int
    payload: dict[str, Any]
    payload_digest_sha256: str
    state: str = "ready"
    runtime_run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "sequence": self.sequence,
            "payload_digest_sha256": self.payload_digest_sha256,
            "state": self.state,
            "runtime_run_id": self.runtime_run_id,
            "payload": copy.deepcopy(self.payload),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ConsoleSnapshot":
        if not isinstance(payload, Mapping):
            raise ValueError("console payload must be an object")
        provenance = payload.get("provenance")
        if not isinstance(provenance, Mapping) or not isinstance(provenance.get("run_id"), str) or not provenance["run_id"]:
            raise ValueError("console payload has no valid provenance.run_id")
        workspace = payload.get("workspace")
        events = workspace.get("events") if isinstance(workspace, Mapping) else None
        records = events.get("events") if isinstance(events, Mapping) else None
        if not isinstance(records, list):
            raise ValueError("console payload has no event sequence")
        runtime = payload.get("runtime")
        runtime_run_id = runtime.get("run_id") if isinstance(runtime, Mapping) else None
        runtime_cursor = runtime.get("cursor") if isinstance(runtime, Mapping) else None
        sequence = (
            int(runtime_cursor)
            if isinstance(runtime_cursor, int)
            else max((int(item.get("sequence", -1)) for item in records if isinstance(item, Mapping)), default=-1)
        )
        redacted = redact_payload(dict(payload))
        return cls(
            str(runtime_run_id or provenance["run_id"]),
            sequence,
            redacted,
            _digest(redacted),
            runtime_run_id=str(runtime_run_id) if runtime_run_id else None,
        )


def project_console_snapshot(
    workspace_root: str | Path,
    *,
    local_projection_config: ConsoleLocalProjectionConfig | None = None,
    runtime_store: Any | None = None,
    runtime_run_id: str | None = None,
) -> ConsoleSnapshot:
    """Build and validate a current snapshot from the governed workspace."""
    payload = build_console_export(workspace_root, local_projection_config=local_projection_config)
    if runtime_store is not None:
        state = runtime_store.state if hasattr(runtime_store, "state") else runtime_store
        if not isinstance(state, Mapping):
            raise ValueError("runtime store state must be an object")
        runs = state.get("runs", {})
        if not isinstance(runs, Mapping):
            raise ValueError("runtime store runs must be an object")
        if runtime_run_id is None:
            if len(runs) == 1:
                runtime_run_id = str(next(iter(runs)))
            elif len(runs) > 1:
                # Keep the legacy endpoint deterministic while never exposing
                # sibling run records in one snapshot.
                runtime_run_id = str(sorted(runs)[0])
        if runtime_run_id is not None and runtime_run_id not in runs:
            raise ValueError("runtime_run_id is not present in runtime store")

        def keep(value: Any) -> Any:
            if isinstance(value, Mapping):
                if "runtime_run_id" in value and value.get("runtime_run_id") != runtime_run_id:
                    return None
                result = {}
                for key, child in value.items():
                    kept = keep(child)
                    if kept is not None:
                        result[key] = kept
                return result
            if isinstance(value, list):
                return [kept for item in value if (kept := keep(item)) is not None]
            return value

        projected_state = keep(dict(state))
        # Cursor zero is the stable empty-stream baseline used by the console
        # contract; subsequent runtime events use their durable sequence.
        target_events = [
            event for event in getattr(runtime_store, "events", ())
            if runtime_run_id is None or getattr(event, "payload", {}).get("runtime_run_id") == runtime_run_id
        ]
        event_cursor = max(0, len(target_events) - 1)
        payload = dict(payload)
        payload["runtime"] = {
            "run_id": runtime_run_id,
            "cursor": event_cursor,
            "state": projected_state,
            "head_hash": getattr(runtime_store, "head_hash", None),
        }
        snapshot = ConsoleSnapshot.from_payload(payload)
        return ConsoleSnapshot(
            str(runtime_run_id or snapshot.run_id),
            event_cursor,
            snapshot.payload,
            snapshot.payload_digest_sha256,
            snapshot.state,
            str(runtime_run_id) if runtime_run_id else None,
        )
    return ConsoleSnapshot.from_payload(payload)


__all__ = ["ConsoleSnapshot", "project_console_snapshot", "redact_payload", "SENSITIVE_KEYS"]
