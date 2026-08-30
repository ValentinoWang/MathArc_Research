from __future__ import annotations

import unittest

from matharc.v02.review import (
    ObligationVerdict,
    ObligationVerdictKind,
    ReviewDecision,
    ReviewerProfile,
    ReviewerRoster,
    ReviewRecord,
    review_to_evidence,
    set_reviewer_roster,
    statement_digest_sha256,
    submit_review,
)
from matharc.v02.review_policy import (
    ClosureTrustClass,
    claim_closure_trust_class,
    review_gate_applies,
)
from matharc.v02.metrics import compute_research_metrics
from matharc.v02.schema import (
    ClaimRecord,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
)
from matharc.v02.trace import PromotionError, ResearchTrace

_GROUP_A = ReviewerProfile(
    reviewer_id="reviewer-A", name="A", affiliation="", independence_group="group-A"
)
_GROUP_B = ReviewerProfile(
    reviewer_id="reviewer-B", name="B", affiliation="", independence_group="group-B"
)


def _roster() -> ReviewerRoster:
    return ReviewerRoster(roster_version="roster-1", reviewers=(_GROUP_A, _GROUP_B))


def _critical_trace() -> ResearchTrace:
    trace = ResearchTrace("V03-POLICY", TheoremContract("K", "p", ("C",), "s"))
    trace.add_claim(ClaimRecord("C", "n + 1 = 1 + n", "all integers n", critical=True, owner="p1"))
    trace.add_route(
        ResearchRoute(
            "R",
            "direct",
            "commute",
            ("m",),
            "kt",
            status=RouteStatus.ACTIVE,
            claim_ids=("C",),
            created_by="route-proposer",
        )
    )
    return trace


def _approve(trace: ResearchTrace, *, review_id: str, reviewer: ReviewerProfile) -> ReviewRecord:
    claim = trace.claims["C"]
    return ReviewRecord(
        review_id=review_id,
        claim_id="C",
        claim_revision=claim.revision,
        statement_digest=statement_digest_sha256(claim.statement),
        bundle_digest="b" * 64,
        reviewer_id=reviewer.reviewer_id,
        reviewer_profile_digest=reviewer.digest_sha256,
        roster_version="roster-1",
        review_policy_version="policy-1",
        statement_correspondence="matches",
        verdicts=(
            ObligationVerdict("OB-STATEMENT-CORRESPONDENCE", ObligationVerdictKind.OK),
            ObligationVerdict("OB-INDEPENDENCE", ObligationVerdictKind.OK),
        ),
        overall_decision=ReviewDecision.APPROVE,
    ).with_signature()


class OptInBoundaryTests(unittest.TestCase):
    def test_pure_machine_claim_is_untouched_by_the_gate(self) -> None:
        trace = ResearchTrace("T", TheoremContract("K", "p", ("C",), "s"))
        trace.add_claim(ClaimRecord("C", "s", "scope", critical=True, owner="p1"))
        trace.add_evidence(
            EvidenceRecord(
                evidence_id="EV1",
                claim_ids=("C",),
                kind=EvidenceKind.EXACT_COMPUTATION,
                status=EvidenceStatus.ACCEPTED,
                summary="s",
                artifact_uri="u",
                digest_sha256="a" * 64,
                producer="p1",
                verifier="p2",
                independence_group="g1",
                replay_command="r",
                statement_correspondence="m",
            )
        )
        trace.add_evidence(
            EvidenceRecord(
                evidence_id="EV2",
                claim_ids=("C",),
                kind=EvidenceKind.EXACT_COMPUTATION,
                status=EvidenceStatus.ACCEPTED,
                summary="s",
                artifact_uri="u",
                digest_sha256="b" * 64,
                producer="p3",
                verifier="p4",
                independence_group="g2",
                replay_command="r",
                statement_correspondence="m",
            )
        )
        self.assertFalse(review_gate_applies(trace, "C"))
        self.assertEqual(claim_closure_trust_class(trace, "C"), ClosureTrustClass.MACHINE)
        # Two independent EXACT groups on a critical claim: promotes with
        # zero interaction with review.py, exactly as before R4 existed.
        trace.promote_claim("C")
        self.assertEqual(trace.claims["C"].status.value, "PROVED")


class SingleGroupCriticalClaimTests(unittest.TestCase):
    def test_critical_claim_closing_on_a_single_human_audit_group_is_rejected(self) -> None:
        trace = _critical_trace()
        set_reviewer_roster(trace, _roster())
        record = _approve(trace, review_id="REV-1", reviewer=_GROUP_A)
        submit_review(trace, record)
        evidence = review_to_evidence(
            trace, "REV-1", evidence_id="EV-REV-1", artifact_uri="review:REV-1"
        )
        trace.add_evidence(evidence)

        self.assertTrue(review_gate_applies(trace, "C"))
        self.assertEqual(claim_closure_trust_class(trace, "C"), ClosureTrustClass.HUMAN)
        with self.assertRaises(PromotionError) as ctx:
            trace.promote_claim("C")
        message = str(ctx.exception)
        self.assertIn("OB-INDEPENDENCE", message)
        self.assertIn("HUMAN_DOUBLE", message)
        # boundary_violations gets a durable record naming the claim.
        self.assertTrue(trace.boundary_violations)
        self.assertEqual(trace.boundary_violations[-1]["claim_id"], "C")


class TwoIndependentGroupsTests(unittest.TestCase):
    def test_critical_claim_with_two_independent_human_audit_groups_promotes(self) -> None:
        trace = _critical_trace()
        set_reviewer_roster(trace, _roster())

        submit_review(trace, _approve(trace, review_id="REV-A", reviewer=_GROUP_A))
        evidence_a = review_to_evidence(
            trace, "REV-A", evidence_id="EV-A", artifact_uri="review:REV-A"
        )
        trace.add_evidence(evidence_a)

        submit_review(trace, _approve(trace, review_id="REV-B", reviewer=_GROUP_B))
        evidence_b = review_to_evidence(
            trace, "REV-B", evidence_id="EV-B", artifact_uri="review:REV-B"
        )
        trace.add_evidence(evidence_b)

        trace.promote_claim("C")
        self.assertEqual(trace.claims["C"].status.value, "PROVED")

        metrics = compute_research_metrics(trace)
        snapshot = metrics["review_assurance"]["C"]
        self.assertEqual(snapshot["closure_trust_class"], "human")
        self.assertTrue(snapshot["review_gate_applies"])
        obligation_ids = {item["obligation_id"] for item in snapshot["obligations"]}
        self.assertIn("OB-INDEPENDENCE", obligation_ids)
        independence_row = next(
            item for item in snapshot["obligations"] if item["obligation_id"] == "OB-INDEPENDENCE"
        )
        self.assertTrue(independence_row["satisfied"])
        self.assertEqual(independence_row["achieved_assurance"], "HUMAN_DOUBLE")
        self.assertEqual(sorted(independence_row["supporting_reviewer_groups"]), ["group-A", "group-B"])


class MixedTrustClassTests(unittest.TestCase):
    def test_mixed_evidence_reports_mixed_trust_class(self) -> None:
        trace = _critical_trace()
        trace.add_evidence(
            EvidenceRecord(
                evidence_id="EV-EXACT",
                claim_ids=("C",),
                kind=EvidenceKind.EXACT_COMPUTATION,
                status=EvidenceStatus.ACCEPTED,
                summary="s",
                artifact_uri="u",
                digest_sha256="a" * 64,
                producer="p1",
                verifier="p2",
                independence_group="g1",
                replay_command="r",
                statement_correspondence="m",
            )
        )
        set_reviewer_roster(trace, _roster())
        submit_review(trace, _approve(trace, review_id="REV-A", reviewer=_GROUP_A))
        evidence_a = review_to_evidence(
            trace, "REV-A", evidence_id="EV-A", artifact_uri="review:REV-A"
        )
        trace.add_evidence(evidence_a)
        self.assertEqual(claim_closure_trust_class(trace, "C"), ClosureTrustClass.MIXED)


if __name__ == "__main__":
    unittest.main()
