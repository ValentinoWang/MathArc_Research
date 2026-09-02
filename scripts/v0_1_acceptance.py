#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_command(command: list[str], cwd: Path, timeout: int = 900) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "passed": completed.returncode == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/v0.1-acceptance.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    required = [
        "matharc/codex_runtime.py",
        "matharc/agent_service.py",
        "matharc/api.py",
        "matharc/dashboard.py",
        "tests/test_codex_runtime.py",
        "tests/test_codex_dashboard.py",
        "docs/reports/codex-agent-runtime.md",
        "docs/reports/v0.1-engineering-contract-acceptance.md",
        "benchmarks/v0.1-acceptance-contract.json",
        "experiments/frankl_q6_round4/LATEST_Q6_AUDIT.md",
    ]
    file_checks = {item: (root / item).is_file() for item in required}

    with tempfile.TemporaryDirectory(prefix="matharc-acceptance-") as directory:
        demo_dir = Path(directory) / "demo"
        commands = [
            run_command(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                root,
            ),
            run_command(
                [sys.executable, "-m", "matharc", "demo", "--out-dir", str(demo_dir)],
                root,
            ),
            run_command(
                [
                    sys.executable,
                    "-m",
                    "matharc",
                    "validate",
                    "--run",
                    str(demo_dir / "run.json"),
                ],
                root,
            ),
            run_command(
                [
                    sys.executable,
                    "-m",
                    "matharc",
                    "codex",
                    "status",
                    "--workspace",
                    str(root),
                ],
                root,
            ),
        ]
        dashboard = (
            (demo_dir / "dashboard.html").read_text(encoding="utf-8")
            if (demo_dir / "dashboard.html").is_file()
            else ""
        )
        validation = (
            json.loads(commands[2]["stdout_tail"])
            if commands[2]["passed"] and commands[2]["stdout_tail"].strip()
            else {}
        )

    progress_path = root / "benchmarks" / "engineering-progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    dashboard_markers = {
        "codex_agent_panel": "Codex Research Agents" in dashboard,
        "sse_endpoint": "/api/agent/stream" in dashboard,
        "proof_graph": "Claim / Obligation DAG" in dashboard,
        "proposal_only_boundary": "Codex acceptance authority" in dashboard,
        "workspace_write_explicit": "workspace-write" in dashboard,
    }
    semantic_checks = {
        "weighted_completion_is_100": progress.get("weighted_completion_percent") == 100.0,
        "demo_valid": validation.get("valid") is True,
        "demo_release_state": validation.get("release_state") == "MACHINE_VERIFIED",
        "demo_theorem_closure": validation.get("theorem_closure_binary") == 1,
        "demo_certificate_debt_empty": validation.get("certificate_debt") == [],
        "superiority_claim_remains_benchmark_gated": progress.get(
            "external_superiority_claim"
        )
        == "BLOCKED_PENDING_MATCHED_EMPIRICAL_REPLAY",
    }

    passed = (
        all(file_checks.values())
        and all(item["passed"] for item in commands)
        and all(dashboard_markers.values())
        and all(semantic_checks.values())
    )
    result = {
        "schema_version": 1,
        "contract": "MathArc Research v0.1 engineering contract",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "FAIL",
        "engineering_completion_percent": 100.0 if passed else progress.get(
            "weighted_completion_percent", 0
        ),
        "scope_note": (
            "100% means the frozen v0.1 engineering deliverables are implemented and replayed. "
            "It does not mean Frankl's full conjecture is proved or that MathArc empirically "
            "outperforms every prover."
        ),
        "required_files": file_checks,
        "commands": commands,
        "dashboard_markers": dashboard_markers,
        "semantic_checks": semantic_checks,
        "next_version_frontier": [
            "matched-budget external prover leaderboard",
            "clean-room Frankl q=6 verifier reimplementation",
            "minimum-three-set q>=7 research program",
        ],
    }
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
