"""Small fail-closed primitives for local console records.

These records are intentionally separate from a research workspace.  They
support console projections but never participate in research replay.
"""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping

from .schema import canonical_json, digest_json


class LocalStoreError(ValueError):
    """Raised for malformed, tampered, or incorrectly located local state."""


def external_root(root: str | Path) -> Path:
    """Resolve a local-store root and reject a research workspace or descendant."""

    resolved = Path(root).resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "workspace.json").is_file():
            raise LocalStoreError("local console state must be outside a research workspace")
    return resolved


def require_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
        raise LocalStoreError(f"{label} must be a lowercase SHA-256 digest")
    return value


def strict_mapping(value: object, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LocalStoreError(f"{label} must be an object")
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown or missing:
        raise LocalStoreError(
            f"{label} fields mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    return value


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalStoreError(f"{label} is unreadable") from exc


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(canonical_json(value) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@contextmanager
def exclusive_lock(root: Path, name: str) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / f".{name}.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def state_digest(payload: Mapping[str, Any], digest_field: str = "state_digest_sha256") -> str:
    unsigned = dict(payload)
    unsigned.pop(digest_field, None)
    return digest_json(unsigned)
