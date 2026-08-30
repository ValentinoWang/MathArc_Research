import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from matharc.agent_service import AgentRequestError, CodexAgentService
from matharc.codex_runtime import CodexConfig, CodexRunner, parse_jsonl_event
from matharc.demo import build_demo_run


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
last = pathlib.Path(args[args.index("--output-last-message") + 1])
prompt = sys.stdin.read()
print(json.dumps({"type": "thread.started", "thread_id": "thread-test-001"}), flush=True)
print(json.dumps({"type": "turn.started"}), flush=True)
print(json.dumps({
    "type": "item.completed",
    "item": {"id": "r1", "type": "reasoning", "text": "Check scope before proof search."}
}), flush=True)
print(json.dumps({
    "type": "item.completed",
    "item": {
        "id": "c1", "type": "command_execution", "command": "python verifier.py",
        "aggregated_output": "PASS", "exit_code": 0, "status": "completed"
    }
}), flush=True)
print(json.dumps({
    "type": "item.completed",
    "item": {"id": "m1", "type": "agent_message", "text": "Structured result is ready."}
}), flush=True)
print(json.dumps({
    "type": "turn.completed",
    "usage": {"input_tokens": 50, "cached_input_tokens": 0, "cache_write_input_tokens": 0,
              "output_tokens": 20, "reasoning_output_tokens": 5}
}), flush=True)
result = {
    "status": "progress",
    "executive_summary": "One verifier-ready obligation was isolated.",
    "public_reasoning": {
        "objective": "Close one atomic claim", "premises": ["Frozen scope"],
        "proposed_move": "Replay an exact checker", "observation": "No promotion yet",
        "falsification": "Search a boundary counterexample", "decision": "Keep open"
    },
    "claim_updates": [{
        "claim_id": "C-NEW", "action": "propose", "statement": "Atomic candidate",
        "scope": "GLOBAL", "evidence_needed": ["independent replay"]
    }],
    "tool_requests": [{
        "tool": "python", "purpose": "replay", "command": "python verifier.py",
        "expected_discriminator": "PASS or counterexample"
    }],
    "risks": ["checker independence"],
    "next_actions": ["write a second implementation"],
    "claim_boundary": "This is a proposal, not a verified theorem."
}
last.write_text(json.dumps(result), encoding="utf-8")
assert "NON-NEGOTIABLE RESEARCH RULES" in prompt
'''


class CodexEventTests(unittest.TestCase):
    def test_jsonl_event_normalization(self) -> None:
        event = parse_jsonl_event(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "python check.py",
                        "aggregated_output": "PASS",
                        "exit_code": 0,
                        "status": "completed",
                    },
                }
            ),
            3,
        )
        self.assertEqual("command_execution", event.payload["item_type"])
        self.assertEqual("python check.py", event.payload["command"])
        self.assertEqual(0, event.payload["exit_code"])


class CodexRunnerTests(unittest.TestCase):
    def _fake(self, directory: str) -> Path:
        path = Path(directory) / "fake-codex"
        path.write_text(FAKE_CODEX, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
        return path

    def test_codex_cli_stream_and_structured_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = self._fake(directory)
            runner = CodexRunner(
                CodexConfig(
                    executable=str(executable),
                    workspace=Path(directory),
                    timeout_seconds=20,
                )
            )
            events = list(runner.stream_turn("prompt", role="falsifier"))
            self.assertEqual("thread.started", events[0].type)
            self.assertIn("command_execution", [e.payload.get("item_type") for e in events])
            result = events[-1].payload["result"]
            self.assertEqual("thread-test-001", result["thread_id"])
            self.assertEqual("progress", result["final_response"]["status"])
            self.assertEqual(50, result["usage"]["input_tokens"])
            self.assertIn("--output-schema", result["command"])
            self.assertIn("read-only", result["command"])

    def test_agent_service_persists_proposal_without_promoting_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = self._fake(directory)
            run = build_demo_run()
            release_before = run.release_state
            service = CodexAgentService(
                run,
                config=CodexConfig(
                    executable=str(executable),
                    workspace=Path(directory),
                    timeout_seconds=20,
                ),
                session_root=Path(directory) / "sessions",
            )
            response = service.run(
                {
                    "role": "verifier",
                    "message": "Audit the current proof contract.",
                    "sandbox": "read-only",
                }
            )
            self.assertEqual(release_before, run.release_state)
            self.assertEqual("progress", response["result"]["final_response"]["status"])
            self.assertEqual(run.run_id, response["result"]["run_id"])
            self.assertTrue(response["result"]["result_sha256"])
            self.assertEqual(1, len(service.list_sessions()))

    def test_request_rejects_unsafe_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = build_demo_run()
            service = CodexAgentService(
                run,
                config=CodexConfig(executable="missing-codex", workspace=Path(directory)),
                session_root=Path(directory) / "sessions",
            )
            with self.assertRaises(AgentRequestError):
                service.validate_request(
                    {"role": "prover", "message": "x", "sandbox": "danger-full-access"}
                )


if __name__ == "__main__":
    unittest.main()
