from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from matharc.v02.claude_code_runtime import ClaudeCodeConfig, ClaudeCodeRunner
from matharc.v02.model_workers import LLMProposalWorker, load_model_routing
from matharc.v02.orchestrator import ResearchOrchestrator
from matharc.v02.schema import ClaimRecord, ResearchRoute, RouteStatus, TheoremContract, ToolStatus
from matharc.v02.trace import ResearchTrace

from tests.fake_claude_code import write_fake_claude_code


def trace_for_worker() -> ResearchTrace:
    trace = ResearchTrace("MODEL-WORKER-TEST", TheoremContract("K", "prove C", ("C",), "test scope"))
    trace.add_claim(ClaimRecord("C", "candidate statement", "test scope"))
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


class LLMProposalWorkerTests(unittest.TestCase):
    def test_successful_turn_becomes_a_recordable_proposal(self) -> None:
        trace = trace_for_worker()
        orchestrator = ResearchOrchestrator(trace)
        plan = orchestrator.plan_round()
        proposal = {
            "status": "progress",
            "public_reasoning": {
                "objective": "advance",
                "premises": [],
                "proposed_move": "move",
                "observation": "obs",
                "falsification": "test",
                "decision": "candidate",
            },
            "claim_boundary": "no promotion",
        }
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            with patch.dict(os.environ, {"FAKE_CLAUDE_STRUCTURED_OUTPUT": json.dumps(proposal)}):
                runner = ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
                worker = LLMProposalWorker("prover", runner=runner)
                execution = worker.execute(plan, {"focus_claim": trace.claims["C"].to_dict()})
        self.assertEqual(execution.tool_call.status, ToolStatus.PASS)
        self.assertIsNotNone(execution.proposal)
        self.assertEqual(execution.proposal["status"], "progress")
        self.assertIsNotNone(execution.model_usage)
        self.assertEqual(execution.model_usage["input_tokens"], 100)
        orchestrator.accept_agent_proposal(role="prover", payload=execution.proposal)
        self.assertEqual(len(trace.public_reasoning), 1)

    def test_runtime_failure_never_raises_and_records_error_status(self) -> None:
        trace = trace_for_worker()
        orchestrator = ResearchOrchestrator(trace)
        plan = orchestrator.plan_round()
        worker = LLMProposalWorker(
            "falsifier",
            runner=ClaudeCodeRunner(ClaudeCodeConfig(executable="definitely-not-a-real-binary")),
        )
        execution = worker.execute(plan, {})
        self.assertEqual(execution.tool_call.status, ToolStatus.ERROR)
        self.assertIsNone(execution.proposal)
        self.assertTrue(execution.raw_stderr)

    def test_unknown_role_never_raises(self) -> None:
        trace = trace_for_worker()
        orchestrator = ResearchOrchestrator(trace)
        plan = orchestrator.plan_round()
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            worker = LLMProposalWorker(
                "not-a-role", runner=ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
            )
            execution = worker.execute(plan, {})
        self.assertEqual(execution.tool_call.status, ToolStatus.ERROR)
        self.assertIsNone(execution.proposal)


class ModelRoutingTests(unittest.TestCase):
    def test_load_model_routing_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/routing.json"
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "prover": {"provider": "claude-code", "model": "claude-opus-5"},
                        "falsifier": {"provider": "claude-code"},
                    },
                    handle,
                )
            routing = load_model_routing(path)
        self.assertEqual(routing["prover"].provider, "claude-code")
        self.assertEqual(routing["prover"].model, "claude-opus-5")
        self.assertIsNone(routing["falsifier"].model)

    def test_load_model_routing_requires_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/routing.json"
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"prover": {"model": "x"}}, handle)
            with self.assertRaises(ValueError):
                load_model_routing(path)


if __name__ == "__main__":
    unittest.main()
