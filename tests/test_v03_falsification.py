from __future__ import annotations

import tempfile
import unittest

from matharc.v02.campaign import ResearchCampaign
from matharc.v02.falsification import (
    FalsificationContractError,
    KillTestKind,
    KillTestSpec,
    RouteEvaluationOutcome,
    attach_kill_test_spec,
    evaluation_from_tool_call,
    iter_route_evaluations,
    record_route_evaluation,
)
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolCallRecord,
    ToolStatus,
    utc_now,
)
from matharc.v02.trace import PromotionError, ResearchTrace
from matharc.v02.workers import StaticProposalWorker
from matharc.v02.workspace import ResearchWorkspace


def _trace() -> ResearchTrace:
    trace = ResearchTrace(
        "V03-FALSIFICATION",
        TheoremContract("K", "Prove C.", ("C",), "all symbolic inputs"),
    )
    trace.add_claim(ClaimRecord("C", "n + 1 = 1 + n", "all integers n"))
    trace.add_route(
        ResearchRoute(
            "R",
            "symbolic normalization",
            "commutativity closes the identity",
            ("symbolic polynomial normalization",),
            "compare both sides exactly",
            RouteStatus.ACTIVE,
            ("C",),
        )
    )
    return trace


def _spec(kind: KillTestKind = KillTestKind.INSTANCE_EVAL) -> KillTestSpec:
    return KillTestSpec(
        kind=kind,
        generator_spec={"family": "symbolic-identity", "variable": "n"},
        discriminator_spec={"tool": "polynomial_identity", "expect": "PASS"},
        tested_scope="the declared symbolic identity",
        max_cases=1,
        seed=7 if kind is KillTestKind.PROPERTY_RANDOM else None,
    )


def _tool_call(call_id: str = "T-CHECK") -> ToolCallRecord:
    now = utc_now()
    return ToolCallRecord(
        call_id=call_id,
        tool="test",
        purpose="deterministic route check",
        status=ToolStatus.PASS,
        input_digest_sha256="a" * 64,
        output_digest_sha256="b" * 64,
        linked_claim_ids=("C",),
        independence_group="checker",
        replay_command="python replay.py",
        started_at=now,
        ended_at=now,
        environment_digest_sha256="c" * 64,
    )


def _proposal(*, route_id: str | None) -> dict[str, object]:
    request: dict[str, object] = {
        "tool": "polynomial_identity",
        "purpose": "check the route kill test",
        "arguments": {"lhs": "n+1", "rhs": "1+n", "variable": "n"},
    }
    if route_id is not None:
        request["route_id"] = route_id
    return {
        "status": "progress",
        "public_reasoning": {
            "objective": "test the current route before promotion",
            "premises": [],
            "proposed_move": "run exact symbolic normalization",
            "observation": "the exact checker decides the bounded route test",
            "falsification": "a non-zero coefficient difference kills the route",
            "decision": "use the result only in its declared scope",
        },
        "tool_requests": [request],
        "claim_boundary": "the worker does not self-promote",
    }


class FalsificationContractTests(unittest.TestCase):
    def test_kill_test_spec_round_trip_and_unknown_fields_are_rejected(self) -> None:
        spec = _spec()
        self.assertEqual(KillTestSpec.from_dict(spec.to_dict()).digest_sha256, spec.digest_sha256)
        payload = spec.to_dict()
        payload["surprise"] = True
        with self.assertRaises(FalsificationContractError):
            KillTestSpec.from_dict(payload)

    def test_kill_test_identity_excludes_provenance_timestamp(self) -> None:
        first = KillTestSpec(
            kind=KillTestKind.ENUMERATION,
            generator_spec={"family": "small-cases"},
            discriminator_spec={"predicate": "violates-target"},
            tested_scope="n <= 8",
            created_at="2026-08-27T00:00:00+00:00",
        )
        second = KillTestSpec(
            kind=KillTestKind.ENUMERATION,
            generator_spec={"family": "small-cases"},
            discriminator_spec={"predicate": "violates-target"},
            tested_scope="n <= 8",
            created_at="2026-08-28T00:00:00+00:00",
        )
        self.assertNotEqual(first.created_at, second.created_at)
        self.assertEqual(first.digest_sha256, second.digest_sha256)

    def test_random_no_counterexample_is_inconclusive_not_pass(self) -> None:
        trace = _trace()
        attach_kill_test_spec(trace, "R", _spec(KillTestKind.PROPERTY_RANDOM))
        call = _tool_call("T-RANDOM")
        trace.add_tool_call(call)
        record = evaluation_from_tool_call(
            trace,
            evaluation_id="EV-RANDOM",
            route_id="R",
            claim_id="C",
            tool_call=call,
        )
        self.assertEqual(record.outcome, RouteEvaluationOutcome.INCONCLUSIVE)

    def test_stale_claim_revision_cannot_accept_old_route_evaluation(self) -> None:
        trace = _trace()
        spec = _spec()
        attach_kill_test_spec(trace, "R", spec)
        call = _tool_call("T-STALE")
        trace.add_tool_call(call)
        record = evaluation_from_tool_call(
            trace,
            evaluation_id="EV-STALE",
            route_id="R",
            claim_id="C",
            tool_call=call,
        )
        trace.revise_claim("C", statement="n + 1 = 1 + n for all declared n")
        with self.assertRaisesRegex(FalsificationContractError, "stale"):
            record_route_evaluation(trace, record)

    def test_campaign_records_route_evaluation_before_promotion(self) -> None:
        trace = _trace()
        attach_kill_test_spec(trace, "R", _spec())
        report = ResearchCampaign(
            trace,
            [StaticProposalWorker("prover", _proposal(route_id="R"))],
            max_rounds=1,
            max_rounds_without_gain=1,
        ).run()
        self.assertEqual(trace.claims["C"].status, ClaimStatus.PROVED)
        records = iter_route_evaluations(trace)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].outcome, RouteEvaluationOutcome.PASS_BOUNDED)
        tool_result = report.rounds[0]["workers"][0]["executed_tools"][0]
        self.assertEqual(
            tool_result["route_evaluation"]["status"], "ROUTE_EVALUATION_RECORDED"
        )
        self.assertTrue(tool_result["promoted"])

    def test_structured_route_without_attributed_evaluation_blocks_all_promotion_paths(self) -> None:
        trace = _trace()
        attach_kill_test_spec(trace, "R", _spec())
        report = ResearchCampaign(
            trace,
            [StaticProposalWorker("prover", _proposal(route_id=None))],
            max_rounds=1,
            max_rounds_without_gain=1,
        ).run()
        self.assertNotEqual(trace.claims["C"].status, ClaimStatus.PROVED)
        tool_result = report.rounds[0]["workers"][0]["executed_tools"][0]
        self.assertEqual(tool_result["promotion_blockers"], ["R"])
        self.assertFalse(tool_result["promoted"])
        with self.assertRaisesRegex(PromotionError, "PASS_BOUNDED"):
            trace.promote_claim("C")

    def test_workspace_audit_consumes_the_shared_route_evaluation_record(self) -> None:
        missing = _trace()
        attach_kill_test_spec(missing, "R", _spec())
        with tempfile.TemporaryDirectory() as directory:
            report = ResearchWorkspace(directory, missing, strict_artifacts=False).audit()
        messages = [item.message for item in report.issues]
        self.assertTrue(
            any("no current PASS_BOUNDED RouteEvaluationRecord" in item for item in messages),
            messages,
        )

        passing = _trace()
        attach_kill_test_spec(passing, "R", _spec())
        call = _tool_call("T-AUDIT-PASS")
        passing.add_tool_call(call)
        record = evaluation_from_tool_call(
            passing,
            evaluation_id="EV-AUDIT-PASS",
            route_id="R",
            claim_id="C",
            tool_call=call,
        )
        record_route_evaluation(passing, record)
        with tempfile.TemporaryDirectory() as directory:
            report = ResearchWorkspace(directory, passing, strict_artifacts=False).audit()
        messages = [item.message for item in report.issues]
        self.assertFalse(
            any("no current PASS_BOUNDED RouteEvaluationRecord" in item for item in messages),
            messages,
        )


if __name__ == "__main__":
    unittest.main()
