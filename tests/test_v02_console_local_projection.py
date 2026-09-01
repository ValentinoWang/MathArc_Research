from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

from matharc.v02.console_export import ConsoleLocalProjectionConfig, build_console_export
from matharc.v02.exploration_session import ExplorationSessionStore
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_server import make_server


class ConsoleLocalProjectionTests(unittest.TestCase):
    def test_default_is_explicitly_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"; write_full_workspace_bundle(workspace)
            local = build_console_export(workspace)["local_console"]
            self.assertEqual({item["state"] for item in local.values()}, {"not_configured"})

    def test_explicit_local_records_are_exported_and_served_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); workspace = root / "workspace"; write_full_workspace_bundle(workspace)
            sessions = root / "sessions"; store = ExplorationSessionStore(sessions)
            provenance = build_console_export(workspace)["provenance"]
            store.create("S-1", provenance)
            config = ConsoleLocalProjectionConfig(workspace_index_root=root, exploration_session_root=sessions)
            payload = build_console_export(workspace, local_projection_config=config)
            self.assertEqual(payload["local_console"]["workspace_index"]["state"], "live")
            self.assertEqual(payload["local_console"]["exploration_sessions"]["sessions"][0]["session_id"], "S-1")
            dashboard = root / "console.html"; dashboard.write_text("<!doctype html><title>console</title>", encoding="utf-8")
            server = make_server(workspace, host="127.0.0.1", port=0, dashboard_path=dashboard, local_projection_config=config)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/console") as response:
                    served = json.loads(response.read().decode("utf-8"))
                self.assertEqual(served["local_console"]["exploration_sessions"]["state"], "live")
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=2)

    def test_mismatched_session_is_stale_and_index_hides_host_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); workspace = root / "workspace"; write_full_workspace_bundle(workspace)
            sessions = root / "sessions"; store = ExplorationSessionStore(sessions)
            store.create(
                "S-other",
                {"run_id": "OTHER-RUN", "state_digest_sha256": "a" * 64, "event_head_hash": "b" * 64},
            )
            invalid = root / "invalid"; invalid.mkdir()
            (invalid / "workspace.json").write_text("{not json", encoding="utf-8")
            payload = build_console_export(
                workspace,
                local_projection_config=ConsoleLocalProjectionConfig(
                    workspace_index_root=root, exploration_session_root=sessions
                ),
            )
            local = payload["local_console"]
            self.assertEqual(local["exploration_sessions"]["state"], "live_with_stale_records")
            self.assertEqual(local["exploration_sessions"]["sessions"], [])
            self.assertEqual(
                local["exploration_sessions"]["stale_sessions"],
                [{"session_id": "S-other", "reason": "workspace_provenance_mismatch"}],
            )
            rendered = json.dumps(local, sort_keys=True)
            self.assertNotIn(str(root.resolve()), rendered)
            self.assertNotIn(str(invalid.resolve()), rendered)
            self.assertEqual(local["workspace_index"]["invalid_candidates"], [{"reason": "invalid_workspace"}])


if __name__ == "__main__": unittest.main()
