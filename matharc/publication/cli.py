from __future__ import annotations

import argparse
import json
from pathlib import Path

from .gates import audit_publication


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="matharc-publication")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="run fail-closed publication gates")
    audit.add_argument("--workspace", required=True, type=Path)
    audit.add_argument("--publication-bundle", required=True, type=Path)
    audit.add_argument("--latex", type=Path)
    audit.add_argument("--claim-map", type=Path)
    audit.add_argument("--abstract", type=Path)
    audit.add_argument("--compile", action="store_true", help="run the available LaTeX compiler")
    args = parser.parse_args(argv)
    if args.command == "audit":
        report = audit_publication(args.workspace, args.publication_bundle, latex=args.latex,
                                   claim_map=args.claim_map, abstract=args.abstract,
                                   compile_source=args.compile)
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report.valid else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
