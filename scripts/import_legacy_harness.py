from __future__ import annotations

import argparse
import json
from pathlib import Path

from matharc.v02.legacy_harness import ImportPolicy, import_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a legacy proof-research harness without laundering its claims."
    )
    parser.add_argument("--progress", required=True)
    parser.add_argument("--validation")
    parser.add_argument("--acceptance-manifest")
    parser.add_argument(
        "--policy",
        choices=["metadata_only", "replay_manifest"],
        default="metadata_only",
    )
    parser.add_argument(
        "--allow-same-source-replay",
        action="store_true",
        help="Do not require independent reconstruction. Intended only for diagnostics.",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = import_files(
        args.progress,
        validation_path=args.validation,
        acceptance_manifest_path=args.acceptance_manifest,
        policy=ImportPolicy(
            mode=args.policy,
            require_independent_replay=not args.allow_same_source_replay,
        ),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "release_state": result["release_state"]}, indent=2))


if __name__ == "__main__":
    main()
