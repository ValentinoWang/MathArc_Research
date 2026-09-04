from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from matharc.v02.access import InvitationAccessStore
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_server import make_server


class RuntimeHTTPIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.workspace = root / "workspace"
        write_full_workspace_bundle(self.workspace)
        self.dashboard = root / "console.html"
        self.dashboard.write_text("<!doctype html><title>runtime</title>", encoding="utf-8")
        self.access_root = root / "access"
        access = InvitationAccessStore(self.access_root)
        invitation = access.issue_invitation(email="runtime@example.com", topic_scopes=["runtime"])
        token, _ = access.redeem(email="runtime@example.com", code=invitation.code)
        self.cookie = f"matharc_access_session={token}"
        self.server = make_server(
            self.workspace,
            host="127.0.0.1",
            port=0,
            dashboard_path=self.dashboard,
            access_store_root=self.access_root,
            runtime_store_path=root / "runtime-store",
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, path: str, *, method: str = "GET", payload: dict | None = None, cookie: str | None = None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.base + path, method=method, data=body)
        if body is not None:
            request.add_header("Content-Type", "application/json")
        if cookie is not None:
            request.add_header("Cookie", cookie)
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def run_spec(self) -> dict:
        return {
            "workspace_id": "workspace-1",
            "trace_id": "trace-1",
            "runtime_run_id": "runtime-1",
            "task_id": "task-1",
            "contract_version": "1.0",
            "source_digest": "",
            "evaluator_digest": "",
            "tool_registry_digest": "",
            "seed": 1,
            "budget": {"max_seconds": 10},
            "workers": [],
            "status": "CREATED",
        }

    def test_snapshot_is_cookie_protected_and_contains_runtime_state(self) -> None:
        self.assertEqual(401, self.request("/api/runtime/snapshot")[0])
        status, payload = self.request("/api/runtime/snapshot", cookie=self.cookie)
        self.assertEqual(200, status)
        self.assertIn("payload", payload)
        self.assertIn("runtime", payload["payload"])
        self.assertGreaterEqual(payload["sequence"], 0)

    def test_run_action_is_persistent_idempotent_and_rejects_process_inputs(self) -> None:
        status, created = self.request("/api/runtime/runs", method="POST", payload=self.run_spec(), cookie=self.cookie)
        self.assertEqual(201, status)
        self.assertEqual("runtime-1", created["run"]["runtime_run_id"])
        action = {"action_id": "a-1", "action": "start"}
        status, first = self.request("/api/runtime/runs/runtime-1/actions", method="POST", payload=action, cookie=self.cookie)
        self.assertEqual(200, status)
        self.assertFalse(first["replayed"])
        status, replay = self.request("/api/runtime/runs/runtime-1/actions", method="POST", payload=action, cookie=self.cookie)
        self.assertEqual(200, status)
        self.assertTrue(replay["replayed"])
        self.assertEqual(first["receipt"], replay["receipt"])
        status, rejected = self.request("/api/runtime/runs/runtime-1/actions", method="POST", payload={**action, "action_id": "a-2", "payload": {"cwd": "/tmp"}}, cookie=self.cookie)
        self.assertEqual(400, status)
        self.assertEqual("invalid_runtime_action", rejected["error"])
        status, events = self.request("/api/runtime/events?after=-1", cookie=self.cookie)
        self.assertEqual(200, status)
        self.assertEqual(["RUN_CREATED", "RUN_ACTION"], [item["event_type"] for item in events["events"]])

    def test_existing_console_endpoint_remains_available(self) -> None:
        status, payload = self.request("/api/console", cookie=self.cookie)
        self.assertEqual(200, status)
        self.assertEqual("1.0", payload["schema_version"])


if __name__ == "__main__":
    unittest.main()
