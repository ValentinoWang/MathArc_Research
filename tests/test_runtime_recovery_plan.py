import unittest

from matharc.v02.runtime.recovery import RecoveryError, build_recovery_plan


class RuntimeRecoveryTests(unittest.TestCase):
    def test_plan_uses_last_complete_commit_and_is_replayable(self):
        commits = [{"runtime_run_id": "r", "generation_id": "g1", "complete": True, "snapshot_digest": "s1", "failures": [{"execution_id": "e1", "failure_class": "TIMEOUT"}]}]
        plan = build_recovery_plan(commits, expected={"snapshot_digest": "s1"})
        self.assertEqual(plan.next_generation_id, "g2")
        self.assertIn("retry_failures", plan.actions)
        self.assertEqual(plan.plan_digest, build_recovery_plan(commits, expected={"snapshot_digest": "s1"}).plan_digest)

    def test_input_digest_drift_rejects_recovery(self):
        commit = {"runtime_run_id": "r", "generation_id": "g1", "complete": True, "snapshot_digest": "old"}
        with self.assertRaises(RecoveryError): build_recovery_plan([commit], expected={"snapshot_digest": "new"})


if __name__ == "__main__": unittest.main()
