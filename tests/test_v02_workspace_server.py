from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_server import make_server


class WorkspaceServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "workspace"
        write_full_workspace_bundle(self.root)
        self.server = make_server(
            self.root,
            host="127.0.0.1",
            port=0,
            dashboard_path=self.root / "workspace-dashboard.html",
            sse_poll_seconds=0.02,
            sse_lifetime_seconds=0.12,
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.02},
            daemon=True,
        )
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def get_json(self, path: str) -> dict[str, object]:
        with urlopen(self.base + path, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_health_workspace_events_and_artifacts(self) -> None:
        health = self.get_json("/api/health")
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["audit_errors"], 0)
        self.assertEqual(len(str(health["state_digest_sha256"])), 64)

        workspace = self.get_json("/api/workspace")
        self.assertTrue(workspace["audit"]["valid"])
        self.assertEqual(
            workspace["workspace"]["state_digest_sha256"],
            health["state_digest_sha256"],
        )

        events = self.get_json("/api/events?after=-1")
        self.assertGreaterEqual(len(events["events"]), 1)
        self.assertEqual(events["head_hash"], health["event_head_hash"])

        artifacts = self.get_json("/api/artifacts")
        self.assertFalse(artifacts["raw_download_enabled"])
        self.assertGreaterEqual(len(artifacts["records"]), 1)

    def test_dashboard_is_served_only_after_workspace_validation(self) -> None:
        with urlopen(self.base + "/", timeout=5) as response:
            body = response.read().decode("utf-8")
        self.assertIn("命题依赖图", body)
        self.assertIn("事件哈希链", body)
        self.assertIn("基准资格", body)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_post_is_rejected_and_does_not_mutate_workspace(self) -> None:
        before = self.get_json("/api/health")["state_digest_sha256"]
        request = Request(
            self.base + "/api/workspace",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as captured:
            urlopen(request, timeout=5)
        self.assertEqual(captured.exception.code, 405)
        payload = json.loads(captured.exception.read().decode("utf-8"))
        self.assertEqual(payload["error"], "read_only")
        after = self.get_json("/api/health")["state_digest_sha256"]
        self.assertEqual(before, after)

    def test_sse_stream_contains_hash_chained_research_events(self) -> None:
        with urlopen(self.base + "/events?after=-1", timeout=5) as response:
            body = response.read().decode("utf-8")
        self.assertIn("event: research_event", body)
        self.assertIn("event_hash", body)
        self.assertIn("previous_hash", body)
        self.assertIn("WORKSPACE_CREATED", body)

    def test_non_manifest_file_tampering_is_rejected_on_next_request(self) -> None:
        trace_path = self.root / "research-trace.json"
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        payload.setdefault("metadata", {})["tampered_after_server_start"] = True
        trace_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaises(HTTPError) as captured:
            urlopen(self.base + "/api/health", timeout=5)
        self.assertEqual(captured.exception.code, 409)
        error = json.loads(captured.exception.read().decode("utf-8"))
        self.assertIn("digest mismatch", error["message"])

        with self.assertRaises(HTTPError) as dashboard_error:
            urlopen(self.base + "/", timeout=5)
        self.assertEqual(dashboard_error.exception.code, 409)

    def test_unknown_paths_do_not_expose_workspace_files(self) -> None:
        for path in (
            "/research-trace.json",
            "/workspace.json",
            "/artifacts/manifest.json",
            "/../workspace.json",
        ):
            with self.assertRaises(HTTPError) as captured:
                urlopen(self.base + path, timeout=5)
            self.assertEqual(captured.exception.code, 404)

    def test_cli_refuses_remote_binding_without_explicit_override(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [
                sys.executable,
                "examples/serve_workspace_v02.py",
                "--workspace",
                str(self.root),
                "--host",
                "0.0.0.0",
                "--port",
                "0",
            ],
            cwd=project_root,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Refusing a non-loopback bind", completed.stderr)

    def test_cli_secure_cookie_flag_reaches_access_response(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        access_root = Path(self.temporary.name) / "access"
        process = subprocess.Popen(
            [
                sys.executable,
                "examples/serve_workspace_v02.py",
                "--workspace",
                str(self.root),
                "--host",
                "127.0.0.1",
                "--port",
                "0",
                "--dashboard",
                str(self.root / "workspace-dashboard.html"),
                "--access-store",
                str(access_root),
                "--access-cookie-secure",
                "--issue-preview-email",
                "researcher@example.edu",
            ],
            cwd=project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            assert process.stdout is not None
            startup_lines: list[str] = []
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                line = process.stdout.readline()
                if not line:
                    break
                startup_lines.append(line)
                if line.strip() == "}":
                    break
            startup = json.loads("".join(startup_lines))
            self.assertTrue(startup["access_cookie_secure"])
            request = Request(
                str(startup["url"]) + "api/access/redeem",
                data=json.dumps(
                    {
                        "email": "researcher@example.edu",
                        "code": startup["preview_invitation_code"],
                    }
                ).encode("utf-8"),
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("Secure", response.headers["Set-Cookie"])
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

    def test_cli_secure_cookie_flag_requires_access_store(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [
                sys.executable,
                "examples/serve_workspace_v02.py",
                "--workspace",
                str(self.root),
                "--access-cookie-secure",
            ],
            cwd=project_root,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "--access-cookie-secure requires --access-store", completed.stderr
        )


if __name__ == "__main__":
    unittest.main()
