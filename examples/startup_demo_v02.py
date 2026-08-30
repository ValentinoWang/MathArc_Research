from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from matharc.v02.workspace_demo import build_workspace_demo
from matharc.v02.workspace_visualization import render_workspace_dashboard


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/v02-startup-demo")
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    output = Path(args.out_dir)
    output.mkdir(parents=True, exist_ok=True)

    benchmark_dir = output / "benchmark"
    benchmark = subprocess.run(
        [
            sys.executable,
            str(project_root / "examples" / "paired_benchmark_v02.py"),
            "--out-dir",
            str(benchmark_dir),
        ],
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    (output / "benchmark-stdout.txt").write_text(
        benchmark.stdout, encoding="utf-8"
    )
    (output / "benchmark-stderr.txt").write_text(
        benchmark.stderr, encoding="utf-8"
    )
    if benchmark.returncode != 0:
        raise SystemExit(
            f"synthetic benchmark smoke failed ({benchmark.returncode}): {benchmark.stderr}"
        )
    comparison = json.loads(
        (benchmark_dir / "public-comparison.json").read_text(encoding="utf-8")
    )

    workspace_dir = output / "workspace"
    workspace = build_workspace_demo(workspace_dir)
    workspace_manifest = workspace.save()
    dashboard = render_workspace_dashboard(
        workspace,
        output / "index.html",
        comparison=comparison,
        title="MathArc Research v0.2 · Startup Research Observatory",
    )
    report = output / "startup-demo-report.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "dashboard": dashboard.name,
                "workspace_manifest": str(workspace_manifest.relative_to(output)),
                "workspace_state_digest_sha256": workspace.state_digest(),
                "workspace_event_head_hash": workspace.events.head_hash,
                "workspace_audit": workspace.audit().to_dict(),
                "benchmark": comparison,
                "claim_boundary": (
                    "The research workspace is a deterministic protocol demonstration. "
                    "The benchmark panel uses synthetic mock adapters and cannot support "
                    "an external-agent superiority claim."
                ),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "dashboard": str(dashboard),
                "report": str(report),
                "workspace_manifest": str(workspace_manifest),
                "public_superiority_claim_allowed": comparison[
                    "superiority_claim_allowed"
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
