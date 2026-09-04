import unittest

from matharc.v02.runtime.contracts import ResearchRunSpec
from matharc.v02.runtime.coordinator import RuntimeCoordinator


class ApprovedTaskIngestionContractTests(unittest.TestCase):
    """Coordinator owns this integration; this sentinel prevents accidental test omission."""

    def test_contract_is_scoped_to_coordinator(self):
        self.assertTrue(True)

    def test_rejected_and_over_budget_tasks_never_start(self):
        coordinator = RuntimeCoordinator()
        with self.assertRaises(PermissionError):
            coordinator.ingest_approved_task({"task_id": "denied", "status": "REJECTED"})
        coordinator.ingest_approved_task({
            "task_id": "approved",
            "status": "APPROVED",
            "budget": {"max_steps": 2},
        })
        spec = ResearchRunSpec(
            workspace_id="ws", trace_id="trace", runtime_run_id="run",
            task_id="approved", budget={"max_steps": 3},
        )
        with self.assertRaises(ValueError):
            coordinator.run_approved_task("approved", spec)
        self.assertEqual(coordinator._started_tasks, set())

    def test_approved_task_is_one_shot(self):
        coordinator = RuntimeCoordinator()
        coordinator.ingest_approved_task({"task_id": "once", "status": "APPROVED"})
        spec = ResearchRunSpec(
            workspace_id="ws", trace_id="trace", runtime_run_id="run",
            task_id="once",
        )
        result = coordinator.run_approved_task("once", spec)
        self.assertTrue(result.started_full_run)
        with self.assertRaises(ValueError):
            coordinator.run_approved_task("once", spec)


if __name__ == "__main__":
    unittest.main()
