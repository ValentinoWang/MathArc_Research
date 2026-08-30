from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from matharc.v02.benchmark_runner import (
    BenchmarkCase,
    BudgetSpec,
    PairedBenchmarkRunner,
    SubprocessAgentSpec,
)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/v02-benchmark-smoke")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    mock = root / "examples" / "mock_benchmark_agent.py"
    candidate = SubprocessAgentSpec(
        system_name="MathArc protocol mock candidate",
        system_version="smoke-v1",
        command=(sys.executable, str(mock)),
        cwd=str(root),
        adapter_id="mock-candidate",
        environment_lock_digest_sha256=sha("python-stdlib-mock-candidate-v1"),
        extra_env=(("MATHARC_MOCK_SCORE", "1.0"),),
    )
    baseline = SubprocessAgentSpec(
        system_name="Protocol mock baseline",
        system_version="smoke-v1",
        command=(sys.executable, str(mock)),
        cwd=str(root),
        adapter_id="mock-baseline",
        environment_lock_digest_sha256=sha("python-stdlib-mock-baseline-v1"),
        extra_env=(("MATHARC_MOCK_SCORE", "0.5"),),
    )
    case = BenchmarkCase(
        case_id="MOCK-CASE",
        family_id="PROTOCOL-SMOKE",
        problem="Exercise the paired benchmark protocol; no external mathematics system is measured.",
        theorem_contract={
            "target": "return a deterministic, replayable protocol record",
            "non_claims": ["external-agent superiority", "mathematical research performance"],
        },
        case_payload={"synthetic": True},
        required_metrics=("audited_closure",),
        acceptance_contract={"replay_pass": True, "false_promotion": False},
    )
    runner = PairedBenchmarkRunner(
        suite_id="MATHARC-SYNTHETIC-PROTOCOL-SMOKE",
        suite_version="1.0",
        candidate=candidate,
        baseline=baseline,
        budget=BudgetSpec(
            wall_time_seconds=10.0,
            max_output_bytes=100_000,
            token_budget=100,
            model_call_budget=2,
            tool_cpu_seconds=1.0,
        ),
        output_root=args.out_dir,
        metric_directions={"audited_closure": "maximize"},
        primary_metrics=("audited_closure",),
        minimum_pairs=30,
        bootstrap_samples=500,
    )
    run = runner.run([case], range(30))
    raw = run.comparison.to_dict()
    public = dict(raw)
    public["raw_protocol_gate_passed"] = raw["superiority_claim_allowed"]
    public["qualification_state"] = "SYNTHETIC_PROTOCOL_PASS_NOT_EXTERNAL_EVIDENCE"
    public["superiority_claim_allowed"] = False
    public["reasons"] = [
        "Synthetic mock agents were used only to test the benchmark machinery.",
        "No external mathematics agent was measured.",
        "No product or research superiority claim is permitted from this run.",
    ]
    report = Path(args.out_dir) / "public-comparison.json"
    report.write_text(
        json.dumps(public, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "raw_protocol_gate_passed": raw["superiority_claim_allowed"],
                "public_superiority_claim_allowed": False,
                "paired_case_count": raw["paired_case_count"],
                "run": str(Path(args.out_dir) / "run.json"),
                "public_comparison": str(report),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(0 if raw["superiority_claim_allowed"] else 1)


if __name__ == "__main__":
    main()
