from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.recovery import RecoveryError, build_recovery_plan
from matharc.v02.runtime.run_store import RuntimeStore


class RuntimeAttackRecoveryTests(unittest.TestCase):
    def test_snapshot_drift_blocks_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            store.record_generation_commit({"runtime_run_id": "r", "generation_id": "g1", "complete": True, "snapshot_digest": "known", "commit_digest": "commit"})
            with self.assertRaises(RecoveryError):
                build_recovery_plan(store, expected={"snapshot_digest": "attacker-value"})

    def test_retryable_and_rejected_failures_have_separate_actions(self) -> None:
        plan = build_recovery_plan([{
            "runtime_run_id": "r", "generation_id": "g1", "complete": True,
            "failures": [
                {"execution_id": "timeout-1", "failure_class": "TIMEOUT"},
                {"execution_id": "bad-1", "failure_class": "INVALID_OUTPUT", "retryable": False},
            ],
        }], max_retries=1)
        self.assertIn("retry_failures", plan.actions)
        self.assertEqual(plan.retryable_failures, ("timeout-1",))
        self.assertEqual(plan.rejected_failures, ("bad-1",))

    def test_missing_complete_commit_fails_closed(self) -> None:
        with self.assertRaises(RecoveryError):
            build_recovery_plan([{"runtime_run_id": "r", "generation_id": "g1", "complete": False}])


if __name__ == "__main__":
    unittest.main()
