from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_server import make_server


class ConsoleObservatoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "workspace"
        write_full_workspace_bundle(self.root)
        self.console = self.root / "console.html"
        self.console.write_text("<!doctype html><title>Console fixture</title>", encoding="utf-8")
        self.server = make_server(self.root, host="127.0.0.1", port=0, dashboard_path=self.console, campaign_report_path=self.root / "campaign.json")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2); self.temporary.cleanup()

    def test_missing_campaign_is_explicit_and_post_stays_read_only(self) -> None:
        with urlopen(self.base + "/api/campaign") as response:
            payload = json.loads(response.read().decode())
            self.assertFalse(payload["available"])
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        with self.assertRaises(HTTPError) as captured:
            urlopen(Request(self.base + "/api/campaign", data=b"{}", method="POST"))
        self.assertEqual(captured.exception.code, 405)

    def test_campaign_schema_and_console_dashboard_are_served(self) -> None:
        report = {"rounds": [], "stop_reason": "done", "final_metrics": {}, "budget": None, "creation_log": []}
        (self.root / "campaign.json").write_text(json.dumps(report), encoding="utf-8")
        with urlopen(self.base + "/api/campaign") as response:
            payload = json.loads(response.read().decode())
        self.assertTrue(payload["available"])
        self.assertEqual(payload["report"], report)
        with urlopen(self.base + "/") as response:
            self.assertIn("Console fixture", response.read().decode())

        with urlopen(self.base + "/api/console") as response:
            console = json.loads(response.read().decode())
        self.assertEqual(console["schema_version"], "1.0")
        self.assertTrue(console["workspace"]["audit"]["valid"])

    def test_missing_dashboard_is_not_generated_by_a_get_request(self) -> None:
        self.console.unlink()
        with self.assertRaises(HTTPError) as captured:
            urlopen(self.base + "/")
        self.assertEqual(captured.exception.code, 404)
        self.assertFalse(self.console.exists())


if __name__ == "__main__":
    unittest.main()
