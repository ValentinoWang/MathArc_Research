"""Runtime-facing bridge for the audited v0.2 episode memory.

The canonical implementation remains :mod:`matharc.v02.episode_memory` so
existing research-director callers keep their public API.  Runtime callers
import this module to make the boundary explicit without creating a second
memory store or weakening provenance checks.
"""
from __future__ import annotations

from ..episode_memory import EpisodeMatch, EpisodeMemory, ResearchEpisode, digest_text
from ..failure_memory import FailureLesson, FailureMatch, FailureMemory


# Descriptive alias for code that wants to state which memory it is using.
RuntimeEpisodeMemory = EpisodeMemory


def ingest_candidate(memory: EpisodeMemory, candidate: object, **kwargs: object) -> ResearchEpisode:
    """Distill a runtime candidate through the canonical provenance API."""
    return memory.ingest_candidate(candidate, **kwargs)


def distill_failure(memory: EpisodeMemory, candidate: object, **kwargs: object) -> FailureLesson:
    """Distill a runtime candidate into the existing FailureMemory contract."""
    return memory.distill_failure(candidate, **kwargs)


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
