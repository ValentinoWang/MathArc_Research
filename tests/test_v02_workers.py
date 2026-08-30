from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from matharc.v02.schema import ClaimRecord, ClaimStatus, ResearchRoute, RouteStatus, TheoremContract
from matharc.v02.session import ResearchSession
from matharc.v02.trace import ResearchTrace
from matharc.v02.workers import StaticProposalWorker, SubprocessProposalWorker


def trace_for_worker() -> ResearchTrace:
    trace = ResearchTrace(
        "WORKER-TEST",
        TheoremContract("K", "prove C", ("C",), "test scope"),
    )
    trace.add_claim(ClaimRecord("C", "candidate statement", "test scope", critical=True))
    trace.add_route(
        ResearchRoute(
            "R",
            "test route",
            "try a direct derivation",
            ("direct derivation",),
            "search the smallest counterexample",
            RouteStatus.ACTIVE,
            ("C",),
        )
    )
    return trace


def proposal() -> dict[str, object]:
    return {
        "public_reasoning": {
            "objective": "advance C",
            "premises": [],
            "proposed_move": "derive one atomic identity",
            "observation": "candidate identity produced",
            "falsification": "check the smallest boundary case",
            "decision": "record as candidate only",
        },
        "claim_updates": [{"claim_id": "C", "action": "propose"}],
        "linked_route_ids": ["R"],
    }


class WorkerSessionTests(unittest.TestCase):
    def test_static_worker_records_tool_and_candidate_not_proof(self) -> None:
        trace = trace_for_worker()
        session = ResearchSession(trace, [StaticProposalWorker("prover", proposal())])
        result = session.run_round()
        self.assertEqual(len(trace.tool_calls), 1)
        self.assertEqual(len(trace.public_reasoning), 1)
        self.assertEqual(trace.claims["C"].status, ClaimStatus.CANDIDATE)
        self.assertNotEqual(trace.claims["C"].status, ClaimStatus.PROVED)
        self.assertTrue(result.workers[0].proposal_recorded)

    def test_subprocess_worker_uses_json_contract(self) -> None:
        trace = trace_for_worker()
        code = (
            "import json,sys; request=json.load(sys.stdin); "
            f"print(json.dumps({json.dumps(proposal())}))"
        )
        with tempfile.TemporaryDirectory() as directory:
            worker = SubprocessProposalWorker(
                role="falsifier",
                command=(sys.executable, "-c", code),
                cwd=Path(directory),
                timeout_seconds=10,
            )
            result = ResearchSession(trace, [worker]).run_round()
        self.assertEqual(result.workers[0].status, "PASS")
        self.assertTrue(result.workers[0].proposal_recorded)
        self.assertEqual(trace.claims["C"].status, ClaimStatus.CANDIDATE)

    def test_invalid_subprocess_json_is_a_tool_error(self) -> None:
        trace = trace_for_worker()
        with tempfile.TemporaryDirectory() as directory:
            worker = SubprocessProposalWorker(
                role="verifier",
                command=(sys.executable, "-c", "print('not-json')"),
                cwd=Path(directory),
                timeout_seconds=10,
            )
            result = ResearchSession(trace, [worker]).run_round()
        self.assertEqual(result.workers[0].status, "ERROR")
        self.assertFalse(result.workers[0].proposal_recorded)
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)


if __name__ == "__main__":
    unittest.main()
