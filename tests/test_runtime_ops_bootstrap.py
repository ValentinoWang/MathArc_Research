from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from matharc.v02.runtime.ops import (
    RuntimeBootstrapError,
    bootstrap_from_env,
    cleanup_regenerable,
)


class RuntimeOpsBootstrapTests(unittest.TestCase):
    def _environment(self, root: Path, credential: Path) -> dict[str, str]:
        return {
            "MATHARC_RUNTIME_RUN_ID": "pilot-run-1",
            "MATHARC_RELEASE_ID": "release-1",
            "MATHARC_RUN_PATH": str(root / "runs" / "current.json"),
            "MATHARC_WORKSPACE": str(root / "workspace"),
            "MATHARC_STORE_PATH": str(root / "store"),
            "MATHARC_BACKUP_PATH": str(root / "backups"),
            "MATHARC_LOG_PATH": str(root / "logs" / "runtime.jsonl"),
            "MATHARC_SECRET_FILE": "%d/api-token",
            "CREDENTIALS_DIRECTORY": str(credential.parent),
        }

    def test_bootstrap_consumes_identity_store_and_credential(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credential = root / "credentials" / "api-token"
            credential.parent.mkdir()
            credential.write_text("opaque-token\n", encoding="utf-8")
            env = self._environment(root, credential)
            with patch.dict(os.environ, env, clear=False):
                runtime = bootstrap_from_env()
                reopened = bootstrap_from_env()
            self.assertEqual(runtime.runtime_run_id, "pilot-run-1")
            self.assertEqual(runtime.release_id, "release-1")
            self.assertEqual(reopened.store.state["runs"]["pilot-run-1"]["release_id"], "release-1")
            self.assertTrue(runtime.healthz()["ok"])
            self.assertFalse(runtime.readyz()["ok"])  # the configured run file is not seeded

    def test_systemd_entrypoint_is_bootstrapped(self) -> None:
        root = Path(__file__).resolve().parents[1]
        service = (root / "deploy/matharc-research.service").read_text(encoding="utf-8")
        env = (root / "deploy/matharc-research.env.example").read_text(encoding="utf-8")
        self.assertIn("-m matharc.v02.runtime.ops serve", service)
        self.assertIn("MATHARC_STORE_PATH=/var/lib/matharc-research/", env)

    def test_bootstrap_rejects_missing_external_credential(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = self._environment(root, root / "credentials" / "api-token")
            with patch.dict(os.environ, env, clear=False), self.assertRaises(RuntimeBootstrapError):
                bootstrap_from_env()

    def test_serve_uses_v02_workspace_server_and_persistent_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credential = root / "credentials" / "api-token"
            credential.parent.mkdir()
            credential.write_text("opaque-token\n", encoding="utf-8")
            env = self._environment(root, credential) | {
                "MATHARC_DASHBOARD_PATH": str(root / "workspace" / "dashboard.html"),
                "MATHARC_ACCESS_STORE_PATH": str(root / "access"),
                "MATHARC_ACCESS_COOKIE_SECURE": "true",
            }
            runtime = SimpleNamespace(
                workspace=root / "workspace",
                store_path=root / "store",
                readyz=lambda: {"ok": True},
            )
            server = SimpleNamespace(
                serve_forever=lambda **_: None,
                server_close=lambda: None,
            )
            captured: dict[str, object] = {}

            def fake_make_server(workspace, **kwargs):
                captured["workspace"] = workspace
                captured.update(kwargs)
                return server

            # Keep this test at the bootstrap boundary: no network socket is
            # opened, while the constructor contract is fully asserted.
            with patch.dict(os.environ, env, clear=False), \
                    patch("matharc.v02.runtime.ops.bootstrap_from_env", return_value=runtime), \
                    patch("matharc.v02.workspace_server.make_server", side_effect=fake_make_server):
                from matharc.v02.runtime.ops import _serve
                self.assertEqual(0, _serve(SimpleNamespace(host="127.0.0.1", port=0, run="", workspace="")))
            self.assertEqual(root / "workspace", captured["workspace"])
            self.assertEqual(root / "store", captured["runtime_store_path"])
            self.assertEqual(root / "access", captured["access_store_root"])
            self.assertTrue(captured["access_cookie_secure"])

    def test_cleanup_backs_up_before_allowlisted_removal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            root.mkdir()
            (root / "regenerable.cache").write_text("cache", encoding="utf-8")
            backup = Path(directory) / "backup-1"
            result = cleanup_regenerable(root, ["regenerable.cache"], backup_path=backup)
            self.assertFalse((root / "regenerable.cache").exists())
            self.assertTrue((backup / "events.jsonl").exists() is False)
            manifest = json.loads((backup / "backup-manifest.json").read_text(encoding="utf-8"))
            self.assertIn("regenerable.cache", manifest["files"])
            self.assertEqual(result["removed"], ["regenerable.cache"])

    def test_cleanup_rejects_protected_and_escape_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            root.mkdir()
            protected = root / "events.jsonl"
            protected.write_text("durable", encoding="utf-8")
            with self.assertRaises(RuntimeBootstrapError):
                cleanup_regenerable(root, ["events.jsonl"], backup_path=Path(directory) / "backup", protected=["events.jsonl"])
            disposable = root / "disposable.cache"
            disposable.write_text("cache", encoding="utf-8")
            with self.assertRaises(RuntimeBootstrapError):
                cleanup_regenerable(root, ["disposable.cache"], backup_path=Path(directory) / "backup-allowlist", allowlist=[])
            with self.assertRaises(RuntimeBootstrapError):
                cleanup_regenerable(root, ["../outside"], backup_path=Path(directory) / "backup-2")

    def test_backup_rejects_destination_inside_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            root.mkdir()
            (root / "events.jsonl").write_text("{}\n", encoding="utf-8")
            from matharc.v02.runtime.ops import backup_runtime_store
            with self.assertRaises(RuntimeBootstrapError):
                backup_runtime_store(root, root / "backup")


if __name__ == "__main__":
    unittest.main()
