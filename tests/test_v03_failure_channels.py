from __future__ import annotations

import unittest

from matharc.v02.episode_memory import EpisodeMemory
from matharc.v02.failure_channels import (
    FailureChannel,
    FailureChannelError,
    FailureChannelRecord,
    record_claim_counterexample,
    record_review_gap,
    record_route_failure,
)
from matharc.v02.research_director import AdaptiveResearchDirector
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
)
from matharc.v02.trace import PromotionError, ResearchTrace


def _trace(*, with_descendant: bool = False) -> ResearchTrace:
    trace = ResearchTrace(
        "V03-FAILURE-CHANNELS",
        TheoremContract("K", "Decide C.", ("C",), "declared scope"),
    )
    trace.add_claim(ClaimRecord("C", "C", "declared scope"))
    if with_descendant:
        trace.add_claim(
            ClaimRecord(
                "D",
                "D follows from C",
                "declared scope",
                dependencies=("C",),
            )
        )
    trace.add_route(
        ResearchRoute(
            "R",
            "candidate route",
            "this mechanism may prove C",
            ("mechanism-r",),
            "look for a counterexample",
            RouteStatus.ACTIVE,
            ("C",),
        )
    )
    return trace


def _counterexample(
    *,
    evidence_id: str = "E-CEX",
    producer: str = "counterexample-generator",
    verifier: str = "independent-checker",
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim_ids=("C",),
        kind=EvidenceKind.COUNTEREXAMPLE,
        status=EvidenceStatus.ACCEPTED,
        summary="Explicit witness falsifies C.",
        artifact_uri=f"workspace://{evidence_id}",
        digest_sha256="d" * 64,
        producer=producer,
        verifier=verifier,
        independence_group="counterexample:independent",
        replay_command=f"python replay.py {evidence_id}",
        statement_correspondence="The replayed witness satisfies C's assumptions and negates C.",
    )


class FailureChannelTests(unittest.TestCase):
    def test_review_gap_changes_no_mathematical_status_and_reenters_planning(self) -> None:
        trace = _trace()
        record_review_gap(
            trace,
            FailureChannelRecord(
                event_id="GAP-1",
                channel=FailureChannel.REVIEW_GAP,
                claim_id="C",
                claim_revision=0,
                description="Check the quantifier order in the second reduction.",
            ),
        )
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)
        self.assertEqual(trace.routes["R"].status, RouteStatus.ACTIVE)
        plan = AdaptiveResearchDirector(
            trace,
            episode_memory=EpisodeMemory(),
        ).plan_round()
        self.assertTrue(
            any("GAP-1" in item and "quantifier order" in item for item in plan.mandatory_attack_tests),
            plan.mandatory_attack_tests,
        )

    def test_route_failure_kills_only_the_route(self) -> None:
        trace = _trace()
        record_route_failure(
            trace,
            FailureChannelRecord(
                event_id="RF-1",
                channel=FailureChannel.ROUTE_FAILURE,
                claim_id="C",
                claim_revision=0,
                route_id="R",
                description="The route's bridge lemma fails on a boundary instance.",
            ),
        )
        self.assertEqual(trace.routes["R"].status, RouteStatus.BLOCKED)
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)

    def test_counterexample_evidence_cannot_be_used_as_positive_proof(self) -> None:
        trace = _trace()
        trace.add_evidence(_counterexample())
        with self.assertRaisesRegex(PromotionError, "no accepted proof-capable evidence"):
            trace.promote_claim("C")
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)

    def test_claim_counterexample_requires_independent_replayable_evidence(self) -> None:
        trace = _trace()
        trace.add_evidence(
            _counterexample(
                evidence_id="E-SELF",
                producer="same-checker",
                verifier="same-checker",
            )
        )
        with self.assertRaisesRegex(FailureChannelError, "independently"):
            record_claim_counterexample(
                trace,
                FailureChannelRecord(
                    event_id="CEX-BAD",
                    channel=FailureChannel.CLAIM_COUNTEREXAMPLE,
                    claim_id="C",
                    claim_revision=0,
                    route_id="R",
                    description="self-verified witness",
                    evidence_ids=("E-SELF",),
                    exact=True,
                ),
            )
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)

    def test_verified_claim_counterexample_refutes_claim_and_blocks_descendants(self) -> None:
        trace = _trace(with_descendant=True)
        trace.add_evidence(_counterexample())
        failure = record_claim_counterexample(
            trace,
            FailureChannelRecord(
                event_id="CEX-1",
                channel=FailureChannel.CLAIM_COUNTEREXAMPLE,
                claim_id="C",
                claim_revision=0,
                route_id="R",
                description="The explicit witness violates the universal conclusion.",
                evidence_ids=("E-CEX",),
                exact=True,
            ),
        )
        self.assertTrue(failure.exact)
        self.assertEqual(trace.claims["C"].status, ClaimStatus.REFUTED)
        self.assertEqual(trace.routes["R"].status, RouteStatus.FALSIFIED)
        self.assertEqual(trace.claims["D"].status, ClaimStatus.BLOCKED)
        self.assertIn("D", failure.invalidated_claim_ids)


if __name__ == "__main__":
    unittest.main()
