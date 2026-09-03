from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matharc.v02.access import InvitationAccessStore
from matharc.v02.access_server import ACCESS_COOKIE_NAME
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_server import make_server
from tests.test_v02_console_observatory import _REVIEW_TOKEN, write_review_trace


class ResearchPreviewAccessServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.access_root = self.root / "access"
        write_full_workspace_bundle(self.workspace)
        self.dashboard = self.root / "console.html"
        self.dashboard.write_text("<!doctype html><title>Access fixture</title>", encoding="utf-8")
        self.store = InvitationAccessStore(self.access_root)
        self.invitation = self.store.issue_invitation(
            email="researcher@example.edu",
            topic_scopes=("ramsey-numbers", "erdos-szekeres"),
        )
        self.review_trace = self.root / "review-trace.json"
        write_review_trace(self.review_trace)
        self.server = make_server(
            self.workspace,
            host="127.0.0.1",
            port=0,
            dashboard_path=self.dashboard,
            access_store_root=self.access_root,
            review_trace_path=self.review_trace,
            review_write_token=_REVIEW_TOKEN,
            sse_lifetime_seconds=0.05,
            sse_poll_seconds=0.01,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, object | None, object]:
        request_headers = dict(headers or {})
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        request = Request(
            self.base + path,
            data=body,
            method=method,
            headers=request_headers,
        )
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as exc:
            response = exc
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
        decoded = (
            json.loads(raw.decode("utf-8"))
            if raw and content_type.startswith("application/json")
            else raw.decode("utf-8") if raw else None
        )
        return response.status, decoded, response.headers

    def redeem(self) -> tuple[str, dict[str, object]]:
        status, payload, headers = self.request(
            "/api/access/redeem",
            method="POST",
            payload={"email": "researcher@example.edu", "code": self.invitation.code},
        )
        self.assertEqual(200, status)
        assert isinstance(payload, dict)
        cookie = headers.get("Set-Cookie")
        self.assertIsNotNone(cookie)
        return str(cookie).split(";", 1)[0], payload

    def test_public_entry_and_health_do_not_expose_protected_projections(self) -> None:
        for path in ("/", "/api/health"):
            with self.subTest(path=path):
                status, _, _ = self.request(path)
                self.assertEqual(200, status)
        for path in (
            "/api/workspace",
            "/api/campaign",
            "/api/console",
            "/api/audit",
            "/api/events",
            "/api/artifacts",
            "/events",
            "/api/review-queue",
            "/api/review-bundle/C",
        ):
            with self.subTest(path=path):
                status, payload, _ = self.request(path)
                self.assertEqual(401, status)
                self.assertEqual("access_required", payload["error"])

    def test_application_is_pending_public_and_strict(self) -> None:
        application = {
            "email": "Applicant@Example.edu",
            "institution": "Example University",
            "research_role": "Researcher",
            "research_direction": "Combinatorics",
            "purpose": "Evaluate the governed preview.",
        }
        status, payload, headers = self.request(
            "/api/access/applications",
            method="POST",
            payload=application,
        )
        self.assertEqual(202, status)
        self.assertEqual(
            {"application_id", "status", "email", "submitted_at"},
            set(payload["application"]),
        )
        self.assertEqual("PENDING", payload["application"]["status"])
        self.assertEqual("applicant@example.edu", payload["application"]["email"])
        self.assertIsNone(headers.get("Set-Cookie"))

        before = (self.access_root / "access-state.json").read_bytes()
        status, payload, _ = self.request(
            "/api/access/applications",
            method="POST",
            payload={**application, "unexpected": True},
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", payload["error"])
        self.assertEqual(before, (self.access_root / "access-state.json").read_bytes())

    def test_redeem_session_logout_and_secret_storage_boundary(self) -> None:
        status, payload, headers = self.request(
            "/api/access/redeem",
            method="POST",
            payload={"email": "wrong@example.edu", "code": self.invitation.code},
        )
        self.assertEqual(401, status)
        self.assertEqual("invalid_credentials", payload["error"])
        self.assertIsNone(headers.get("Set-Cookie"))

        cookie, payload = self.redeem()
        self.assertTrue(payload["authenticated"])
        self.assertEqual("researcher@example.edu", payload["session"]["email"])
        issued_cookie = self.request(
            "/api/access/redeem",
            method="POST",
            payload={"email": "researcher@example.edu", "code": self.invitation.code},
        )
        self.assertEqual(401, issued_cookie[0])

        state = (self.access_root / "access-state.json").read_text(encoding="utf-8")
        self.assertNotIn(self.invitation.code, state)
        self.assertNotIn(cookie.split("=", 1)[1], state)
        self.assertIn("code_hash_sha256", state)
        self.assertIn("token_hash_sha256", state)

        status, console, _ = self.request("/api/console", headers={"Cookie": cookie})
        self.assertEqual(200, status)
        self.assertEqual("1.0", console["schema_version"])
        status, session, _ = self.request("/api/access/session", headers={"Cookie": cookie})
        self.assertEqual(200, status)
        self.assertTrue(session["authenticated"])

        status, _, logout_headers = self.request(
            "/api/access/logout",
            method="POST",
            headers={"Cookie": cookie, "Content-Length": "0"},
        )
        self.assertEqual(204, status)
        expired = logout_headers.get("Set-Cookie")
        self.assertIn(f"{ACCESS_COOKIE_NAME}=", expired)
        self.assertIn("Max-Age=0", expired)
        self.assertEqual(401, self.request("/api/console", headers={"Cookie": cookie})[0])
        self.assertEqual(204, self.request("/api/access/logout", method="POST")[0])

    def test_cookie_attributes_and_review_double_gate(self) -> None:
        status, _, headers = self.request(
            "/api/access/redeem",
            method="POST",
            payload={"email": "researcher@example.edu", "code": self.invitation.code},
        )
        self.assertEqual(200, status)
        set_cookie = headers.get("Set-Cookie")
        self.assertTrue(set_cookie.startswith(f"{ACCESS_COOKIE_NAME}="))
        self.assertIn("Path=/", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=Strict", set_cookie)
        self.assertIn("Max-Age=", set_cookie)
        self.assertNotIn("Domain=", set_cookie)
        self.assertNotIn("Secure", set_cookie)
        cookie = set_cookie.split(";", 1)[0]

        status, payload, _ = self.request(
            "/api/review",
            method="POST",
            payload={"not": "a review"},
            headers={"Authorization": f"Bearer {_REVIEW_TOKEN}"},
        )
        self.assertEqual(401, status)
        self.assertEqual("access_required", payload["error"])

        status, payload, _ = self.request(
            "/api/review",
            method="POST",
            payload={"not": "a review"},
            headers={"Cookie": cookie},
        )
        self.assertEqual(401, status)
        self.assertEqual("unauthorized", payload["error"])
        self.assertEqual(200, self.request("/api/review-queue", headers={"Cookie": cookie})[0])


if __name__ == "__main__":
    unittest.main()
