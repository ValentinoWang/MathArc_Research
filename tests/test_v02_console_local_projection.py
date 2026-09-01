from __future__ import annotations

import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

from matharc.operations import Account, OperationsDomainStore
from matharc.v02.console_export import ConsoleLocalProjectionConfig, build_console_export
from matharc.v02.exploration_session import ExplorationSessionStore
from matharc.v02.operations_ledger import WorkspaceBoundOperationsLedger
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

    def test_operations_projection_requires_workspace_bound_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            write_full_workspace_bundle(workspace)
            operations_root = root / "operations"
            OperationsDomainStore(operations_root).create_account(Account("A", "unbound"))
            config = ConsoleLocalProjectionConfig(operations_domain_root=operations_root)
            with self.assertRaisesRegex(ValueError, "provenance"):
                build_console_export(workspace, local_projection_config=config)

    def test_operations_projection_is_bound_and_rejects_sibling_workspace_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            write_full_workspace_bundle(workspace_a)
            shutil.copytree(workspace_a, workspace_b)
            provenance = build_console_export(workspace_a)["provenance"]
            operations_root = root / "operations"
            ledger = WorkspaceBoundOperationsLedger(
                operations_root,
                {**provenance, "workspace_root": str(workspace_a.resolve())},
            )
            ledger.create_account(Account("A", "bound"))
            config = ConsoleLocalProjectionConfig(operations_domain_root=operations_root)
            before = (operations_root / "operations-domain.json").read_bytes()
            projected = build_console_export(workspace_a, local_projection_config=config)
            self.assertEqual(before, (operations_root / "operations-domain.json").read_bytes())
            self.assertEqual(projected["local_console"]["operations"]["state"], "live")
            self.assertEqual(
                projected["local_console"]["operations"]["provenance"], provenance
            )
            with self.assertRaisesRegex(ValueError, "another workspace"):
                build_console_export(workspace_b, local_projection_config=config)


if __name__ == "__main__": unittest.main()
