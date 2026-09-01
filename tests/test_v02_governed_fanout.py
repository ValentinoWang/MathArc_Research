from __future__ import annotations

import unittest

from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.orchestrator import (
    MAX_SPAWN_BUDGET_PER_REQUEST,
    MAX_SPAWN_DEPTH,
    MAX_SPAWN_REQUESTS_PER_ROUND,
    ResearchOrchestrator,
)
from matharc.v02.schema import (
    ClaimRecord,
    FailureClass,
    FailureRecord,
    ResearchRoute,
    RouteStatus,
    SpawnDecisionStatus,
    TheoremContract,
)
from matharc.v02.trace import ResearchTrace
from matharc.v02.workers import StaticProposalWorker


def empty_trace() -> ResearchTrace:
    trace = ResearchTrace(
        "FANOUT-TEST",
        TheoremContract(
            "FANOUT-CONTRACT",
            "Prove C.",
            ("C",),
            "The declared test scope.",
        ),
    )
    trace.add_claim(ClaimRecord("C", "C", "test scope"))
    return trace


def proposal(**extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "public_reasoning": {
            "objective": "record a governed request",
            "premises": [],
            "proposed_move": "request a declarative child descriptor",
            "observation": "the request is bounded",
            "falsification": "check the governance caps",
            "decision": "keep the parent proposal auditable",
        }
    }
    value.update(extra)
    return value


class GovernedFanoutTests(unittest.TestCase):
    def test_every_request_gets_an_immutable_decision_and_approval_is_descriptor_only(self) -> None:
        orchestrator = ResearchOrchestrator(empty_trace())
        orchestrator.begin_round("ROUND-FANOUT")
        orchestrator.accept_agent_proposal(
            role="planner",
            payload=proposal(
                spawn_requests=[
                    {"request_id": "S-1", "brief": "inspect A", "role": "explorer", "budget": 1},
                    {"request_id": "S-2", "brief": "inspect B", "role": "explorer", "budget": 2},
                    {
                        "request_id": "S-3",
                        "brief": "recursive child",
                        "role": "explorer",
                        "budget": 1,
                        "depth": MAX_SPAWN_DEPTH + 1,
                    },
                    {
                        "request_id": "S-4",
                        "brief": "unknown field",
                        "role": "explorer",
                        "budget": 1,
                        "unexpected": True,
                    },
                ],
            ),
        )

        records = orchestrator.spawn_log
        self.assertEqual(len(records), 4)
        self.assertEqual(
            [record.status for record in records],
            [
                SpawnDecisionStatus.APPROVED,
                SpawnDecisionStatus.APPROVED,
                SpawnDecisionStatus.REJECTED,
                SpawnDecisionStatus.REJECTED,
            ],
        )
        self.assertEqual([item.request_id for item in orchestrator.approved_spawn_descriptors], ["S-1", "S-2"])
        self.assertIsNotNone(records[0].descriptor)
        self.assertIn("no task or process execution", records[0].reason)
        with self.assertRaises(AttributeError):
            records[0].status = SpawnDecisionStatus.REJECTED  # type: ignore[misc]
        with self.assertRaises(AttributeError):
            orchestrator.spawn_log.append(records[0])  # type: ignore[attr-defined]

    def test_round_cap_rejects_each_excess_request_without_rejecting_the_batch(self) -> None:
        orchestrator = ResearchOrchestrator(empty_trace())
        orchestrator.begin_round("ROUND-CAP")
        requests = [
            {
                "request_id": f"S-{index}",
                "brief": "bounded work",
                "role": "explorer",
                "budget": 1,
            }
            for index in range(MAX_SPAWN_REQUESTS_PER_ROUND + 2)
        ]
        orchestrator.accept_agent_proposal(
            role="planner",
            payload=proposal(spawn_requests=requests),
        )
        records = orchestrator.spawn_log
        self.assertEqual(len(records), MAX_SPAWN_REQUESTS_PER_ROUND + 2)
        self.assertEqual(
            sum(record.status is SpawnDecisionStatus.APPROVED for record in records),
            MAX_SPAWN_REQUESTS_PER_ROUND,
        )
        self.assertTrue(all(record.descriptor is None for record in records[MAX_SPAWN_REQUESTS_PER_ROUND:]))

    def test_budget_cap_and_malformed_container_are_rejected(self) -> None:
        orchestrator = ResearchOrchestrator(empty_trace())
        orchestrator.begin_round("ROUND-BUDGET")
        orchestrator.accept_agent_proposal(
            role="planner",
            payload=proposal(
                spawn_requests=[
                    {
                        "request_id": "TOO-LARGE",
                        "brief": "too much",
                        "role": "explorer",
                        "budget": MAX_SPAWN_BUDGET_PER_REQUEST + 1,
                    }
                ]
            ),
        )
        self.assertEqual(orchestrator.spawn_log[0].status, SpawnDecisionStatus.REJECTED)
        self.assertEqual(orchestrator.approved_spawn_descriptors, ())

        orchestrator.accept_agent_proposal(
            role="planner",
            payload=proposal(spawn_requests={"brief": "not an array"}),
        )
        self.assertEqual(orchestrator.spawn_log[-1].status, SpawnDecisionStatus.REJECTED)

    def test_spawn_request_does_not_change_trace_or_promotion_policy(self) -> None:
        trace = empty_trace()
        before = trace.content_digest()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="planner",
            payload=proposal(
                spawn_requests=[
                    {"brief": "child", "role": "explorer", "budget": 1},
                ]
            ),
        )
        self.assertNotEqual(trace.content_digest(), before)
        self.assertEqual(len(orchestrator.approved_spawn_descriptors), 1)
        self.assertNotIn("Task", orchestrator.spawn_log[0].reason)

    def test_campaign_serializes_spawn_log_without_charging_requested_budget(self) -> None:
        budget = BudgetLedger()
        campaign = ResearchCampaign(
            empty_trace(),
            [
                StaticProposalWorker(
                    "planner",
                    proposal(
                        spawn_requests=[
                            {
                                "request_id": "S-CAMPAIGN",
                                "brief": "declarative child",
                                "role": "explorer",
                                "budget": 7,
                            }
                        ]
                    ),
                )
            ],
            budget=budget,
            max_rounds=1,
            max_rounds_without_gain=1,
        )
        report = campaign.run()
        self.assertEqual(report.to_dict()["spawn_log"][0]["status"], "APPROVED")
        self.assertEqual(report.rounds[0]["spawn_log"][0]["request_id"], "S-CAMPAIGN")
        self.assertEqual(budget.spent_input_tokens, 0)
        self.assertEqual(budget.spent_output_tokens, 0)
        self.assertEqual(budget.spent_cost_usd, 0.0)


if __name__ == "__main__":
    unittest.main()
