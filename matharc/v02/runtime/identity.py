"""Content-neutral identities for the native research runtime.

The runtime identity is deliberately separate from ``ResearchTrace.run_id``.
Objects carry the complete prefix of the hierarchy they belong to; this makes
cross-workspace and cross-generation references fail closed at construction
time.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Mapping


class IdentityError(ValueError):
    """Raised for missing, malformed, or mismatched runtime identities."""


_IDENTITY_FIELDS = (
    "workspace_id", "trace_id", "runtime_run_id", "generation_id",
    "worker_id", "execution_id", "candidate_id", "evidence_id",
)


def _require(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IdentityError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True, slots=True)
class RuntimeIdentity:
    workspace_id: str
    trace_id: str
    runtime_run_id: str
    generation_id: str | None = None
    worker_id: str | None = None
    execution_id: str | None = None
    candidate_id: str | None = None
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        values = {name: getattr(self, name) for name in _IDENTITY_FIELDS}
        for name, value in values.items():
            if value is not None:
                _require(value, name)
        seen_none = False
        for name in _IDENTITY_FIELDS:
            value = values[name]
            if value is None:
                seen_none = True
            elif seen_none:
                raise IdentityError(f"{name} cannot be present without its parent identity")

    @property
    def level(self) -> str:
        for name in reversed(_IDENTITY_FIELDS):
            if getattr(self, name) is not None:
                return name
        raise IdentityError("workspace_id is required")

    def to_dict(self) -> dict[str, str | None]:
        return {name: getattr(self, name) for name in _IDENTITY_FIELDS}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RuntimeIdentity":
        if not isinstance(payload, Mapping):
            raise IdentityError("identity payload must be an object")
        unknown = set(payload) - set(_IDENTITY_FIELDS)
        if unknown:
            raise IdentityError(f"unknown identity fields: {sorted(unknown)}")
        return cls(**{name: payload.get(name) for name in _IDENTITY_FIELDS})

    def child(self, level: str, value: str) -> "RuntimeIdentity":
        if level not in _IDENTITY_FIELDS or level == "workspace_id":
            raise IdentityError(f"unsupported child identity level: {level}")
        index = _IDENTITY_FIELDS.index(level)
        if any(getattr(self, name) is not None for name in _IDENTITY_FIELDS[index:]):
            raise IdentityError("identity already has a child at or below requested level")
        values = self.to_dict()
        values[level] = _require(value, level)
        return RuntimeIdentity(**values)

    def require_ancestor_of(self, other: "RuntimeIdentity") -> None:
        if not isinstance(other, RuntimeIdentity):
            raise IdentityError("expected RuntimeIdentity")
        for name in _IDENTITY_FIELDS:
            mine = getattr(self, name)
            if mine is not None and mine != getattr(other, name):
                raise IdentityError(f"identity mismatch at {name}")

    def same_generation(self, other: "RuntimeIdentity") -> bool:
        return (self.workspace_id, self.trace_id, self.runtime_run_id, self.generation_id) == (
            other.workspace_id, other.trace_id, other.runtime_run_id, other.generation_id
        )


def validate_identity(parent: RuntimeIdentity, child: RuntimeIdentity) -> None:
    """Validate that *child* belongs to *parent* (a fail-closed check)."""
    parent.require_ancestor_of(child)


def idempotency_key(runtime_run_id: str, generation_id: str) -> str:
    return f"{_require(runtime_run_id, 'runtime_run_id')}+{_require(generation_id, 'generation_id')}"


__all__ = ["IdentityError", "RuntimeIdentity", "validate_identity", "idempotency_key"]
