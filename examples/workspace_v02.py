from __future__ import annotations

import argparse
import json
from pathlib import Path

from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_demo import write_workspace_demo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate or verify the MathArc v0.2 tamper-evident workspace demo."
    )
    parser.add_argument("--out-dir", default="artifacts/v02-workspace")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    target = Path(args.out_dir)
    if args.verify:
        workspace = ResearchWorkspace.load(target)
        report = workspace.audit()
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        raise SystemExit(0 if report.valid else 1)
    paths = write_workspace_demo(target)
    print(
        json.dumps(
            {key: str(value) for key, value in paths.items()},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
