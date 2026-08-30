from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
)
from matharc.v02.trace import ResearchTrace, load_trace
from matharc.v02.workers import StaticProposalWorker

_VALID_INDUCTION_CERTIFICATE = {
    "variable": "n",
    "base": {"at": 0, "lhs": "0", "rhs": "0*0"},
    "step": {"lhs": "(n*n) + (2*(n+1) - 1)", "rhs": "(n+1)*(n+1)"},
}


def fresh_odd_sum_trace() -> ResearchTrace:
    """A fresh (evidence-free) odd-sum trace the campaign has to close for itself.

    Mirrors the shape of matharc/v02/demo.py's odd-sum theorem, but starts
    empty of evidence -- unlike the demo, nothing here is hand-authored.
    """

    contract = TheoremContract(
        contract_id="CONTRACT-CAMPAIGN-TEST",
        problem="Prove that the sum of the first n positive odd integers equals n squared.",
        target_claim_ids=("C-TARGET",),
        scope="For every integer n >= 0.",
    )
    trace = ResearchTrace(run_id="CAMPAIGN-TEST", contract=contract)
    trace.add_claim(
        ClaimRecord("C-BASE", "The identity holds at n = 0.", "Single base case.", weight=1.0)
    )
    trace.add_claim(
        ClaimRecord(
            "C-STEP",
            "If the identity holds at n, then it holds at n + 1.",
            "Every natural number n.",
            dependencies=("C-BASE",),
            weight=2.0,
            critical=True,
        )
    )
    trace.add_claim(
        ClaimRecord(
            "C-TARGET",
            "For every n >= 0, 1 + 3 + ... + (2n - 1) = n^2.",
            "All natural numbers.",
            dependencies=("C-BASE", "C-STEP"),
            weight=4.0,
            critical=True,
        )
    )
    trace.add_route(
        ResearchRoute(
            route_id="R-INDUCTION",
            name="Induction with symbolic difference certificate",
            hypothesis="The formula follows from a checked base case and a polynomial induction step.",
            mechanism_signature=("mathematical induction", "symbolic polynomial normalization"),
            kill_test="Normalize (n^2 + 2n + 1) - (n+1)^2 and require exact zero.",
            status=RouteStatus.ACTIVE,
            claim_ids=("C-BASE", "C-STEP", "C-TARGET"),
        )
    )
    return trace


def induction_proposal() -> dict[str, object]:
    return {
        "status": "progress",
        "public_reasoning": {
            "objective": "advance the focus claim",
            "premises": [],
            "proposed_move": "run the induction certificate check",
            "observation": "a certificate is available",
            "falsification": "check the smallest boundary case",
            "decision": "attach exact evidence",
        },
        "tool_requests": [
            {
                "tool": "induction_certificate",
                "purpose": "check base+step for the odd-sum identity",
                "arguments": {"certificate": _VALID_INDUCTION_CERTIFICATE},
            }
        ],
        "claim_boundary": "the worker never self-promotes",
    }


class ResearchCampaignTests(unittest.TestCase):
    def test_campaign_promotes_a_real_base_case_but_withholds_a_critical_claim(self) -> None:
        trace = fresh_odd_sum_trace()
        worker = StaticProposalWorker("prover", induction_proposal())
        campaign = ResearchCampaign(trace, [worker], max_rounds=6, max_rounds_without_gain=2)
        report = campaign.run()

        # C-BASE is not critical and has no dependencies: one real exact-tool
        # pass through the campaign is enough for trace.promote_claim to
        # actually succeed -- no hand-authored evidence anywhere.
        self.assertEqual(trace.claims["C-BASE"].status, ClaimStatus.PROVED)

        # C-STEP is critical and needs two INDEPENDENT evidence groups; the
        # same tool run twice shares one independence_group by design, so the
        # gate must correctly keep refusing it -- this is the fail-closed
        # boundary working against a real automated loop, not a bug.
        self.assertNotEqual(trace.claims["C-STEP"].status, ClaimStatus.PROVED)

        self.assertEqual(report.stop_reason, "no_gain_rounds_exhausted")

        first_round = report.rounds[0]
        executed = first_round["workers"][0]["executed_tools"]
        self.assertEqual(executed[0]["status"], "EVIDENCE_ACCEPTED")
        self.assertTrue(executed[0]["promoted"])

        later_round = report.rounds[-1]
        later_executed = later_round["workers"][0]["executed_tools"]
        self.assertEqual(later_executed[0]["status"], "EVIDENCE_ACCEPTED")
        self.assertFalse(later_executed[0]["promoted"])

    def test_campaign_persists_the_trace_after_every_round(self) -> None:
        trace = fresh_odd_sum_trace()
        worker = StaticProposalWorker("prover", induction_proposal())
        with tempfile.TemporaryDirectory() as directory:
            persist_path = Path(directory) / "trace.json"
            campaign = ResearchCampaign(
                trace,
                [worker],
                max_rounds=2,
                max_rounds_without_gain=1,
                persist_path=persist_path,
            )
            campaign.run()
            self.assertTrue(persist_path.exists())
            reloaded = load_trace(persist_path)
        self.assertEqual(reloaded.claims["C-BASE"].status, ClaimStatus.PROVED)

    def test_campaign_stops_on_budget_exhaustion(self) -> None:
        trace = fresh_odd_sum_trace()
        worker = StaticProposalWorker("prover", induction_proposal())
        budget = BudgetLedger(wall_seconds_limit=0.0)
        campaign = ResearchCampaign(
            trace, [worker], budget=budget, max_rounds=10, max_rounds_without_gain=10
        )
        report = campaign.run()
        self.assertEqual(report.stop_reason, "budget_exhausted")
        self.assertEqual(len(report.rounds), 0)

    def test_worker_can_grow_the_claim_dag_through_a_campaign(self) -> None:
        trace = fresh_odd_sum_trace()
        proposal = {
            "status": "progress",
            "public_reasoning": {
                "objective": "decompose further",
                "premises": [],
                "proposed_move": "split the base case check into two smaller checks",
                "observation": "structure identified",
                "falsification": "check smallest instance",
                "decision": "propose a sub-claim",
            },
            "new_claims": [
                {
                    "claim_id": "C-BASE-AUX",
                    "statement": "an auxiliary lemma for the base case",
                    "scope": "narrower scope",
                    "dependencies": [],
                }
            ],
            "claim_boundary": "the worker never self-promotes",
        }
        worker = StaticProposalWorker("strategist", proposal)
        campaign = ResearchCampaign(trace, [worker], max_rounds=1, max_rounds_without_gain=5)
        campaign.run()
        self.assertIn("C-BASE-AUX", trace.claims)
        self.assertEqual(trace.claims["C-BASE-AUX"].status, ClaimStatus.PROPOSED)

    def test_duplicate_worker_roles_are_rejected(self) -> None:
        trace = fresh_odd_sum_trace()
        worker_a = StaticProposalWorker("prover", induction_proposal())
        worker_b = StaticProposalWorker("prover", induction_proposal())
        with self.assertRaises(ValueError):
            ResearchCampaign(trace, [worker_a, worker_b])

    def test_at_least_one_worker_is_required(self) -> None:
        trace = fresh_odd_sum_trace()
        with self.assertRaises(ValueError):
            ResearchCampaign(trace, [])


if __name__ == "__main__":
    unittest.main()
