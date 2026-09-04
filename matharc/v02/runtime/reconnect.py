"""Cursor-based reconnect handling for console event streams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class ReconnectResult:
    run_id: str
    after: int
    events: tuple[dict[str, Any], ...]
    reload_required: bool = False
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "after": self.after, "events": list(self.events), "reload_required": self.reload_required, "reason": self.reason}


class ReconnectManager:
    """Validate event continuity and return only events after a cursor."""

    def __init__(self, run_id: str, sequence: int = -1) -> None:
        if not run_id:
            raise ValueError("run_id is required")
        self.run_id = run_id
        self.sequence = int(sequence)

    def reconnect(self, *, run_id: str, after: int, events: Iterable[Mapping[str, Any]]) -> ReconnectResult:
        if run_id != self.run_id:
            return ReconnectResult(self.run_id, self.sequence, (), True, "run_id_changed")
        if int(after) < -1 or int(after) > self.sequence:
            return ReconnectResult(self.run_id, self.sequence, (), True, "cursor_out_of_range")
        selected: list[dict[str, Any]] = []
        expected = int(after) + 1
        for raw in events:
            if not isinstance(raw, Mapping):
                return ReconnectResult(self.run_id, self.sequence, (), True, "invalid_event")
            event_run = raw.get("run_id", self.run_id)
            seq = raw.get("sequence")
            if event_run != self.run_id or not isinstance(seq, int):
                return ReconnectResult(self.run_id, self.sequence, (), True, "event_identity_mismatch")
            if seq <= int(after):
                continue
            if seq != expected:
                return ReconnectResult(self.run_id, self.sequence, (), True, "sequence_gap")
            selected.append(dict(raw)); expected += 1
        if selected:
            self.sequence = selected[-1]["sequence"]
        return ReconnectResult(self.run_id, self.sequence, tuple(selected))


__all__ = ["ReconnectManager", "ReconnectResult"]
