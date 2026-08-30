from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

try:
    from matharc.api import create_server
    from matharc.codex_agent import CodexSettings
    from matharc.demo import build_demo_run
    from matharc.store import save_run
    from tests.fake_codex import write_fake_codex
except ImportError as exc:  # pragma: no cover - v0.1 finalize overlay surface
    raise unittest.SkipTest(
        f"v0.1 Codex agent API surface is not present on this tree: {exc}"
    ) from exc


class AgentApiTests(unittest.TestCase):
    def test_real_http_sse_stream_and_dashboard_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = write_fake_codex(root)
            run_path = save_run(build_demo_run(), root / "run.json")
            settings = CodexSettings(
                executable=str(fake),
                workspace=str(root),
                timeout_seconds=5,
                persistent_sessions=True,
                max_concurrent=1,
                session_store=str(root / ".matharc" / "sessions.json"),
            )
            server = create_server(run_path, "127.0.0.1", 0, codex_settings=settings)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with urllib.request.urlopen(base + "/api/health", timeout=5) as response:
                    health = json.loads(response.read().decode("utf-8"))
                self.assertTrue(health["ok"])
                self.assertTrue(health["codex"]["available"])
                self.assertFalse(health["codex"]["acceptance_authority"])

                with urllib.request.urlopen(base + "/", timeout=5) as response:
                    dashboard = response.read().decode("utf-8")
                self.assertIn("发送给 Codex", dashboard)
                self.assertIn("/api/agent/stream", dashboard)
                self.assertIn("proposal-only", dashboard)
                self.assertIn("Claim / Obligation DAG", dashboard)

                payload = json.dumps(
                    {
                        "message": "Attack the selected claim and report the exact evidence boundary.",
                        "session_id": "web-session",
                        "role": "falsifier",
                        "mode": "attack",
                        "selected_claim_ids": ["C-STEP"],
                        "include_run_context": True,
                    }
                ).encode("utf-8")
                request = urllib.request.Request(
                    base + "/api/agent/stream",
                    data=payload,
                    headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=15) as response:
                    stream = response.read().decode("utf-8")
                self.assertIn("event: session", stream)
                self.assertIn("event: reasoning", stream)
                self.assertIn("event: plan", stream)
                self.assertIn("event: tool", stream)
                self.assertIn("event: final", stream)
                self.assertIn('"proposal_only":true', stream)
                self.assertIn("No mathematical promotion occurred", stream)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_invalid_agent_request_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = write_fake_codex(root)
            run_path = save_run(build_demo_run(), root / "run.json")
            server = create_server(
                run_path,
                "127.0.0.1",
                0,
                codex_settings=CodexSettings(
                    executable=str(fake),
                    workspace=str(root),
                    session_store=str(root / "sessions.json"),
                ),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_address[1]}/api/agent/chat",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(request, timeout=5)
                self.assertEqual(400, raised.exception.code)
                raised.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
