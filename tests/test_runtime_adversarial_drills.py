from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.backends.base import BackendRequest, DeterministicTestBackend
from matharc.v02.runtime.contracts import ExecutionStatus, WorkerExecutionResult
from matharc.v02.runtime.coordinator import RuntimeCoordinator
from matharc.v02.runtime.run_store import RuntimeStore, RuntimeStoreError
from matharc.v02.runtime.service import ConsoleRuntimeService


class RuntimeAdversarialDrillTests(unittest.TestCase):
    def test_identity_mismatch_is_rejected_at_result_boundary(self) -> None:
        result = WorkerExecutionResult("workspace", "trace", "run", "g1", "worker", "exec", ExecutionStatus.SUCCEEDED, "d")
        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            store.create_run({"workspace_id": "workspace", "trace_id": "trace", "runtime_run_id": "run"})
            with self.assertRaises(RuntimeStoreError):
                store.import_execution_result({**result.to_dict(), "trace_id": "other"})

    def test_conflicting_replay_for_same_execution_id_is_rejected(self) -> None:
        backend = DeterministicTestBackend(output={"value": 1})
        coordinator = RuntimeCoordinator(backends={"deterministic-test": backend})
        request = BackendRequest("w", "t", "r", "g1", "worker", "task", payload={"x": 1}, execution_id="e1")
        coordinator.execute_backend(request)
        with self.assertRaises(ValueError):
            coordinator.execute_backend(BackendRequest("w", "t", "r", "g1", "worker", "task", payload={"x": 2}, execution_id="e1"))

    def test_tampered_event_chain_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            store = RuntimeStore(root)
            store.append_event("NOTE", {"value": 1})
            path = root / "events.jsonl"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["payload"]["value"] = 2
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            with self.assertRaises(RuntimeStoreError):
                RuntimeStore(root)

    def test_console_rejects_process_authority_fields(self) -> None:
        service = ConsoleRuntimeService(".")
        with self.assertRaises(ValueError):
            service.create_run("pilot-run", command="sh")
        with self.assertRaises(ValueError):
            service.runtime_action("pilot-run", "start", action_id="a1", payload={"cwd": "/tmp"})


if __name__ == "__main__":
    unittest.main()
