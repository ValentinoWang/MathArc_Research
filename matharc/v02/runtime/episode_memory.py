"""Runtime-facing bridge for the audited v0.2 episode memory.

The canonical implementation remains :mod:`matharc.v02.episode_memory` so
existing research-director callers keep their public API.  Runtime callers
import this module to make the boundary explicit without creating a second
memory store or weakening provenance checks.
"""
from __future__ import annotations

from ..episode_memory import EpisodeMatch, EpisodeMemory, ResearchEpisode, digest_text
from ..failure_memory import FailureLesson, FailureMatch, FailureMemory
from ..schema import FailureClass


class RuntimeEpisodeMemory(EpisodeMemory):
    """Episode memory facade whose failure distillation is provenance-strict."""

    def distill_failure(self, candidate: object, *, failure_class: object,
                        trigger: str, diagnosis: str, repair: str,
                        reusable_lesson: str = "Reproduce with an independent check.",
                        failure_memory: FailureMemory | None = None) -> FailureLesson:
        provenance = dict(getattr(candidate, "provenance", {}) or {})
        run_id = str(provenance.get("runtime_run_id", ""))
        generation_id = str(provenance.get("generation_id", ""))
        candidate_id = str(getattr(candidate, "candidate_id", provenance.get("candidate_id", "")))
        candidate_origin = str(provenance.get("source", "runtime-execution"))
        if not all((run_id.strip(), generation_id.strip(), candidate_id.strip(), candidate_origin.strip())):
            raise ValueError("runtime failure requires run, generation, candidate and origin provenance")
        try:
            failure_enum = failure_class if isinstance(failure_class, FailureClass) else FailureClass(str(failure_class))
        except ValueError as exc:
            raise ValueError(f"unknown failure class: {failure_class}") from exc
        lesson = FailureLesson(
            lesson_id=f"{run_id}:{generation_id}:{candidate_id}", source_run_id=run_id,
            failure_id=candidate_id, failure_class=failure_enum,
            claim_statement=str(getattr(candidate, "payload", "candidate")),
            mechanism_signature=("runtime-execution",), trigger=str(trigger),
            diagnosis=str(diagnosis), minimal_witness=str(getattr(candidate, "payload", ""))[:500],
            repair=str(repair), reusable_lesson=str(reusable_lesson), exact=False,
            generation_id=generation_id, candidate_id=candidate_id, candidate_origin=candidate_origin,
        )
        target = failure_memory or getattr(self, "failure_memory", None)
        if target is not None:
            target.add(lesson)
        return lesson


def ingest_candidate(memory: EpisodeMemory, candidate: object, **kwargs: object) -> ResearchEpisode:
    """Distill a runtime candidate through the canonical provenance API."""
    return memory.ingest_candidate(candidate, **kwargs)


def distill_failure(memory: EpisodeMemory, candidate: object, **kwargs: object) -> FailureLesson:
    """Distill a runtime candidate into the existing FailureMemory contract."""
    if isinstance(memory, RuntimeEpisodeMemory):
        return memory.distill_failure(candidate, **kwargs)
    # Keep the bridge useful with a canonical EpisodeMemory while enforcing
    # the runtime provenance contract in this boundary.
    facade = RuntimeEpisodeMemory(memory.episodes)
    return facade.distill_failure(candidate, **kwargs)


__all__ = [
    "EpisodeMatch",
    "EpisodeMemory",
    "FailureLesson",
    "FailureMatch",
    "FailureMemory",
    "ResearchEpisode",
    "RuntimeEpisodeMemory",
    "digest_text",
    "distill_failure",
    "ingest_candidate",
]
