from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .episode_memory import EpisodeMatch, EpisodeMemory
from .failure_channels import open_review_gaps
from .failure_memory import FailureMemory
from .orchestrator import ResearchOrchestrator, ResearchRoundPlan
from .trace import ResearchTrace


@dataclass(slots=True)
class AdaptiveRoundPlan:
    base_plan: ResearchRoundPlan
    episode_matches: tuple[EpisodeMatch, ...]
    mandatory_attack_tests: tuple[str, ...]
    historical_repairs: tuple[str, ...]
    route_constraints: tuple[str, ...]
    stop_conditions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_plan": self.base_plan.to_dict(),
            "episode_matches": [item.to_dict() for item in self.episode_matches],
            "mandatory_attack_tests": list(self.mandatory_attack_tests),
            "attack_source": (
                "ResearchRoundPlan.route_actions + retrieved_failures + "
                "v0.3 open ReviewGap records + EpisodeMemory.minimal_check"
            ),
            "historical_repairs": list(self.historical_repairs),
            "route_constraints": list(self.route_constraints),
            "stop_conditions": list(self.stop_conditions),
            "public_summary": (
                f"Focus {self.base_plan.focus_claim_id}; execute "
                f"{len(self.mandatory_attack_tests)} historical/review attacks before expansion."
            ),
            "claim_boundary": (
                "Historical episodes and review gaps modify planning and falsification. "
                "They are not evidence proving the focus claim."
            ),
        }


class AdaptiveResearchDirector:
    """Combine dependency load, failure memory, expert gaps and episodes.

    `ResearchRoundPlan` intentionally stores route actions rather than a second,
    potentially divergent `required_attacks` field. This director is the single
    compiler from route actions, exact failures, review feedback and historical
    episodes to mandatory attack tests.
    """

    def __init__(
        self,
        trace: ResearchTrace,
        *,
        episode_memory: EpisodeMemory,
        failure_memory: FailureMemory | None = None,
        domain: str = "",
    ) -> None:
        self.trace = trace
        self.episode_memory = episode_memory
        self.failure_memory = failure_memory or FailureMemory()
        self.domain = domain
        self.base = ResearchOrchestrator(trace, self.failure_memory)
        self._planned_episode_ids: set[str] = set()

    def plan_round(self, *, top_k_episodes: int = 5) -> AdaptiveRoundPlan:
        base_plan = self.base.plan_round()
        base_attacks = self._base_attack_tests(base_plan)
        claim = self.trace.claims[base_plan.focus_claim_id]
        review_gaps = open_review_gaps(self.trace, claim.claim_id)
        review_attacks = tuple(
            f"Resolve expert review gap {item.event_id}: {item.description}"
            for item in review_gaps
        )
        query = " ".join(
            (
                self.trace.contract.problem,
                self.trace.contract.scope,
                claim.statement,
                claim.scope,
                claim.boundary,
                *base_attacks,
                *review_attacks,
            )
        )
        matches = tuple(
            self.episode_memory.query(
                query,
                domain=self.domain,
                top_k=top_k_episodes,
            )
        )
        self._planned_episode_ids.update(
            match.episode.episode_id for match in matches
        )
        attacks = self._unique(
            (
                *base_attacks,
                *review_attacks,
                *(match.episode.minimal_check for match in matches),
            )
        )
        repairs = self._unique(match.episode.repair for match in matches)
        route_constraints = self._unique(
            (
                "Each route must have a mechanism signature different from every active route.",
                "Run the cheapest discriminator before expanding a route.",
                "Do not cite a historical episode or expert review as proof evidence.",
                *(
                    f"A current expert gap remains load-bearing: {item.event_id}. "
                    "Address it explicitly before claiming closure."
                    for item in review_gaps
                ),
                *(
                    f"Guard against {match.episode.failure_class}: "
                    f"{match.episode.reusable_policy}"
                    for match in matches
                ),
            )
        )
        stop_conditions = self._unique(
            (
                "Stop and record an exact claim counterexample only when a minimal witness passes independent checking.",
                "Stop promotion when statement correspondence changes a quantifier, object class or limit.",
                "Stop route expansion when its declared kill test fails.",
                "Stop the round after one load-bearing claim is proved, refuted or exactly blocked.",
            )
        )
        return AdaptiveRoundPlan(
            base_plan=base_plan,
            episode_matches=matches,
            mandatory_attack_tests=attacks,
            historical_repairs=repairs,
            route_constraints=route_constraints,
            stop_conditions=stop_conditions,
        )

    def mark_plan_used(
        self,
        plan: AdaptiveRoundPlan,
        *,
        used_episode_ids: Iterable[str],
    ) -> None:
        permitted = {
            match.episode.episode_id for match in plan.episode_matches
        }
        for episode_id in used_episode_ids:
            if episode_id not in permitted:
                raise ValueError(
                    f"episode {episode_id} was not retrieved for this round"
                )
            self.episode_memory.mark_reused(episode_id)

    def metrics(self) -> dict[str, Any]:
        values = self.episode_memory.metrics()
        values.update(
            {
                "planned_episode_count": len(self._planned_episode_ids),
                "planned_episode_ids": sorted(self._planned_episode_ids),
            }
        )
        return values

    @classmethod
    def _base_attack_tests(cls, base_plan: ResearchRoundPlan) -> tuple[str, ...]:
        attacks: list[str] = [
            "Check exact quantifiers, object class and theorem scope before promotion.",
            "Attempt the smallest degenerate, boundary and adversarial instances first.",
        ]
        for action in base_plan.route_actions:
            kill_test = str(action.get("kill_test", "")).strip()
            if kill_test:
                attacks.append(kill_test)
            discriminator = str(action.get("expected_discriminator", "")).strip()
            if discriminator:
                attacks.append(f"Confirm the route discriminator: {discriminator}")
        for failure in base_plan.retrieved_failures:
            lesson_id = str(
                failure.get("lesson_id")
                or failure.get("failure_id")
                or "historical failure"
            )
            diagnosis = str(failure.get("diagnosis", "")).strip()
            repair = str(failure.get("repair", "")).strip()
            if diagnosis:
                attacks.append(f"Reproduce {lesson_id}: {diagnosis}")
            if repair:
                attacks.append(f"Verify the repair boundary for {lesson_id}: {repair}")
        return cls._unique(attacks)

    @staticmethod
    def _unique(values: Iterable[str]) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = " ".join(str(value).split())
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return tuple(result)
