from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from matharc.codex_agent import AgentRequest, CodexAgentService, CodexSettings
    from matharc.demo import build_demo_run
    from tests.fake_codex import write_fake_codex
except ImportError as exc:  # pragma: no cover - v0.1 finalize overlay surface
    raise unittest.SkipTest(
        f"v0.1 Codex agent service surface is not present on this tree: {exc}"
    ) from exc


class CodexAgentServiceTests(unittest.TestCase):
    def settings(self, root: Path, executable: Path, *, timeout: int = 5) -> CodexSettings:
        return CodexSettings(
            executable=str(executable),
            workspace=str(root),
            timeout_seconds=timeout,
            persistent_sessions=True,
            max_concurrent=1,
            session_store=str(root / ".matharc" / "sessions.json"),
        )

    def test_stream_normalizes_events_and_persists_resume_thread(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = write_fake_codex(root)
            log = root / "argv.jsonl"
            settings = self.settings(root, fake)
            request = AgentRequest(
                message="Attack the selected bridge and design an exact replay.",
                session_id="session-test",
                role="falsifier",
                mode="attack",
                selected_claim_ids=["C-STEP"],
            )
            with patch.dict(os.environ, {"FAKE_CODEX_LOG": str(log)}, clear=False):
                first = CodexAgentService(settings).collect(request, build_demo_run())
                second = CodexAgentService(settings).collect(
                    AgentRequest(
                        message="Continue from the previous exact frontier.",
                        session_id="session-test",
                        role="verifier",
                        mode="verify",
                        selected_claim_ids=["C-STEP"],
                    ),
                    build_demo_run(),
                )

            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            event_names = {event["event"] for event in first["events"]}
            self.assertTrue(
                {"session", "status", "reasoning", "plan", "tool", "message", "usage", "final"}
                <= event_names
            )
            final = first["final"]
            self.assertTrue(final["proposal_only"])
            self.assertEqual("No mathematical promotion occurred.", final["result"]["claim_boundary"])
            self.assertFalse(CodexAgentService(settings).capabilities()["acceptance_authority"])

            stored = json.loads(Path(settings.session_store).read_text(encoding="utf-8"))
            self.assertEqual("thread-fake-001", stored["session-test"]["thread_id"])
            invocations = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertGreaterEqual(len(invocations), 2)
            self.assertTrue(
                any(
                    "resume" in invocation and "thread-fake-001" in invocation
                    for invocation in invocations[1:]
                )
            )

    def test_timeout_fails_closed_without_final_answer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = write_fake_codex(root)
            service = CodexAgentService(self.settings(root, fake, timeout=1))
            with patch.dict(os.environ, {"FAKE_CODEX_SLEEP": "2"}, clear=False):
                events = list(
                    service.stream(
                        AgentRequest(
                            message="This turn should time out.",
                            session_id="timeout-session",
                        ),
                        build_demo_run(),
                    )
                )
            self.assertFalse(any(event.get("event") == "final" for event in events))
            errors = [event for event in events if event.get("event") == "error"]
            self.assertTrue(errors)
            self.assertIn("timed out", errors[-1]["message"].lower())

    def test_capability_probe_reports_official_surface_without_acceptance_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = write_fake_codex(root)
            capability = CodexAgentService(self.settings(root, fake)).capabilities()
            self.assertTrue(capability["available"])
            self.assertIn("codex-cli", capability["version"])
            self.assertEqual("read-only", capability["sandbox"])
            self.assertFalse(capability["acceptance_authority"])
            self.assertIn("prover", capability["roles"])
            self.assertIn("verify", capability["modes"])


if __name__ == "__main__":
    unittest.main()
