from __future__ import annotations

import hashlib
import unittest

from matharc.v02.benchmark import BenchmarkResult, compare_agents, compare_against_all


def result(
    system: str,
    case: int,
    score: float,
    *,
    false_promotion: bool = False,
    replay: bool = True,
    budget: float = 100.0,
) -> BenchmarkResult:
    return BenchmarkResult(
        system_name=system,
        suite_id="PINNED-SUITE",
        suite_version="1.0",
        case_id=f"case-{case}",
        seed=case,
        metrics={"audited_closure": score},
        release_state="PROVED_AND_AUDITED" if score == 1 else "BLOCKED_EXACT",
        false_promotion=false_promotion,
        replay_pass=replay,
        budget_units=budget,
        runtime_seconds=1.0,
        artifact_digest_sha256=hashlib.sha256(f"{system}-{case}".encode()).hexdigest(),
    )


class BenchmarkQualificationTests(unittest.TestCase):
    def test_missing_baseline_never_allows_superiority(self) -> None:
        comparison = compare_agents(
            [result("candidate", 0, 1.0)],
            [],
            metric_directions={"audited_closure": "maximize"},
            primary_metrics=("audited_closure",),
        )
        self.assertFalse(comparison.superiority_claim_allowed)
        self.assertEqual(comparison.qualification_state, "INSUFFICIENT_EVIDENCE")

    def test_constant_positive_paired_delta_can_qualify(self) -> None:
        candidate = [result("candidate", index, 1.0) for index in range(30)]
        baseline = [result("baseline", index, 0.5) for index in range(30)]
        comparison = compare_agents(
            candidate,
            baseline,
            metric_directions={"audited_closure": "maximize"},
            primary_metrics=("audited_closure",),
            minimum_pairs=30,
            bootstrap_samples=300,
        )
        self.assertTrue(comparison.superiority_claim_allowed, comparison.to_dict())
        self.assertEqual(
            comparison.qualification_state,
            "QUALIFIED_SUPERIOR_ON_PINNED_SUITE",
        )
        self.assertGreater(comparison.deltas[0].confidence_low, 0)

    def test_false_promotion_blocks_claim_even_with_high_score(self) -> None:
        candidate = [
            result("candidate", index, 1.0, false_promotion=index == 0)
            for index in range(30)
        ]
        baseline = [result("baseline", index, 0.5) for index in range(30)]
        comparison = compare_agents(
            candidate,
            baseline,
            metric_directions={"audited_closure": "maximize"},
            primary_metrics=("audited_closure",),
            minimum_pairs=30,
            bootstrap_samples=200,
        )
        self.assertFalse(comparison.superiority_claim_allowed)
        self.assertEqual(comparison.candidate_false_promotions, 1)

    def test_budget_mismatch_blocks_claim(self) -> None:
        candidate = [result("candidate", index, 1.0, budget=101.0) for index in range(30)]
        baseline = [result("baseline", index, 0.5, budget=100.0) for index in range(30)]
        comparison = compare_agents(
            candidate,
            baseline,
            metric_directions={"audited_closure": "maximize"},
            primary_metrics=("audited_closure",),
            minimum_pairs=30,
            bootstrap_samples=200,
        )
        self.assertFalse(comparison.superiority_claim_allowed)
        self.assertFalse(comparison.equal_budget)

    def test_all_baseline_claim_requires_every_pairwise_gate(self) -> None:
        candidate = [result("candidate", index, 1.0) for index in range(30)]
        strong_baseline = [result("strong", index, 1.0) for index in range(30)]
        weak_baseline = [result("weak", index, 0.4) for index in range(30)]
        summary = compare_against_all(
            candidate,
            {"weak": weak_baseline, "strong": strong_baseline},
            metric_directions={"audited_closure": "maximize"},
            primary_metrics=("audited_closure",),
            minimum_pairs=30,
            bootstrap_samples=200,
        )
        self.assertFalse(summary["all_baselines_qualified"])
        self.assertIn("No all-baseline", summary["permitted_claim"])


if __name__ == "__main__":
    unittest.main()
