from __future__ import annotations

import json
import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from matharc.v02.runtime.ops import bootstrap_from_env
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

    def test_bootstrap_wires_logger_quota_and_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credential = root / "credential"; credential.write_text("token\n", encoding="utf-8")
            run = root / "runs/current.json"; run.parent.mkdir(); run.write_text('{"runtime_run_id":"rr","release_id":"rel"}', encoding="utf-8")
            env = {
                "MATHARC_RUNTIME_RUN_ID": "rr", "MATHARC_RELEASE_ID": "rel",
                "MATHARC_RUN_PATH": str(run), "MATHARC_WORKSPACE": str(root / "workspace"),
                "MATHARC_STORE_PATH": str(root / "store"), "MATHARC_BACKUP_PATH": str(root / "backup"),
                "MATHARC_LOG_PATH": str(root / "log/runtime.jsonl"), "MATHARC_SECRET_FILE": str(credential),
                "MATHARC_PER_USER_QUOTA": "2", "MATHARC_GLOBAL_QUOTA": "4",
                "MATHARC_CANCEL_POLICY": "TERM", "MATHARC_FAILURE_POLICY": "classify",
            }
            with patch.dict(os.environ, env, clear=False):
                runtime = bootstrap_from_env()
            self.assertEqual(runtime.quota.per_user_limit, 2)
            self.assertEqual(runtime.policy["cancel_policy"], "TERM")
            self.assertTrue((root / "log/runtime.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
