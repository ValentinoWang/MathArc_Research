"""Candidate records and source-bound identity helpers for the runtime ledger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..schema import digest_json

try:  # RUN1 is deliberately optional while the runtime is assembled in waves.
    from .contracts import CandidateEnvelope  # type: ignore
except Exception:  # pragma: no cover
    @dataclass(frozen=True, slots=True)
    class CandidateEnvelope:
        candidate_id: str
        workspace_id: str
        trace_id: str
        runtime_run_id: str
        generation_id: str
        task_digest: str = ""
        source_digest: str = ""
        evaluator_digest: str = ""
        tool_registry_digest: str = ""
        budget_digest: str = ""
        artifact_digest: str = ""
        payload_digest: str = ""

        def to_dict(self) -> dict[str, Any]:
            return self.__dict__.copy()


class CandidateImportError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    """A persisted candidate and the source identity that produced it."""

    candidate_id: str
    source_identity: Mapping[str, Any]
    envelope: Mapping[str, Any]
    imported_at: str | None = None

    @property
    def source_digest(self) -> str:
        return digest_json(dict(self.source_identity))

    def to_dict(self) -> dict[str, Any]:
        value = {
            "candidate_id": self.candidate_id,
            "source_identity": dict(self.source_identity),
            "envelope": dict(self.envelope),
        }
        if self.imported_at is not None:
            value["imported_at"] = self.imported_at
        return value


def envelope_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = dict(value)
    elif hasattr(value, "to_dict"):
        result = dict(value.to_dict())
    else:
        raise CandidateImportError("candidate envelope must be a mapping or expose to_dict()")
    if not result.get("candidate_id"):
        raise CandidateImportError("candidate_id is required")
    return result


def source_identity(value: Any) -> dict[str, Any]:
    """Extract only provenance fields; changing any of them is a conflict."""
    if isinstance(value, Mapping):
        payload = dict(value)
    elif hasattr(value, "to_dict"):
        payload = dict(value.to_dict())
    else:
        raise CandidateImportError("source value must be a mapping or expose to_dict()")
    fields = (
        "workspace_id", "trace_id", "runtime_run_id", "generation_id",
        "worker_id", "execution_id", "task_digest", "source_digest",
        "evaluator_digest", "tool_registry_digest", "budget_digest", "artifact_digest",
    )
    return {key: payload[key] for key in fields if key in payload}


__all__ = ["CandidateEnvelope", "CandidateImportError", "CandidateRecord", "envelope_dict", "source_identity"]
