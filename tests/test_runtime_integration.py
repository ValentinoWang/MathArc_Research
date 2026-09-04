from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.access import InvitationAccessStore
from matharc.v02.access_server import AccessAPI
from matharc.v02.runtime import RuntimeCoordinator, RuntimeStore
from matharc.v02.runtime.backends.base import DeterministicTestBackend
from matharc.v02.runtime.contracts import ResearchRunSpec, ResearchWorkerSpec
from matharc.v02.runtime.service import ConsoleRuntimeService, PermissionDeniedError


class RuntimeIntegrationTests(unittest.TestCase):
    def test_coordinator_records_run_execution_candidate_and_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            spec = ResearchRunSpec(
                "workspace", "trace", "run-1", "task-1",
                workers=(ResearchWorkerSpec("worker-1", backend="deterministic-test"),),
            )
            result = RuntimeCoordinator(
                backends={"deterministic-test": DeterministicTestBackend(output={"answer": 42})},
                runtime_store=store,
            ).run(spec)
            self.assertTrue(result.success)
            state = store.state
            self.assertIn("run-1", state["runs"])
            self.assertIn("exec-run-1-worker-1", state["executions"])
            self.assertIn(result.candidates[0].candidate_id, state["candidates"])
            self.assertEqual(len(state["commits"]), 1)

    def test_default_worker_backend_is_registered(self) -> None:
        spec = ResearchRunSpec(
            "workspace", "trace", "run-default", "task-default",
            workers=(ResearchWorkerSpec("worker-1"),),
        )
        result = RuntimeCoordinator().run(spec)
        self.assertTrue(result.started_full_run)
        self.assertEqual(result.results[0].status.value, "FAILED")
        self.assertEqual(result.results[0].failure_class, "TOOL_UNAVAILABLE")

    def test_service_replays_lifecycle_receipt_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime"
            first_store = RuntimeStore(path)
            first = ConsoleRuntimeService("artifacts/v02-workspace", runtime_store=first_store)
            first.create_run("run-1")
            receipt = first.runtime_action("run-1", "start", action_id="action-1")
            second = ConsoleRuntimeService("artifacts/v02-workspace", runtime_store=RuntimeStore(path))
            replay = second.runtime_action("run-1", "start", action_id="action-1")
            self.assertEqual(receipt.to_dict(), replay.to_dict())
            self.assertEqual(second.runtime_action("run-1", "revalidate", action_id="action-2").resulting_state.value, "RUNNING")

    def test_stop_is_a_valid_persisted_contract_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            service = ConsoleRuntimeService("artifacts/v02-workspace", runtime_store=store)
            service.create_run("run-1")
            service.runtime_action("run-1", "start", action_id="start")
            stopped = service.runtime_action("run-1", "stop", action_id="stop")
            self.assertEqual(stopped.resulting_state.value, "STOPPED")
            self.assertEqual(store.state["runs"]["run-1"]["status"], "STOPPED")

    def test_actor_and_wired_action_boundaries_fail_closed(self) -> None:
        service = ConsoleRuntimeService("artifacts/v02-workspace")
        with self.assertRaises(PermissionDeniedError):
            service.create_run("run-1", actor="spoofed")
        with self.assertRaises(PermissionDeniedError):
            service.register_action("review-submit", idempotency_key="review-1")

    def test_actor_must_match_authenticated_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            access = InvitationAccessStore(Path(directory) / "access")
            invitation = access.issue_invitation(email="researcher@example.com", topic_scopes=["runtime"])
            token, _ = access.redeem(email="researcher@example.com", code=invitation.code)
            service = ConsoleRuntimeService(
                "artifacts/v02-workspace", access_api=AccessAPI(access)
            )
            cookie = f"matharc_access_session={token}"
            with self.assertRaises(PermissionDeniedError):
                service.create_run("run-1", actor="spoofed", cookie_header=cookie)
            self.assertEqual(
                service.create_run("run-1", actor="researcher@example.com", cookie_header=cookie)["status"],
                "CREATED",
            )


if __name__ == "__main__":
    unittest.main()
