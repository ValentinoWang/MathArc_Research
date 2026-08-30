from __future__ import annotations

import unittest

from matharc.v02.failure_channels import (
    FailureChannel,
    FailureChannelRecord,
    record_review_gap,
)
from matharc.v02.falsification import (
    KillTestKind,
    KillTestSpec,
    RouteEvaluationRecord,
    RouteEvaluationOutcome,
    attach_kill_test_spec,
    record_route_evaluation,
)
from matharc.v02.review import (
    NominationError,
    ObligationVerdict,
    ObligationVerdictKind,
    ReviewAuthorizationError,
    ReviewContractError,
    ReviewDecision,
    ReviewerProfile,
    ReviewerRoster,
    ReviewLifecycleStatus,
    ReviewRecord,
    can_review,
    get_reviewer_roster,
    nomination_blockers,
    nominate_for_review,
    nominations_for_claim,
    review_to_evidence,
    revoke_review,
    set_reviewer_roster,
    statement_digest_sha256,
    submit_review,
)
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolCallRecord,
    ToolStatus,
)
from matharc.v02.trace import PromotionError, ResearchTrace


def _trace_with_claim(*, critical: bool = False) -> ResearchTrace:
    trace = ResearchTrace(
        "V03-REVIEW",
        TheoremContract("K", "Prove C.", ("C",), "all symbolic inputs"),
    )
    trace.add_claim(
        ClaimRecord("C", "n + 1 = 1 + n", "all integers n", critical=critical, owner="prover-1")
    )
    trace.add_route(
        ResearchRoute(
            "R",
            "direct",
            "commute the addends",
            ("direct-computation",),
            "kill test",
            status=RouteStatus.ACTIVE,
            claim_ids=("C",),
            created_by="route-proposer",
        )
    )
    return trace


def _candidate_trace() -> ResearchTrace:
    trace = ResearchTrace(
        "V03-REVIEW-R1",
        TheoremContract("K", "Prove C.", ("C",), "all symbolic inputs"),
    )
    trace.add_claim(
        ClaimRecord(
            "C", "n + 1 = 1 + n", "all integers n", status=ClaimStatus.CANDIDATE, owner="prover-1"
        )
    )
    trace.add_route(
        ResearchRoute(
            "R",
            "direct",
            "commute the addends",
            ("direct-computation",),
            "kill test",
            status=RouteStatus.ACTIVE,
            claim_ids=("C",),
            created_by="route-proposer",
        )
    )
    return trace


def _execute_route(
    trace: ResearchTrace, *, outcome: RouteEvaluationOutcome, evaluation_id: str = "EVAL-1"
) -> None:
    spec = KillTestSpec(
        kind=KillTestKind.ENUMERATION,
        generator_spec={"range": [0, 10]},
        discriminator_spec={"check": "commutativity"},
        tested_scope="n in [0, 10)",
    )
    attach_kill_test_spec(trace, "R", spec)
    trace.add_tool_call(
        ToolCallRecord(
            call_id="TC-1",
            tool="enumeration",
            purpose="check commutativity",
            status=ToolStatus.PASS,
            input_digest_sha256="a" * 64,
            output_digest_sha256="b" * 64,
            linked_claim_ids=("C",),
            independence_group="exact:1",
            replay_command="python -m matharc.v02 replay",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T00:00:01Z",
        )
    )
    is_counterexample = outcome is RouteEvaluationOutcome.COUNTEREXAMPLE
    claim = trace.claims["C"]
    record_route_evaluation(
        trace,
        RouteEvaluationRecord(
            evaluation_id=evaluation_id,
            route_id="R",
            route_revision=0,
            claim_id="C",
            claim_revision=claim.revision,
            kill_test_spec_digest=spec.digest_sha256,
            tool_call_id="TC-1",
            outcome=outcome,
            tested_scope=spec.tested_scope,
            verifier_group="exact:1",
            replay_command="python -m matharc.v02 replay",
            witness_artifact_id="ART-1" if is_counterexample else "",
            witness_verified=is_counterexample,
        ),
    )


def _roster(*, extra: tuple[ReviewerProfile, ...] = ()) -> ReviewerRoster:
    return ReviewerRoster(
        roster_version="roster-1",
        reviewers=(
            ReviewerProfile(
                reviewer_id="reviewer-A",
                name="A",
                affiliation="Uni A",
                independence_group="group-A",
            ),
            *extra,
        ),
    )


def _approve_record(
    trace: ResearchTrace,
    *,
    review_id: str = "REV-1",
    reviewer_id: str = "reviewer-A",
    roster_version: str = "roster-1",
) -> ReviewRecord:
    claim = trace.claims["C"]
    roster = get_reviewer_roster(trace, roster_version)
    assert roster is not None
    reviewer = roster.get(reviewer_id)
    assert reviewer is not None
    record = ReviewRecord(
        review_id=review_id,
        claim_id="C",
        claim_revision=claim.revision,
        statement_digest=statement_digest_sha256(claim.statement),
        bundle_digest="b" * 64,
        reviewer_id=reviewer_id,
        reviewer_profile_digest=reviewer.digest_sha256,
        roster_version=roster_version,
        review_policy_version="policy-1",
        statement_correspondence="Formal statement matches the informal claim verbatim.",
        # OB-STATEMENT-CORRESPONDENCE is the one obligation build_review_bundle
        # always generates (R2); verdicting it by its real id, rather than a
        # placeholder, is what makes R4's per-obligation assurance check
        # (which cross-references against a freshly rebuilt bundle) resolve
        # to "satisfied" for this fixture's claim (non-critical, no
        # evidence/kill-test-spec'd route at submission time).
        verdicts=(ObligationVerdict("OB-STATEMENT-CORRESPONDENCE", ObligationVerdictKind.OK),),
        overall_decision=ReviewDecision.APPROVE,
    )
    return record.with_signature()


class ReviewRecordRoundTripTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        record = _approve_record(trace)
        restored = ReviewRecord.from_dict(record.to_dict())
        self.assertEqual(record.to_dict(), restored.to_dict())

    def test_unknown_field_is_rejected(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        payload = dict(_approve_record(trace).to_dict())
        payload["unexpected_field"] = "x"
        with self.assertRaises(ReviewContractError):
            ReviewRecord.from_dict(payload)

    def test_chain_of_thought_field_is_rejected(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        payload = dict(_approve_record(trace).to_dict())
        payload["private_chain_of_thought"] = "secret reasoning"
        with self.assertRaises(ReviewContractError):
            ReviewRecord.from_dict(payload)

    def test_empty_statement_correspondence_is_rejected(self) -> None:
        with self.assertRaises(ReviewContractError):
            ReviewRecord(
                review_id="REV-X",
                claim_id="C",
                claim_revision=0,
                statement_digest="a" * 64,
                bundle_digest="b" * 64,
                reviewer_id="reviewer-A",
                reviewer_profile_digest="c" * 64,
                roster_version="roster-1",
                review_policy_version="policy-1",
                statement_correspondence="",
                verdicts=(ObligationVerdict("OB-1", ObligationVerdictKind.OK),),
                overall_decision=ReviewDecision.APPROVE,
            )

    def test_approve_with_a_gap_verdict_is_rejected(self) -> None:
        with self.assertRaises(ReviewContractError):
            ReviewRecord(
                review_id="REV-X",
                claim_id="C",
                claim_revision=0,
                statement_digest="a" * 64,
                bundle_digest="b" * 64,
                reviewer_id="reviewer-A",
                reviewer_profile_digest="c" * 64,
                roster_version="roster-1",
                review_policy_version="policy-1",
                statement_correspondence="matches",
                verdicts=(ObligationVerdict("OB-1", ObligationVerdictKind.GAP),),
                overall_decision=ReviewDecision.APPROVE,
            )

    def test_tampered_signature_is_rejected(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        record = _approve_record(trace)
        payload = dict(record.to_dict())
        payload["review_signature"] = "0" * 64
        with self.assertRaises(ReviewContractError):
            ReviewRecord.from_dict(payload)


class RosterPinningTests(unittest.TestCase):
    def test_reinstalling_identical_roster_content_is_a_noop(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        set_reviewer_roster(trace, _roster())  # same version, same content
        roster = get_reviewer_roster(trace, "roster-1")
        assert roster is not None
        self.assertEqual(len(roster.reviewers), 1)

    def test_redefining_roster_version_with_different_content_is_rejected(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        swapped = ReviewerRoster(
            roster_version="roster-1",  # same version label
            reviewers=(
                ReviewerProfile(
                    reviewer_id="attacker-controlled",
                    name="X",
                    affiliation="",
                    independence_group="group-Z",
                ),
            ),
        )
        with self.assertRaises(ReviewContractError):
            set_reviewer_roster(trace, swapped)
        # The original roster must still be the one in effect.
        roster = get_reviewer_roster(trace, "roster-1")
        assert roster is not None
        self.assertIsNotNone(roster.get("reviewer-A"))
        self.assertIsNone(roster.get("attacker-controlled"))


class ObjectLevelAuthorizationTests(unittest.TestCase):
    def test_route_proposer_cannot_review_their_own_route(self) -> None:
        trace = _trace_with_claim()
        proposer = ReviewerProfile(
            reviewer_id="route-proposer",
            name="proposer",
            affiliation="",
            independence_group="group-B",
        )
        allowed, reason = can_review(trace, proposer, "C")
        self.assertFalse(allowed)
        self.assertIn("route-proposer", reason)

    def test_evidence_producer_cannot_review_the_same_claim(self) -> None:
        trace = _trace_with_claim()
        trace.add_evidence(
            EvidenceRecord(
                evidence_id="EV-EXISTING",
                claim_ids=("C",),
                kind=EvidenceKind.EXACT_COMPUTATION,
                status=EvidenceStatus.ACCEPTED,
                summary="direct computation",
                artifact_uri="mem://existing",
                digest_sha256="d" * 64,
                producer="prover-2",
                verifier="prover-2",
                independence_group="exact:1",
                statement_correspondence="matches",
            )
        )
        producer = ReviewerProfile(
            reviewer_id="prover-2",
            name="producer",
            affiliation="",
            independence_group="group-B",
        )
        allowed, reason = can_review(trace, producer, "C")
        self.assertFalse(allowed)

    def test_conflict_of_interest_overlap_is_rejected(self) -> None:
        trace = _trace_with_claim()
        conflicted = ReviewerProfile(
            reviewer_id="reviewer-C",
            name="C",
            affiliation="",
            independence_group="group-C",
            conflict_of_interest_ids=("route-proposer",),
        )
        allowed, reason = can_review(trace, conflicted, "C")
        self.assertFalse(allowed)

    def test_unconflicted_reviewer_is_allowed(self) -> None:
        trace = _trace_with_claim()
        reviewer = ReviewerProfile(
            reviewer_id="reviewer-A",
            name="A",
            affiliation="",
            independence_group="group-A",
        )
        allowed, reason = can_review(trace, reviewer, "C")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")


class SubmitAndPromoteTests(unittest.TestCase):
    def test_full_happy_path_promotes_the_claim(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        record = _approve_record(trace)
        submit_review(trace, record)
        evidence = review_to_evidence(
            trace, "REV-1", evidence_id="EV-REVIEW-1", artifact_uri="mem://review-1"
        )
        trace.add_evidence(evidence)
        trace.promote_claim("C")
        self.assertEqual(trace.claims["C"].status.value, "PROVED")

    def test_reviewer_outside_roster_is_rejected(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        claim = trace.claims["C"]
        record = ReviewRecord(
            review_id="REV-GHOST",
            claim_id="C",
            claim_revision=claim.revision,
            statement_digest=statement_digest_sha256(claim.statement),
            bundle_digest="b" * 64,
            reviewer_id="ghost-reviewer",
            reviewer_profile_digest="f" * 64,
            roster_version="roster-1",
            review_policy_version="policy-1",
            statement_correspondence="matches",
            verdicts=(ObligationVerdict("OB-1", ObligationVerdictKind.OK),),
            overall_decision=ReviewDecision.APPROVE,
        ).with_signature()
        # Constructing the record itself succeeds (schema-level only knows
        # about digests, not roster membership); submission is where roster
        # membership is enforced.
        with self.assertRaises(ReviewAuthorizationError):
            submit_review(trace, record)

    def test_conflicted_reviewer_submission_is_rejected(self) -> None:
        trace = _trace_with_claim()
        conflicted = ReviewerProfile(
            reviewer_id="reviewer-C",
            name="C",
            affiliation="",
            independence_group="group-C",
            conflict_of_interest_ids=("route-proposer",),
        )
        set_reviewer_roster(trace, _roster(extra=(conflicted,)))
        record = _approve_record(trace, reviewer_id="reviewer-C")
        with self.assertRaises(ReviewAuthorizationError):
            submit_review(trace, record)

    def test_duplicate_review_id_is_rejected(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        submit_review(trace, _approve_record(trace))
        with self.assertRaises(ReviewContractError):
            submit_review(trace, _approve_record(trace))

    def test_stale_claim_revision_submission_is_rejected(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        record = _approve_record(trace)
        trace.revise_claim("C", statement="n + 1 = 1 + n (restated)")
        with self.assertRaises(ReviewContractError):
            submit_review(trace, record)

    def test_non_approve_decision_cannot_become_evidence(self) -> None:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        claim = trace.claims["C"]
        roster = get_reviewer_roster(trace, "roster-1")
        assert roster is not None
        reviewer = roster.get("reviewer-A")
        assert reviewer is not None
        record = ReviewRecord(
            review_id="REV-GAP",
            claim_id="C",
            claim_revision=claim.revision,
            statement_digest=statement_digest_sha256(claim.statement),
            bundle_digest="b" * 64,
            reviewer_id="reviewer-A",
            reviewer_profile_digest=reviewer.digest_sha256,
            roster_version="roster-1",
            review_policy_version="policy-1",
            statement_correspondence="matches",
            verdicts=(ObligationVerdict("OB-1", ObligationVerdictKind.GAP, "missing step"),),
            overall_decision=ReviewDecision.REQUEST_CHANGES,
        ).with_signature()
        submit_review(trace, record)
        with self.assertRaises(ReviewContractError):
            review_to_evidence(trace, "REV-GAP", evidence_id="EV-X", artifact_uri="mem://x")


class LifecycleInvalidationTests(unittest.TestCase):
    def _promoted_trace(self) -> ResearchTrace:
        trace = _trace_with_claim()
        set_reviewer_roster(trace, _roster())
        submit_review(trace, _approve_record(trace))
        evidence = review_to_evidence(
            trace, "REV-1", evidence_id="EV-REVIEW-1", artifact_uri="mem://review-1"
        )
        trace.add_evidence(evidence)
        return trace

    def test_claim_revision_bump_makes_review_evidence_unable_to_promote(self) -> None:
        trace = self._promoted_trace()
        # Promotion works before the statement changes.
        trace.promote_claim("C")

        trace2 = self._promoted_trace()
        trace2.revise_claim("C", statement="n + 1 = 1 + n (restated)")
        with self.assertRaises(PromotionError) as ctx:
            trace2.promote_claim("C")
        self.assertIn("stale review-derived evidence", str(ctx.exception))

    def test_revoked_review_evidence_is_marked_stale_immediately(self) -> None:
        trace = self._promoted_trace()
        revoke_review(trace, "REV-1", "conflict of interest discovered after submission")
        self.assertEqual(trace.evidence["EV-REVIEW-1"].status, EvidenceStatus.STALE)
        with self.assertRaises(PromotionError):
            trace.promote_claim("C")

    def test_revoked_review_record_lifecycle_status(self) -> None:
        trace = self._promoted_trace()
        updated = revoke_review(trace, "REV-1", "reason")
        self.assertEqual(updated.lifecycle_status, ReviewLifecycleStatus.REVOKED)
        self.assertEqual(updated.revoked_reason, "reason")


class NominationTests(unittest.TestCase):
    def test_non_candidate_claim_is_blocked(self) -> None:
        trace = _trace_with_claim()  # status defaults to OPEN, not CANDIDATE
        reasons = nomination_blockers(trace, "C")
        self.assertTrue(any("not CANDIDATE" in item for item in reasons))
        with self.assertRaises(NominationError) as ctx:
            nominate_for_review(trace, "C")
        self.assertTrue(ctx.exception.reasons)

    def test_candidate_with_no_execution_record_is_blocked(self) -> None:
        trace = _candidate_trace()
        reasons = nomination_blockers(trace, "C")
        self.assertTrue(any("without a completed" in item for item in reasons))

    def test_candidate_with_only_inconclusive_record_is_blocked(self) -> None:
        trace = _candidate_trace()
        _execute_route(trace, outcome=RouteEvaluationOutcome.INCONCLUSIVE)
        reasons = nomination_blockers(trace, "C")
        self.assertTrue(any("without a completed" in item for item in reasons))

    def test_candidate_with_pass_bounded_route_is_nominated(self) -> None:
        trace = _candidate_trace()
        _execute_route(trace, outcome=RouteEvaluationOutcome.PASS_BOUNDED)
        record = nominate_for_review(trace, "C")
        self.assertEqual(record.claim_id, "C")
        self.assertEqual(record.route_ids, ("R",))
        self.assertIn(record, nominations_for_claim(trace, "C"))

    def test_candidate_with_counterexample_outcome_route_is_nominated(self) -> None:
        # A verified COUNTEREXAMPLE is still a *determinate* execution result
        # (as opposed to INCONCLUSIVE/ERROR); it is a settled, reviewable
        # state even though it is a negative one.
        trace = _candidate_trace()
        _execute_route(trace, outcome=RouteEvaluationOutcome.COUNTEREXAMPLE)
        record = nominate_for_review(trace, "C")
        self.assertEqual(record.route_ids, ("R",))

    def test_open_review_gap_blocks_renomination(self) -> None:
        trace = _candidate_trace()
        _execute_route(trace, outcome=RouteEvaluationOutcome.PASS_BOUNDED)
        record_review_gap(
            trace,
            FailureChannelRecord(
                event_id="GAP-1",
                channel=FailureChannel.REVIEW_GAP,
                claim_id="C",
                claim_revision=trace.claims["C"].revision,
                description="statement correspondence needs another pass",
            ),
        )
        reasons = nomination_blockers(trace, "C")
        self.assertTrue(any("open ReviewGap" in item for item in reasons))
        with self.assertRaises(NominationError):
            nominate_for_review(trace, "C")

    def test_unknown_claim_is_blocked(self) -> None:
        trace = _candidate_trace()
        reasons = nomination_blockers(trace, "NOPE")
        self.assertTrue(any("unknown claim" in item for item in reasons))


if __name__ == "__main__":
    unittest.main()
