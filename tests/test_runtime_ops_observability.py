from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.trace import RuntimeQuota, StructuredRuntimeLogger


class RuntimeOpsObservabilityTests(unittest.TestCase):
    def test_structured_log_and_quota_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = StructuredRuntimeLogger(Path(directory) / "runtime.jsonl")
            record = log.emit("run.started", runtime_run_id="rr-1", release_id="rel-1", api_token="do-not-log")
            self.assertEqual(record["event"], "run.started")
            parsed = json.loads((Path(directory) / "runtime.jsonl").read_text().strip())
            self.assertEqual(parsed["runtime_run_id"], "rr-1")
            self.assertEqual(parsed["api_token"], "[REDACTED]")
        quota = RuntimeQuota(per_user=2, global_limit=3)
        self.assertTrue(quota.consume("alice"))
        self.assertTrue(quota.consume("alice"))
        self.assertFalse(quota.consume("alice"))
        self.assertTrue(quota.consume("bob"))
        self.assertFalse(quota.consume("bob"))


if __name__ == "__main__":
    unittest.main()
