"""Compile explicit next-generation work from prior-generation facts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ...schema import digest_json, utc_now


@dataclass(frozen=True, slots=True)
class AgendaItem:
    item_id: str
    action: str
    source_fact_ids: tuple[str, ...]
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "action": self.action,
                "source_fact_ids": list(self.source_fact_ids), "rationale": self.rationale}


@dataclass(frozen=True, slots=True)
class NextGenerationAgenda:
    generation_id: str
    parent_generation_id: str
    items: tuple[AgendaItem, ...]
    consumed_fact_ids: tuple[str, ...]
    created_at: str = field(default_factory=utc_now)

    @property
    def agenda_digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {"generation_id": self.generation_id, "parent_generation_id": self.parent_generation_id,
                "items": [item.to_dict() for item in self.items],
                "consumed_fact_ids": list(self.consumed_fact_ids), "created_at": self.created_at,
                "agenda_digest": self.agenda_digest}


def compile_next_generation_agenda(*, generation_id: str, parent_generation_id: str,
                                   failures: Iterable[Any] = (), episodes: Iterable[Any] = (),
                                   review_gaps: Iterable[Any] = (), route_changes: Iterable[Any] = ()) -> NextGenerationAgenda:
    """Compile failures, lived episodes, review gaps and route changes.

    Every generated item carries at least one immutable fact identifier, making
    it impossible for the next generation to appear ungrounded in prior work.
    """
    if not str(generation_id).strip() or not str(parent_generation_id).strip():
        raise ValueError("generation_id and parent_generation_id are required")
    items: list[AgendaItem] = []
    consumed: list[str] = []

    def add(kind: str, value: Any, default_action: str) -> None:
        if isinstance(value, Mapping):
            fact_id = str(value.get("failure_id") or value.get("episode_id") or value.get("event_id") or value.get("route_id") or value.get("id") or "")
            detail = str(value.get("repair") or value.get("description") or value.get("action") or value.get("rationale") or default_action)
        else:
            fact_id = str(getattr(value, "failure_id", "") or getattr(value, "episode_id", "") or getattr(value, "event_id", "") or getattr(value, "route_id", "") or getattr(value, "id", ""))
            detail = str(getattr(value, "repair", "") or getattr(value, "description", "") or default_action)
        if not fact_id.strip():
            fact_id = f"{kind}-{len(consumed)+1}"
        if fact_id in consumed:
            return
        consumed.append(fact_id)
        items.append(AgendaItem(f"{generation_id}:{kind}:{fact_id}", detail, (fact_id,), f"consumes {kind} from generation {parent_generation_id}"))

    for value in failures: add("failure", value, "reproduce and bound the prior failure")
    for value in episodes: add("episode", value, "apply the episode's minimal check")
    for value in review_gaps: add("review-gap", value, "close the outstanding review gap")
    for value in route_changes: add("route-change", value, "evaluate the changed route discriminator")
    return NextGenerationAgenda(str(generation_id), str(parent_generation_id), tuple(items), tuple(consumed))


compile_agenda = compile_next_generation_agenda


__all__ = ["AgendaItem", "NextGenerationAgenda", "compile_next_generation_agenda", "compile_agenda"]
