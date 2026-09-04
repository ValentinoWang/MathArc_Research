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
        return "".join(ch for ch in str(key).casefold() if ch.isalnum() or ch == "_")

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "sequence": self.sequence,
            "payload_digest_sha256": self.payload_digest_sha256,
            "state": self.state,
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
        sequence = max((int(item.get("sequence", -1)) for item in records if isinstance(item, Mapping)), default=-1)
        redacted = redact_payload(dict(payload))
        return cls(provenance["run_id"], sequence, redacted, _digest(redacted))


def project_console_snapshot(
    workspace_root: str | Path,
    *,
    local_projection_config: ConsoleLocalProjectionConfig | None = None,
    runtime_store: Any | None = None,
) -> ConsoleSnapshot:
    """Build and validate a current snapshot from the governed workspace."""
    payload = build_console_export(workspace_root, local_projection_config=local_projection_config)
    if runtime_store is not None:
        state = runtime_store.state if hasattr(runtime_store, "state") else runtime_store
        if not isinstance(state, Mapping):
            raise ValueError("runtime store state must be an object")
        payload = dict(payload)
        payload["runtime"] = {"state": dict(state), "head_hash": getattr(runtime_store, "head_hash", None)}
    return ConsoleSnapshot.from_payload(payload)


__all__ = ["ConsoleSnapshot", "project_console_snapshot", "redact_payload", "SENSITIVE_KEYS"]
