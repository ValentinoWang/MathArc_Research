from __future__ import annotations

import argparse
import json
from pathlib import Path

from matharc.v02.workspace_bundle import write_full_workspace_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/v02-workspace")
    args = parser.parse_args()
    paths = write_full_workspace_bundle(Path(args.out_dir))
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
