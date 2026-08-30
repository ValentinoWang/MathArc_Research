from __future__ import annotations

import unittest

from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.schema import ClaimRecord, ClaimStatus, TheoremContract
from matharc.v02.trace import ResearchTrace
from matharc.v02.workers import StaticProposalWorker


def _trace() -> ResearchTrace:
    trace = ResearchTrace(
        "V03-GAIN",
        TheoremContract("K", "Prove C.", ("C",), "all n"),
    )
    trace.add_claim(
        ClaimRecord(
            "C",
            "n + 1 = 1 + n",
            "all integers n",
            critical=True,
            boundary="integers only",
        )
    )
    return trace


def _proposal() -> dict[str, object]:
    return {
        "status": "progress",
        "public_reasoning": {
            "objective": "try the exact identity checker",
            "premises": [],
            "proposed_move": "normalize both sides",
            "observation": "the same certificate will be replayed each round",
            "falsification": "non-zero difference would reject the identity",
            "decision": "attach exact evidence without self-promotion",
        },
        "tool_requests": [
            {
                "tool": "polynomial_identity",
                "purpose": "exactly compare the two sides",
                "arguments": {"lhs": "n+1", "rhs": "1+n", "variable": "n"},
            }
        ],
        "claim_boundary": "critical claim still needs a second independent group",
    }


class EvidenceGainTests(unittest.TestCase):
    def test_duplicate_semantic_certificate_is_zero_gain(self) -> None:
        trace = _trace()
        budget = BudgetLedger(wall_seconds_limit=60.0)
        report = ResearchCampaign(
            trace,
            [StaticProposalWorker("prover", _proposal())],
            budget=budget,
            max_rounds=5,
            max_rounds_without_gain=1,
        ).run()
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)
        self.assertEqual(report.stop_reason, "no_gain_rounds_exhausted")
        self.assertEqual(len(report.rounds), 2)
        first = report.rounds[0]["evidence_gain"]
        second = report.rounds[1]["evidence_gain"]
        self.assertTrue(first["has_gain"])
        self.assertGreaterEqual(first["certificate_maturity"], 1)
        self.assertFalse(second["has_gain"])
        self.assertEqual(second["certificate_maturity"], 0)
        self.assertEqual(second["new_positive_evidence"], 0)
        self.assertGreater(report.rounds[0]["cost_delta"]["tool_calls"], 0)


if __name__ == "__main__":
    unittest.main()
