"""Public adaptive director API with an explicit non-evidence boundary."""

from __future__ import annotations

from .._research_director_impl import AdaptiveRoundPlan
from .._research_director_impl import (
    AdaptiveResearchDirector as _AdaptiveResearchDirectorImpl,
)


class AdaptiveResearchDirector(_AdaptiveResearchDirectorImpl):
    def plan_round(self, *, top_k_episodes: int = 5) -> AdaptiveRoundPlan:
        plan = super().plan_round(top_k_episodes=top_k_episodes)
        explicit = "Historical episodes are not evidence for the current claim."
        if explicit not in plan.route_constraints:
            plan.route_constraints = (*plan.route_constraints, explicit)
        return plan


__all__ = ["AdaptiveResearchDirector", "AdaptiveRoundPlan"]
