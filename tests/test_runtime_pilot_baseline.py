from __future__ import annotations

import json
import unittest
from pathlib import Path

from matharc.v02.runtime.backends.base import DeterministicTestBackend
from matharc.v02.runtime.contracts import ResearchRunSpec, ResearchWorkerSpec
from matharc.v02.runtime.coordinator import RuntimeCoordinator
from matharc.v02.runtime.evaluator import EvaluationContract

ROOT = Path(__file__).resolve().parents[1]


class RuntimePilotBaselineTests(unittest.TestCase):
    def test_plan_is_explicitly_local_and_non_production(self) -> None:
        plan = json.loads((ROOT / "benchmarks/runtime-pilot-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["schema_version"], "runtime-pilot-plan.v1")
        self.assertEqual(plan["status"], "PLANNED")
        self.assertFalse(plan["production_claim"])
        self.assertFalse(plan["human_acceptance_claim"])
        self.assertEqual([item["generation_id"] for item in plan["generations"]], ["g1", "g2"])

    def test_smoke_gate_blocks_workers(self) -> None:
        backend = DeterministicTestBackend()
        spec = ResearchRunSpec(
            "pilot-workspace", "pilot-trace", "pilot-run", "pilot-task",
            workers=(ResearchWorkerSpec("worker-1", backend="deterministic-test"),),
        )
        evaluator = EvaluationContract("pilot-evaluator", lambda request: (_ for _ in ()).throw(ValueError("smoke failed")))
        result = RuntimeCoordinator(backends={"deterministic-test": backend}, evaluator=evaluator).run(spec)
        self.assertFalse(result.started_full_run)
        self.assertEqual(backend.calls, 0)
        self.assertFalse(result.smoke_result.passed)

    def test_successful_baseline_is_seeded_and_idempotent(self) -> None:
        backend = DeterministicTestBackend(output={"answer": 42})
        spec = ResearchRunSpec(
            "pilot-workspace", "pilot-trace", "pilot-run", "pilot-task", seed=7,
            workers=(ResearchWorkerSpec("worker-1", backend="deterministic-test"),),
        )
        coordinator = RuntimeCoordinator(backends={"deterministic-test": backend})
        first = coordinator.run(spec, evaluation_input={"problem": "baseline"})
        second = coordinator.run(spec, evaluation_input={"problem": "baseline"})
        self.assertTrue(first.started_full_run)
        self.assertTrue(first.smoke_result.passed)
        self.assertEqual(first.results[0].status.value, "SUCCEEDED")
        self.assertEqual(first.candidates[0].runtime_run_id, "pilot-run")
        self.assertEqual(first.candidates[0].generation_id, "generation-1")
        self.assertEqual(first.to_dict() if hasattr(first, "to_dict") else first.results[0].to_dict(),
                         second.to_dict() if hasattr(second, "to_dict") else second.results[0].to_dict())
        self.assertEqual(backend.calls, 1)


if __name__ == "__main__":
    unittest.main()
