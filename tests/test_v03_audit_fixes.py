from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.cli import DEFAULT_RUN_WALL_SECONDS_BUDGET, _build_run_budget
from matharc.v02.schema import ClaimRecord, TheoremContract, ToolCallRecord, ToolStatus, utc_now
from matharc.v02.trace import ResearchTrace
from matharc.v02.workers import WorkerExecution


def _run_args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "no_budget": False,
        "wall_seconds_budget": None,
        "cost_usd_budget": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class MeteredWorker:
    role = "prover"

    def execute(self, plan: Any, trace_view: Mapping[str, Any]) -> WorkerExecution:
        del trace_view
        timestamp = utc_now()
        call = ToolCallRecord(
            call_id="METERED-WORKER-1",
            tool="test:metered-worker",
            purpose="exercise usage reconciliation",
            status=ToolStatus.PASS,
            input_digest_sha256="a" * 64,
            output_digest_sha256="b" * 64,
            linked_claim_ids=(plan.focus_claim_id,),
            independence_group="test:metered-worker",
            replay_command="python -m unittest tests.test_v03_audit_fixes",
            started_at=timestamp,
            ended_at=timestamp,
            environment_digest_sha256="c" * 64,
        )
        proposal = {
            "status": "progress",
            "usage_report": {"input_tokens": 10, "output_tokens": 5},
            "public_reasoning": {
                "objective": "exercise the metering path",
                "premises": [],
                "proposed_move": "report usage and make no mathematical claim",
                "observation": "provider metering is deliberately different",
                "falsification": "the reconciliation must flag the mismatch",
                "decision": "leave the claim open",
            },
            "claim_boundary": "no proof claim is made",
        }
        return WorkerExecution(
            role=self.role,
            proposal=proposal,
            tool_call=call,
            raw_stdout="{}",
            raw_stderr="",
            model_usage={
                "provider": "test-provider",
                "input_tokens": 1000,
                "output_tokens": 500,
                "cost_usd": 0.01,
            },
        )


def _minimal_trace() -> ResearchTrace:
    trace = ResearchTrace(
        "AUDIT-FIX-RUN",
        TheoremContract("AUDIT-FIX", "Keep C open.", ("C",), "test scope"),
    )
    trace.add_claim(ClaimRecord("C", "C remains an open test claim.", "test scope"))
    return trace


class AuditFixTests(unittest.TestCase):
    def test_default_run_budget_is_fail_closed(self) -> None:
        budget = _build_run_budget(_run_args())
        self.assertIsInstance(budget, BudgetLedger)
        assert budget is not None
        self.assertEqual(budget.wall_seconds_limit, DEFAULT_RUN_WALL_SECONDS_BUDGET)
        self.assertEqual(DEFAULT_RUN_WALL_SECONDS_BUDGET, 1800.0)

    def test_unbounded_run_requires_explicit_opt_out(self) -> None:
        self.assertIsNone(_build_run_budget(_run_args(no_budget=True)))
        with self.assertRaises(SystemExit):
            _build_run_budget(
                _run_args(no_budget=True, wall_seconds_budget=60.0)
            )

    def test_campaign_reconciles_worker_report_against_metered_usage(self) -> None:
        trace = _minimal_trace()
        budget = BudgetLedger(wall_seconds_limit=60.0)
        report = ResearchCampaign(
            trace,
            [MeteredWorker()],
            budget=budget,
            max_rounds=1,
            max_rounds_without_gain=1,
        ).run()
        self.assertEqual(len(budget.divergent_usage_reports), 1)
        self.assertFalse(report.rounds[0]["workers"][0]["usage_reconciliation"]["consistent"])
        history = trace.metadata.get("usage_reconciliation")
        self.assertIsInstance(history, list)
        self.assertEqual(history[0]["call_id"], "METERED-WORKER-1")

    def test_workspace_server_example_runs_from_source_checkout_without_install(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        script = project_root / "examples" / "serve_workspace_v02.py"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, "-S", str(script), "--help"],
                cwd=directory,
                env=env,
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Serve a verified MathArc v0.2 workspace", completed.stdout)

    def test_repository_registry_has_active_matharc_profile(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        registry = (repo_root / "registry.yaml").read_text(encoding="utf-8")
        self.assertIn("project-matharc-research:", registry)
        self.assertIn("project_namespace: .", registry)


if __name__ == "__main__":
    unittest.main()
