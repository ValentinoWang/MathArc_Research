from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.episode_memory import EpisodeMemory, ResearchEpisode


class EpisodeMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.memory = EpisodeMemory.load_jsonl(
            cls.root / "memory" / "research_episodes_v02.jsonl"
        )

    def test_seed_dataset_is_complete_and_unique(self) -> None:
        metrics = self.memory.metrics()
        self.assertGreaterEqual(metrics["episode_count"], 15)
        self.assertGreaterEqual(metrics["domain_count"], 7)
        ids = [episode.episode_id for episode in self.memory.episodes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_yang_mills_query_retrieves_scope_and_bridge_lessons(self) -> None:
        matches = self.memory.query(
            "A bounded finite-volume quantum-group construction is being promoted to full Yang-Mills mass gap without an infinite-volume bridge.",
            domain="mathematical_physics",
            top_k=5,
        )
        ids = {match.episode.episode_id for match in matches}
        self.assertIn("EP-YMS-SCOPE-001", ids)
        self.assertTrue(
            any("domain match" in match.rationale for match in matches)
        )

    def test_finite_search_query_retrieves_local_to_global_episode(self) -> None:
        matches = self.memory.query(
            "Exact UNSAT in one frozen neighborhood is being used as a global construction theorem.",
            failure_classes=("FINITE_TO_GLOBAL",),
            top_k=5,
        )
        self.assertTrue(matches)
        self.assertEqual(matches[0].episode.failure_class, "FINITE_TO_GLOBAL")
        self.assertTrue(matches[0].matched_terms)

    def test_episode_is_planning_context_not_proof_evidence(self) -> None:
        context = self.memory.planner_context(
            "A quotient counterexample is being lifted to the source algebra.",
            domain="ring_theory",
        )
        self.assertTrue(context["episodes"])
        self.assertIn("not premises", context["instruction"])
        self.assertEqual(
            context["episodes"][0]["episode_id"],
            "EP-KAPLANSKY-CORNER-001",
        )

    def test_reuse_is_measured_explicitly(self) -> None:
        memory = EpisodeMemory(self.memory.episodes)
        memory.mark_reused("EP-STC-IFF-001")
        metrics = memory.metrics()
        self.assertEqual(metrics["episodes_reused"], 1)
        self.assertEqual(metrics["total_reuse_events"], 1)
        self.assertGreater(metrics["episode_reuse_rate"], 0)

    def test_jsonl_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.memory.save_jsonl(Path(directory) / "episodes.jsonl")
            loaded = EpisodeMemory.load_jsonl(path)
        self.assertEqual(
            [item.to_dict() for item in loaded.episodes],
            [item.to_dict() for item in self.memory.episodes],
        )

    def test_unknown_fields_are_rejected(self) -> None:
        payload = self.memory.episodes[0].to_dict()
        payload["private_chain_of_thought"] = "forbidden"
        with self.assertRaisesRegex(ValueError, "unknown"):
            ResearchEpisode.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
