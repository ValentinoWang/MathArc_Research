from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from matharc.v02.benchmark_runner import (
    BenchmarkCase,
    BudgetSpec,
    PairedBenchmarkRunner,
    SubprocessAgentSpec,
)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def agent_code(score: float, *, private_field: bool = False, token_usage: int = 10) -> str:
    payload = {
        "release_state": "PROVED_AND_AUDITED",
        "metrics": {"audited_closure": score},
        "false_promotion": False,
        "replay_pass": True,
        "usage": {
            "tokens": token_usage,
            "model_calls": 1,
            "tool_cpu_seconds": 0.1,
        },
    }
    if private_field:
        payload["chain_of_thought"] = "forbidden"
    return (
        "import json,sys; request=json.load(sys.stdin); "
        f"print(json.dumps({payload!r}, sort_keys=True))"
    )


def spec(name: str, code: str, cwd: str) -> SubprocessAgentSpec:
    return SubprocessAgentSpec(
        system_name=name,
        system_version="test-v1",
        command=(sys.executable, "-c", code),
        cwd=cwd,
        adapter_id=f"adapter-{name}",
        environment_lock_digest_sha256=sha(f"environment-{name}"),
    )


def case() -> BenchmarkCase:
    return BenchmarkCase(
        case_id="CASE-1",
        family_id="FORMAL-COMPLETION",
        problem="test case",
        theorem_contract={"target": "C"},
        case_payload={"input": 1},
        required_metrics=("audited_closure",),
        acceptance_contract={"cold_replay": True},
    )


class PairedBenchmarkRunnerTests(unittest.TestCase):
    def test_equal_budget_paired_execution_can_qualify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = PairedBenchmarkRunner(
                suite_id="TEST-SUITE",
                suite_version="1.0",
                candidate=spec("candidate", agent_code(1.0), directory),
                baseline=spec("baseline", agent_code(0.5), directory),
                budget=BudgetSpec(5.0, 100_000, 100, 2, 1.0),
                output_root=Path(directory) / "run",
                metric_directions={"audited_closure": "maximize"},
                primary_metrics=("audited_closure",),
                minimum_pairs=4,
                bootstrap_samples=200,
            )
            run = runner.run([case()], range(4))
            self.assertTrue(run.comparison.superiority_claim_allowed, run.to_dict())
            self.assertEqual(run.comparison.paired_case_count, 4)
            self.assertEqual(len(run.executions), 8)
            self.assertTrue((Path(directory) / "run" / "run.json").is_file())
            orders = [item.result.system_name for item in run.executions]
            self.assertIn("candidate", orders[:2])
            self.assertIn("baseline", orders[:2])

    def test_adapter_budget_violation_blocks_qualification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = PairedBenchmarkRunner(
                suite_id="TEST-SUITE",
                suite_version="1.0",
                candidate=spec("candidate", agent_code(1.0, token_usage=101), directory),
                baseline=spec("baseline", agent_code(0.5), directory),
                budget=BudgetSpec(5.0, 100_000, 100, 2, 1.0),
                output_root=Path(directory) / "run",
                metric_directions={"audited_closure": "maximize"},
                primary_metrics=("audited_closure",),
                minimum_pairs=2,
                bootstrap_samples=100,
            )
            run = runner.run([case()], range(2))
            self.assertFalse(run.comparison.superiority_claim_allowed)
            candidate = [
                item for item in run.executions if item.result.system_name == "candidate"
            ]
            self.assertTrue(all(item.status == "BUDGET_VIOLATION" for item in candidate))
            self.assertTrue(all(not item.result.replay_pass for item in candidate))

    def test_private_reasoning_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = PairedBenchmarkRunner(
                suite_id="TEST-SUITE",
                suite_version="1.0",
                candidate=spec(
                    "candidate",
                    agent_code(1.0, private_field=True),
                    directory,
                ),
                baseline=spec("baseline", agent_code(0.5), directory),
                budget=BudgetSpec(5.0, 100_000, 100, 2, 1.0),
                output_root=Path(directory) / "run",
                metric_directions={"audited_closure": "maximize"},
                primary_metrics=("audited_closure",),
                minimum_pairs=1,
                bootstrap_samples=50,
            )
            run = runner.run([case()], [0])
            candidate = next(
                item for item in run.executions if item.result.system_name == "candidate"
            )
            self.assertEqual(candidate.status, "ERROR")
            self.assertFalse(candidate.result.replay_pass)
            self.assertFalse(run.comparison.superiority_claim_allowed)

    def test_request_and_execution_artifacts_are_hash_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = PairedBenchmarkRunner(
                suite_id="TEST-SUITE",
                suite_version="1.0",
                candidate=spec("candidate", agent_code(0.8), directory),
                baseline=spec("baseline", agent_code(0.7), directory),
                budget=BudgetSpec(5.0, 100_000, 100, 2, 1.0),
                output_root=Path(directory) / "run",
                metric_directions={"audited_closure": "maximize"},
                primary_metrics=("audited_closure",),
                minimum_pairs=1,
                bootstrap_samples=50,
            )
            run = runner.run([case()], [7])
            for execution in run.executions:
                root = Path(execution.artifact_directory)
                self.assertTrue((root / "request.json").is_file())
                self.assertTrue((root / "stdout.txt").is_file())
                self.assertTrue((root / "stderr.txt").is_file())
                payload = json.loads((root / "execution.json").read_text())
                self.assertEqual(
                    payload["stdout_digest_sha256"], execution.stdout_digest_sha256
                )
                self.assertEqual(len(execution.result.artifact_digest_sha256), 64)


if __name__ == "__main__":
    unittest.main()
