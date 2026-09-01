"""Run the deterministic, non-authorizing publication technical-preflight fixture.

This fixture exercises the publication audit against a generated demo workspace and
a tiny claim-mapped LaTeX tree.  It is a quality guard for the audit wiring only;
it is not evidence that a real manuscript is correct or ready for submission.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from matharc.publication.gates import PublicationAudit, audit_publication
from matharc.publication.models import PublicationBundle
from matharc.v02.workspace_demo import write_workspace_demo


FIXTURE_KIND = "publication-audit-technical-preflight"


@dataclass(frozen=True, slots=True)
class PublicationFixturePaths:
    workspace: Path
    bundle: Path
    latex: Path
    claim_map: Path
    abstract: Path


def write_publication_fixture(root: str | Path) -> PublicationFixturePaths:
    """Materialize the self-contained fixture under ``root``."""

    target = Path(root)
    target.mkdir(parents=True, exist_ok=True)
    workspace = target / "workspace"
    write_workspace_demo(workspace)

    latex = target / "main.tex"
    latex.write_text(
        """\\documentclass{article}
\\begin{document}
\\matharcclaim{C-TARGET}{0}
A fixture-only manuscript claim mapped to the demo trace.
\\end{document}
""",
        encoding="utf-8",
    )
    claim_map = target / "claim-map.json"
    claim_map.write_text(
        json.dumps({"claims": {"C-TARGET": 0}}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    abstract = target / "abstract.txt"
    abstract.write_text(
        "Fixture-only technical preflight for the MathArc publication audit.\n",
        encoding="utf-8",
    )
    bundle = target / "publication-bundle.json"
    publication_bundle = PublicationBundle(
        "matharc-technical-preflight-fixture",
        1,
        {"C-TARGET": 0},
        created_at="2026-09-01T00:00:00+00:00",
    )
    bundle.write_text(
        json.dumps(publication_bundle.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return PublicationFixturePaths(workspace, bundle, latex, claim_map, abstract)


def run_fixture(output: str | Path | None = None) -> PublicationAudit:
    """Run the fixture and optionally write a machine-readable audit record."""

    with tempfile.TemporaryDirectory(prefix="matharc-publication-fixture-") as directory:
        paths = write_publication_fixture(directory)
        report = audit_publication(
            paths.workspace,
            paths.bundle,
            latex=paths.latex,
            claim_map=paths.claim_map,
            abstract=paths.abstract,
        )

    if output is not None:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "fixture_kind": FIXTURE_KIND,
            "scope": "technical publication preflight wiring only",
            "authorizes_real_publication": False,
            "audit": report.to_dict(),
        }
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="artifacts/ci/publication-audit-fixture.json",
        help="machine-readable fixture result (default: %(default)s)",
    )
    args = parser.parse_args(argv)
    report = run_fixture(args.output)
    print(json.dumps({"fixture_kind": FIXTURE_KIND, "audit": report.to_dict()}, ensure_ascii=False))
    if not report.valid:
        print("publication technical-preflight fixture: FAIL")
        return 1
    print(
        "publication technical-preflight fixture: PASS "
        "(fixture only; no real-paper or publication authorization)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
