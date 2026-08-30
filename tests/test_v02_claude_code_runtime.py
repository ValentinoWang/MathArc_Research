from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from matharc.v02.claude_code_runtime import (
    ClaudeCodeConfig,
    ClaudeCodeRunner,
    ClaudeCodeRuntimeError,
    claude_code_status,
)
from matharc.v02.prompting import PROPOSAL_OUTPUT_SCHEMA, RESEARCH_RULES_MARKER, build_worker_prompt

from tests.fake_claude_code import write_fake_claude_code


class ClaudeCodeStatusTests(unittest.TestCase):
    def test_status_reports_unavailable_for_missing_executable(self) -> None:
        status = claude_code_status(ClaudeCodeConfig(executable="definitely-not-a-real-binary"))
        self.assertFalse(status["available"])
        self.assertFalse(status["acceptance_authority"])

    def test_status_reports_available_for_fake_executable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            status = claude_code_status(ClaudeCodeConfig(executable=str(fake)))
            self.assertTrue(status["available"])


class ClaudeCodeRunnerCommandTests(unittest.TestCase):
    def test_build_command_disallows_every_mutating_tool(self) -> None:
        runner = ClaudeCodeRunner(ClaudeCodeConfig(executable="claude"))
        command = runner.build_command(json_schema={"type": "object"})
        self.assertIn("--strict-mcp-config", command)
        self.assertIn("--disallowedTools", command)
        disallowed = command[command.index("--disallowedTools") + 1]
        for tool in ("Bash", "Write", "Edit", "WebFetch", "Task"):
            self.assertIn(tool, disallowed)
        self.assertIn("--json-schema", command)

    def test_build_command_rejects_unsafe_model_string(self) -> None:
        runner = ClaudeCodeRunner(ClaudeCodeConfig(executable="claude"))
        with self.assertRaises(ValueError):
            runner.build_command(json_schema={"type": "object"}, model="sonnet; rm -rf /")


class ClaudeCodeRunnerTurnTests(unittest.TestCase):
    def test_successful_turn_parses_structured_output_and_usage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
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
            with patch.dict(
                os.environ,
                {"FAKE_CLAUDE_STRUCTURED_OUTPUT": json.dumps(proposal)},
            ):
                runner = ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
                prompt = build_worker_prompt(role="prover", trace_view={}, user_message="advance C")
                result = runner.run_turn(prompt, role="prover", json_schema=PROPOSAL_OUTPUT_SCHEMA)
        self.assertEqual(result.structured_output, proposal)
        self.assertEqual(result.usage["input_tokens"], 100)
        self.assertEqual(result.session_id, "fake-session-0001")
        self.assertIsInstance(result.cost_usd, float)
        self.assertIn(RESEARCH_RULES_MARKER, prompt)

    def test_run_turn_injects_preamble_for_a_raw_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            log_path = Path(directory) / "log.jsonl"
            with patch.dict(os.environ, {"FAKE_CLAUDE_LOG": str(log_path)}):
                runner = ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
                runner.run_turn("just do it", role="falsifier", json_schema=PROPOSAL_OUTPUT_SCHEMA)
            self.assertTrue(log_path.exists())

    def test_nonzero_exit_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            with patch.dict(os.environ, {"FAKE_CLAUDE_EXIT_CODE": "3"}):
                runner = ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
                with self.assertRaises(ClaudeCodeRuntimeError):
                    runner.run_turn("prompt", role="prover", json_schema=PROPOSAL_OUTPUT_SCHEMA)

    def test_is_error_result_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            with patch.dict(os.environ, {"FAKE_CLAUDE_IS_ERROR": "1"}):
                runner = ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
                with self.assertRaises(ClaudeCodeRuntimeError):
                    runner.run_turn("prompt", role="prover", json_schema=PROPOSAL_OUTPUT_SCHEMA)

    def test_missing_structured_output_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            with patch.dict(os.environ, {"FAKE_CLAUDE_OMIT_STRUCTURED": "1"}):
                runner = ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
                with self.assertRaises(ClaudeCodeRuntimeError):
                    runner.run_turn("prompt", role="prover", json_schema=PROPOSAL_OUTPUT_SCHEMA)

    def test_missing_executable_raises(self) -> None:
        runner = ClaudeCodeRunner(ClaudeCodeConfig(executable="definitely-not-a-real-binary"))
        with self.assertRaises(ClaudeCodeRuntimeError):
            runner.run_turn("prompt", role="prover", json_schema=PROPOSAL_OUTPUT_SCHEMA)

    def test_unknown_role_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = write_fake_claude_code(directory)
            runner = ClaudeCodeRunner(ClaudeCodeConfig(executable=str(fake)))
            with self.assertRaises(ValueError):
                runner.run_turn("prompt", role="not-a-role", json_schema=PROPOSAL_OUTPUT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
