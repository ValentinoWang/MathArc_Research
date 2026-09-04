from __future__ import annotations

import json
import threading
import unittest
from http.client import HTTPConnection

from matharc.v02.runtime.demo_server import DemoHandler
from http.server import ThreadingHTTPServer


class DemoServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method: str, path: str, body: object | None = None) -> tuple[int, dict | str]:
        connection = HTTPConnection(self.host, self.port, timeout=5)
        encoded = None
        headers = {}
        if body is not None:
            encoded = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        content_type = response.getheader("Content-Type", "")
        connection.close()
        return response.status, json.loads(raw) if "json" in content_type else raw.decode("utf-8")

    def test_health_and_page_are_available(self) -> None:
        status, payload = self.request("GET", "/api/health")
        self.assertEqual(200, status)
        self.assertEqual("matharc-agent-demo", payload["service"])
        status, page = self.request("GET", "/problem-intel-console.html")
        self.assertEqual(200, status)
        self.assertIn("问题智能运行台", page)

    def test_run_endpoint_returns_the_complete_demo_projection(self) -> None:
        status, payload = self.request(
            "POST", "/api/demo/run", {"question": "Prove that the sum of the first n positive odd integers equals n squared."}
        )
        self.assertEqual(200, status)
        self.assertEqual("VERIFIED_CERTIFICATE", payload["status"])
        self.assertEqual("READY", payload["stages"]["decomposition"]["status"])
        self.assertEqual("PASS", payload["stages"]["tool"]["status"])
        self.assertEqual("PASS", payload["stages"]["verification"]["status"])
        self.assertFalse(payload["stages"]["result"]["promotion_allowed"])
        self.assertTrue(payload["evidence"]["evidence_id"])

    def test_run_endpoint_rejects_empty_question(self) -> None:
        status, payload = self.request("POST", "/api/demo/run", {"question": " "})
        self.assertEqual(400, status)
        self.assertEqual("question is required", payload["error"])


if __name__ == "__main__":
    unittest.main()
