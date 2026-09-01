from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

from matharc.v02 import cli
from matharc.v02.schema import ClaimRecord, TheoremContract
from matharc.v02.trace import ResearchTrace, load_trace
from matharc.v02.workers import StaticProposalWorker
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_server import make_server


class WorkspaceCampaignCheckpointTests(unittest.TestCase):
    def test_workspace_round_checkpoint_is_visible_to_sse_before_campaign_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            persisted_trace = Path(directory) / "persisted-trace.json"
            output = Path(directory) / "run-report.json"
            trace = ResearchTrace(
                run_id="WORKSPACE-CHECKPOINT",
                contract=TheoremContract(
                    contract_id="CONTRACT-WORKSPACE-CHECKPOINT",
                    problem="A bounded checkpoint fixture.",
                    target_claim_ids=("C",),
                    scope="Fixture only.",
                ),
            )
            trace.add_claim(ClaimRecord("C", "A fixture claim.", "Fixture only."))
            workspace = ResearchWorkspace(root, trace, strict_artifacts=False)
            workspace.save()

            server = make_server(
                root,
                host="127.0.0.1",
                port=0,
                sse_poll_seconds=0.01,
                sse_lifetime_seconds=0.12,
            )
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            second_round_started = threading.Event()
            release_second_round = threading.Event()
            failures: list[BaseException] = []

            class BarrierWorker:
                def __init__(self, role: str, *, runner: object) -> None:
                    self.role = role
                    self._worker = StaticProposalWorker(role, {})
                    self._call_count = 0

                def execute(self, plan: object, trace_view: object) -> object:
                    self._call_count += 1
                    if self._call_count == 2:
                        second_round_started.set()
                        if not release_second_round.wait(timeout=5):
                            raise TimeoutError("test did not release the second campaign round")
                    return self._worker.execute(plan, trace_view)

            def run_cli() -> None:
                try:
                    cli.main(
                        [
                            "run",
                            "--workspace-root",
                            str(root),
                            "--role",
                            "prover",
                            "--rounds",
                            "2",
                            "--max-rounds-without-gain",
                            "3",
                            "--persist",
                            str(persisted_trace),
                            "--output",
                            str(output),
                        ]
                    )
                except BaseException as exc:  # pragma: no cover - asserted below
                    failures.append(exc)

            campaign_thread = threading.Thread(target=run_cli, daemon=True)
            try:
                with patch.object(cli, "LLMProposalWorker", BarrierWorker):
                    campaign_thread.start()
                    self.assertTrue(second_round_started.wait(timeout=5))
                    self.assertTrue(persisted_trace.is_file())
                    persisted = load_trace(persisted_trace)
                    self.assertIn("C", persisted.claims)
                    self.assertEqual(len(persisted.tool_calls), 1)

                    with urlopen(base + "/events?after=-1", timeout=5) as response:
                        sse = response.read().decode("utf-8")
                    self.assertIn("CAMPAIGN_ROUND_COMPLETED", sse)
                    self.assertNotIn("CAMPAIGN_RECORDED", sse)

                    checkpointed = ResearchWorkspace.load(root)
                    checkpoint_events = [
                        event
                        for event in checkpointed.events.events
                        if event.event_type == "CAMPAIGN_ROUND_COMPLETED"
                    ]
                    self.assertEqual(len(checkpoint_events), 1)
                    self.assertEqual(checkpoint_events[0].payload["details"]["round_index"], 1)
                    self.assertEqual(len(checkpoint_events[0].payload["details"]["round_digest_sha256"]), 64)
            finally:
                release_second_round.set()
                campaign_thread.join(timeout=5)
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=2)

            self.assertFalse(campaign_thread.is_alive())
            self.assertEqual(failures, [])
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(report["report"]["rounds"]), 2)
            completed = ResearchWorkspace.load(root)
            self.assertEqual(completed.events.events[-1].event_type, "CAMPAIGN_RECORDED")


if __name__ == "__main__":
    unittest.main()
