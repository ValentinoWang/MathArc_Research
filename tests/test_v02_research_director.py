from __future__ import annotations

import unittest
from pathlib import Path

from matharc.v02.episode_memory import EpisodeMemory
from matharc.v02.research_director import AdaptiveResearchDirector
from matharc.v02.schema import ClaimRecord, ResearchRoute, RouteStatus, TheoremContract
from matharc.v02.trace import ResearchTrace


class AdaptiveResearchDirectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.memory = EpisodeMemory.load_jsonl(
            root / "memory" / "research_episodes_v02.jsonl"
        )

    def test_yang_mills_plan_requires_scope_bridge_attack(self) -> None:
        trace = ResearchTrace(
            "YMS-PLAN",
            TheoremContract(
                "YMS",
                "Construct four-dimensional Yang-Mills theory with a mass gap.",
                ("C-TARGET",),
                "Continuum and infinite volume.",
            ),
        )
        trace.add_claim(
            ClaimRecord(
                "C-BOUNDED",
                "A bounded Wilson-network model has an algebraic reconstruction.",
                "Bounded network.",
                weight=1.0,
            )
        )
        trace.add_claim(
            ClaimRecord(
                "C-TARGET",
                "The continuum infinite-volume theory exists and has a positive mass gap.",
                "Four Euclidean dimensions.",
                dependencies=("C-BOUNDED",),
                critical=True,
                weight=5.0,
                boundary="Requires all continuum, locality and spectral bridges.",
            )
        )
        trace.add_route(
            ResearchRoute(
                "R-UV",
                "quantum-group UV route",
                "UV suppression controls the continuum construction",
                ("quantum-group ultraviolet estimate",),
                "remove the UV structure and identify the first estimate that fails",
                RouteStatus.ACTIVE,
                ("C-TARGET",),
            )
        )
        director = AdaptiveResearchDirector(
            trace,
            episode_memory=EpisodeMemory(self.memory.episodes),
            domain="mathematical_physics",
        )
        plan = director.plan_round()
        self.assertEqual(plan.base_plan.focus_claim_id, "C-BOUNDED")
        self.assertTrue(plan.mandatory_attack_tests)
        ids = {match.episode.episode_id for match in plan.episode_matches}
        self.assertIn("EP-YMS-SCOPE-001", ids)
        self.assertTrue(
            any("side by side" in attack for attack in plan.mandatory_attack_tests)
        )
        self.assertTrue(
            any("not evidence" in item for item in plan.route_constraints)
        )

    def test_round_plan_exposes_active_route_kill_test(self) -> None:
        trace = ResearchTrace(
            "ROUTE-ATTACKS",
            TheoremContract("T", "Target theorem", ("C",), "global scope"),
        )
        trace.add_claim(
            ClaimRecord(
                "C",
                "Prove a universal claim.",
                "global scope",
                route_ids=("R",),
                critical=True,
            )
        )
        trace.add_route(
            ResearchRoute(
                "R",
                "local-to-global route",
                "a local certificate lifts globally",
                ("local certificate", "global lifting"),
                "construct the smallest object where the local certificate exists but the lift fails",
                RouteStatus.ACTIVE,
                ("C",),
                expected_discriminator="exact witness or a proved lifting lemma",
            )
        )
        director = AdaptiveResearchDirector(
            trace,
            episode_memory=EpisodeMemory(()),
        )
        plan = director.plan_round(top_k_episodes=0)
        self.assertIn(
            "construct the smallest object where the local certificate exists but the lift fails",
            plan.mandatory_attack_tests,
        )
        self.assertTrue(
            any(
                action.get("kill_test")
                == "construct the smallest object where the local certificate exists but the lift fails"
                for action in plan.base_plan.route_actions
            )
        )
        self.assertIn("attack_source", plan.to_dict())

    def test_reuse_count_changes_only_when_explicitly_marked(self) -> None:
        trace = ResearchTrace(
            "R",
            TheoremContract("K", "quotient lifting problem", ("C",), "ring theory"),
        )
        trace.add_claim(
            ClaimRecord(
                "C",
                "Lift a non-directly-finite quotient witness to the source algebra.",
                "group algebra",
                critical=True,
                boundary="No quotient-only conclusion is sufficient.",
            )
        )
        memory = EpisodeMemory(self.memory.episodes)
        director = AdaptiveResearchDirector(
            trace,
            episode_memory=memory,
            domain="ring_theory",
        )
        plan = director.plan_round()
        before = director.metrics()["total_reuse_events"]
        target = next(
            match.episode.episode_id
            for match in plan.episode_matches
            if match.episode.episode_id == "EP-KAPLANSKY-CORNER-001"
        )
        self.assertEqual(before, 0)
        director.mark_plan_used(plan, used_episode_ids=(target,))
        self.assertEqual(director.metrics()["total_reuse_events"], 1)

    def test_unretrieved_episode_cannot_be_claimed_as_used(self) -> None:
        trace = ResearchTrace(
            "R",
            TheoremContract("K", "simple arithmetic", ("C",), "natural numbers"),
        )
        trace.add_claim(ClaimRecord("C", "Prove one plus one equals two.", "N"))
        director = AdaptiveResearchDirector(
            trace,
            episode_memory=EpisodeMemory(self.memory.episodes),
        )
        plan = director.plan_round(top_k_episodes=1)
        with self.assertRaisesRegex(ValueError, "not retrieved"):
            director.mark_plan_used(
                plan,
                used_episode_ids=("EP-KAPLANSKY-CORNER-001",),
            )


if __name__ == "__main__":
    unittest.main()
