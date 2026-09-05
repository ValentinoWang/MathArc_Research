from __future__ import annotations

import json
import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

_TOKEN = re.compile(r"[A-Za-z0-9_]+|[\u3400-\u9fff]+")


def digest_text(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _tokens(value: str) -> set[str]:
    result: set[str] = set()
    for match in _TOKEN.findall(value.lower()):
        result.add(match)
        if len(match) > 4 and any("\u3400" <= char <= "\u9fff" for char in match):
            result.update(match[index : index + 2] for index in range(len(match) - 1))
    return result


@dataclass(slots=True, frozen=True)
class ResearchEpisode:
    episode_id: str
    domain: str
    target: str
    public_move: str
    observable_failure: str
    failure_class: str
    minimal_check: str
    repair: str
    outcome: str
    reusable_policy: str
    status: str
    # Runtime provenance is mandatory for distilled episodes, while remaining
    # optional for the frozen v0.2 seed corpus.
    run_id: str = ""
    generation_id: str = ""
    candidate_id: str = ""
    candidate_origin: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "domain": self.domain,
            "target": self.target,
            "public_move": self.public_move,
            "observable_failure": self.observable_failure,
            "failure_class": self.failure_class,
            "minimal_check": self.minimal_check,
            "repair": self.repair,
            "outcome": self.outcome,
            "reusable_policy": self.reusable_policy,
            "status": self.status,
            "run_id": self.run_id,
            "generation_id": self.generation_id,
            "candidate_id": self.candidate_id,
            "candidate_origin": self.candidate_origin,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResearchEpisode":
        allowed = {
            "episode_id",
            "domain",
            "target",
            "public_move",
            "observable_failure",
            "failure_class",
            "minimal_check",
            "repair",
            "outcome",
            "reusable_policy",
            "status",
            "run_id",
            "generation_id",
            "candidate_id",
            "candidate_origin",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown research-episode fields: {sorted(unknown)}")
        required = allowed - {"run_id", "generation_id", "candidate_id", "candidate_origin"}
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            raise ValueError(f"research episode misses fields: {sorted(missing)}")
        return cls(**{field: str(payload.get(field, "")) for field in allowed})

    @property
    def has_runtime_provenance(self) -> bool:
        return all((self.run_id, self.generation_id, self.candidate_id, self.candidate_origin))

    @property
    def search_text(self) -> str:
        return " ".join(
            (
                self.domain,
                self.target,
                self.public_move,
                self.observable_failure,
                self.failure_class,
                self.minimal_check,
                self.repair,
                self.outcome,
                self.reusable_policy,
            )
        )


@dataclass(slots=True, frozen=True)
class EpisodeMatch:
    episode: ResearchEpisode
    score: float
    matched_terms: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode": self.episode.to_dict(),
            "score": self.score,
            "matched_terms": list(self.matched_terms),
            "rationale": self.rationale,
        }


class EpisodeMemory:
    """Transparent lexical retrieval over audited public research episodes.

    Retrieval is intentionally inspectable: no embedding model or hidden score
    determines which historical lesson enters a proof plan.  A future semantic
    backend may be added, but it must preserve the lexical explanation and the
    exact episode IDs used by the planner.
    """

    def __init__(self, episodes: Iterable[ResearchEpisode] = ()) -> None:
        self._episodes: dict[str, ResearchEpisode] = {}
        self._reuse: dict[str, int] = {}
        for episode in episodes:
            self.add(episode)

    @property
    def episodes(self) -> tuple[ResearchEpisode, ...]:
        return tuple(self._episodes[key] for key in sorted(self._episodes))

    def add(self, episode: ResearchEpisode) -> None:
        if episode.episode_id in self._episodes:
            raise ValueError(f"duplicate research episode: {episode.episode_id}")
        self._episodes[episode.episode_id] = episode
        self._reuse.setdefault(episode.episode_id, 0)

    def distill_episode(self, *, run_id: str, generation_id: str, candidate_id: str,
                        candidate_origin: str, domain: str, target: str,
                        public_move: str, observable_failure: str,
                        failure_class: str, minimal_check: str, repair: str,
                        outcome: str, reusable_policy: str,
                        status: str = "RUNTIME_DISTILLED") -> ResearchEpisode:
        """Create an auditable episode from one runtime execution."""
        values = (run_id, generation_id, candidate_id, candidate_origin)
        if any(not str(value).strip() for value in values):
            raise ValueError("runtime episode requires run_id, generation_id, candidate_id and candidate_origin")
        episode_id = "EP-RUNTIME-" + digest_text({"run_id": run_id, "generation_id": generation_id,
                                                    "candidate_id": candidate_id, "origin": candidate_origin})
        episode = ResearchEpisode(episode_id, domain, target, public_move, observable_failure,
            failure_class, minimal_check, repair, outcome, reusable_policy, status,
            str(run_id), str(generation_id), str(candidate_id), str(candidate_origin))
        existing = self._episodes.get(episode_id)
        if existing is not None:
            if existing != episode:
                raise ValueError(f"conflicting runtime episode: {episode_id}")
            return existing
        self.add(episode)
        return episode

    def ingest_candidate(self, candidate: Any, *, domain: str = "runtime",
                         outcome: str = "observed", failure_class: str = "UNKNOWN",
                         repair: str = "review independently") -> ResearchEpisode:
        provenance = dict(getattr(candidate, "provenance", {}) or {})
        payload = getattr(candidate, "payload", candidate)
        return self.distill_episode(
            run_id=str(provenance.get("runtime_run_id", "")),
            generation_id=str(provenance.get("generation_id", "")),
            candidate_id=str(getattr(candidate, "candidate_id", provenance.get("candidate_id", ""))),
            candidate_origin=str(provenance.get("source", "runtime-execution")),
            domain=domain, target=str(provenance.get("task_digest", "candidate")),
            public_move="runtime execution produced a candidate",
            observable_failure=str(payload)[:500], failure_class=failure_class,
            minimal_check="independent replay", repair=repair, outcome=outcome,
            reusable_policy="Use as planning context only; never as proof evidence.",
        )

    def distill_failure(self, candidate: Any, *, failure_class: Any,
                        trigger: str, diagnosis: str, repair: str,
                        reusable_lesson: str = "Reproduce with an independent check.",
                        failure_memory: Any | None = None) -> Any:
        """Distill a runtime candidate into the existing FailureMemory contract."""
        from .failure_memory import FailureLesson
        from .schema import FailureClass
        provenance = dict(getattr(candidate, "provenance", {}) or {})
        run_id = str(provenance.get("runtime_run_id", ""))
        generation_id = str(provenance.get("generation_id", ""))
        candidate_id = str(getattr(candidate, "candidate_id", provenance.get("candidate_id", "")))
        candidate_origin = str(provenance.get("candidate_origin", provenance.get("source", "")))
        if not all((run_id.strip(), generation_id.strip(), candidate_id.strip(), candidate_origin.strip())):
            raise ValueError("runtime failure requires run, generation, candidate and origin provenance")
        if not isinstance(failure_class, FailureClass):
            failure_class = FailureClass(str(failure_class))
        lesson = FailureLesson(
            lesson_id=f"{run_id}:{generation_id}:{candidate_id}", source_run_id=run_id,
            failure_id=candidate_id, failure_class=failure_class,
            claim_statement=str(getattr(candidate, "payload", "candidate")),
            mechanism_signature=("runtime-execution",), trigger=trigger,
            diagnosis=diagnosis, minimal_witness=str(getattr(candidate, "payload", ""))[:500],
            repair=repair, reusable_lesson=reusable_lesson, exact=False,
            generation_id=generation_id, candidate_id=candidate_id, candidate_origin=candidate_origin,
        )
        if failure_memory is not None:
            failure_memory.add(lesson)
        return lesson

    def query(
        self,
        statement: str,
        *,
        domain: str = "",
        failure_classes: Iterable[str] = (),
        top_k: int = 5,
        minimum_score: float = 0.04,
    ) -> list[EpisodeMatch]:
        query_terms = _tokens(" ".join((statement, domain, *failure_classes)))
        if not query_terms:
            return []
        requested_classes = {str(value) for value in failure_classes}
        requested_domain = domain.strip().lower()
        matches: list[EpisodeMatch] = []
        for episode in self._episodes.values():
            episode_terms = _tokens(episode.search_text)
            overlap = query_terms & episode_terms
            union = query_terms | episode_terms
            lexical = len(overlap) / len(union) if union else 0.0
            containment = len(overlap) / len(query_terms) if query_terms else 0.0
            domain_bonus = (
                0.20
                if requested_domain
                and requested_domain in episode.domain.lower()
                else 0.0
            )
            class_bonus = (
                0.22
                if requested_classes and episode.failure_class in requested_classes
                else 0.0
            )
            success_bonus = 0.04 if episode.status == "AUDITED_SUCCESS" else 0.0
            reuse_bonus = min(0.08, 0.02 * math.log1p(self._reuse[episode.episode_id]))
            score = 0.55 * lexical + 0.35 * containment + domain_bonus + class_bonus + success_bonus + reuse_bonus
            if score < minimum_score:
                continue
            rationale_parts = [
                f"lexical={lexical:.3f}",
                f"query_containment={containment:.3f}",
            ]
            if domain_bonus:
                rationale_parts.append("domain match")
            if class_bonus:
                rationale_parts.append("failure-class match")
            if success_bonus:
                rationale_parts.append("audited-success prior")
            if reuse_bonus:
                rationale_parts.append(f"reused={self._reuse[episode.episode_id]}")
            matches.append(
                EpisodeMatch(
                    episode=episode,
                    score=score,
                    matched_terms=tuple(sorted(overlap)),
                    rationale="; ".join(rationale_parts),
                )
            )
        matches.sort(key=lambda item: (-item.score, item.episode.episode_id))
        return matches[:top_k]

    def mark_reused(self, episode_id: str) -> None:
        if episode_id not in self._episodes:
            raise KeyError(episode_id)
        self._reuse[episode_id] += 1

    def planner_context(
        self,
        statement: str,
        *,
        domain: str = "",
        top_k: int = 5,
    ) -> dict[str, Any]:
        matches = self.query(statement, domain=domain, top_k=top_k)
        return {
            "query": statement,
            "domain": domain,
            "episodes": [
                {
                    "episode_id": match.episode.episode_id,
                    "failure_class": match.episode.failure_class,
                    "minimal_check": match.episode.minimal_check,
                    "repair": match.episode.repair,
                    "reusable_policy": match.episode.reusable_policy,
                    "score": match.score,
                    "rationale": match.rationale,
                }
                for match in matches
            ],
            "instruction": (
                "Use retrieved episodes as attack and planning precedents. "
                "They are not premises proving the current claim."
            ),
        }

    def metrics(self) -> dict[str, Any]:
        reused = sum(value > 0 for value in self._reuse.values())
        total_reuse = sum(self._reuse.values())
        classes = {episode.failure_class for episode in self._episodes.values()}
        domains = {episode.domain for episode in self._episodes.values()}
        return {
            "episode_count": len(self._episodes),
            "domain_count": len(domains),
            "failure_class_count": len(classes),
            "episodes_reused": reused,
            "total_reuse_events": total_reuse,
            "episode_reuse_rate": reused / len(self._episodes) if self._episodes else 0.0,
        }

    @classmethod
    def load_jsonl(cls, path: str | Path) -> "EpisodeMemory":
        memory = cls()
        for line_number, line in enumerate(
            Path(path).read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid episode JSON at line {line_number}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"episode line {line_number} is not an object")
            memory.add(ResearchEpisode.from_dict(payload))
        return memory

    def save_jsonl(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "".join(
                json.dumps(episode.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
                for episode in self.episodes
            ),
            encoding="utf-8",
        )
        return target
