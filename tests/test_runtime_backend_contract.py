import unittest

from matharc.v02.runtime.backends.base import BackendRequest, DeterministicTestBackend
from matharc.v02.runtime.backends.codex import CodexBackend
from matharc.v02.runtime.backends.local_process import LocalExactToolBackend
from matharc.v02.runtime.contracts import ExecutionStatus, ResearchRunSpec, ResearchWorkerSpec
from matharc.v02.runtime.coordinator import RuntimeCoordinator


def request(backend="deterministic-test", **extra):
    return BackendRequest("w", "t", "run", "gen-1", "worker", "task",
                          payload={"backend": backend, "value": 2}, execution_id="exec-1", **extra)


class RuntimeBackendContractTests(unittest.TestCase):
    def test_three_first_party_backends_have_independent_identity(self):
        self.assertEqual(DeterministicTestBackend.name, "deterministic-test")
        self.assertEqual(CodexBackend.name, "codex")
        self.assertEqual(LocalExactToolBackend.name, "local-exact-tool")

    def test_result_is_immutable_and_coordinator_only_assembles_candidate(self):
        coordinator = RuntimeCoordinator(backends={"deterministic-test": DeterministicTestBackend()})
        result = coordinator.execute_backend(request())
        with self.assertRaises(Exception):
            result.status = ExecutionStatus.FAILED
        spec = ResearchRunSpec("w", "t", "run", "task", workers=(ResearchWorkerSpec("worker", backend="deterministic-test"),))
        run = coordinator.run(spec)
        self.assertTrue(run.started_full_run)
        self.assertEqual(len(run.candidates), 1)

    def test_execution_id_is_idempotent(self):
        backend = DeterministicTestBackend()
        coordinator = RuntimeCoordinator(backends={"deterministic-test": backend})
        first = coordinator.execute_backend(request())
        second = coordinator.execute_backend(request())
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(backend.calls, 1)


if __name__ == "__main__":
    unittest.main()
