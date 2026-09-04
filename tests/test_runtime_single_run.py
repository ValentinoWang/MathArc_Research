import unittest

from matharc.v02.runtime.contracts import ResearchRunSpec, ResearchWorkerSpec
from matharc.v02.runtime.coordinator import RuntimeCoordinator
from matharc.v02.runtime.evaluator import EvaluationContract


class RuntimeSingleRunTests(unittest.TestCase):
    def test_smoke_gate_precedes_workers(self):
        calls = []
        class Backend:
            def execute(self, request):
                calls.append(request.worker_id)
                return RuntimeCoordinator().backends["deterministic-test"].execute(request)
        spec = ResearchRunSpec("w", "t", "run-single", "task", workers=(ResearchWorkerSpec("worker", backend="deterministic-test"),))
        evaluator = EvaluationContract("eval", lambda request: (_ for _ in ()).throw(ValueError("no")))
        result = RuntimeCoordinator(backends={"deterministic-test": Backend()}, evaluator=evaluator).run(spec)
        self.assertFalse(result.started_full_run)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
