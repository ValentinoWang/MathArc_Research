from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(project_root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(project_root), *args], text=True).strip()


def _run_and_log(project_root: Path, command: list[str], log_path: Path) -> int:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(
        command,
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(result.stdout, encoding="utf-8")
    print(result.stdout, end="")
    return result.returncode


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object: {path}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="override YYYY-MM-DD used in the baseline filename")
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[1]
    dirty = _git(project_root, "status", "--porcelain", "--", ".")
    if dirty:
        print(
            "G0-c baseline generation requires a clean committed project tree because "
            "clean-ci archives HEAD. Commit/stash first."
        )
        print(dirty)
        return 2

    head = _git(project_root, "rev-parse", "HEAD")
    short = head[:12]
    stamp = args.date or dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()
    ci_log = project_root / "artifacts/ci/ci-full.log"
    clean_log = project_root / "artifacts/ci/clean-ci.log"

    # Preserve the interpreter selected for the baseline run.  Without this
    # explicit override, Make falls back to the host default (often a Python
    # without the formal extras), making a valid prepared environment fail.
    python_override = f"PYTHON={sys.executable}"
    ci_exit = _run_and_log(project_root, ["make", "ci-full", python_override], ci_log)
    if ci_exit != 0:
        print("G0-c baseline NOT written: make ci-full failed.")
        return ci_exit
    clean_exit = _run_and_log(project_root, ["make", "clean-ci", python_override], clean_log)
    if clean_exit != 0:
        print("G0-c baseline NOT written: make clean-ci failed.")
        return clean_exit

    summary_path = project_root / "artifacts/ci/unittest-summary.json"
    capabilities_path = project_root / "artifacts/ci/capabilities.json"
    summary = _load_json(summary_path)
    capabilities = _load_json(capabilities_path)

    artifact_paths = [
        project_root / "artifacts/v0.1-acceptance.json",
        project_root / "artifacts/v0.2-acceptance.json",
        project_root / "artifacts/frankl-q6-two-small-python.json",
        summary_path,
        capabilities_path,
    ]
    smoke_dir = project_root / "docs/baselines/smoke"
    if smoke_dir.exists():
        artifact_paths.extend(sorted(smoke_dir.glob("*.json")))

    artifact_rows: list[str] = []
    for path in artifact_paths:
        if path.exists():
            artifact_rows.append(
                f"| `{path.relative_to(project_root).as_posix()}` | `{_sha256(path)}` | {path.stat().st_size} |"
            )
        else:
            artifact_rows.append(
                f"| `{path.relative_to(project_root).as_posix()}` | MISSING | 0 |"
            )

    mypy_file_count = len(list((project_root / "matharc/v02").rglob("*.py")))
    target = project_root / "docs/baselines" / f"{stamp}-{short}-local-ci.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            [
                f"# MathArc G0-c authoritative local baseline — {stamp}",
                "",
                f"- commit: `{head}`",
                "- authority: `make ci-full` + `make clean-ci`",
                "- clean-check source: committed `HEAD:.` tree + registry/workflow authorities",
                "- clean-check bootstrap: fresh venv + `.[research,dev,formal]`",
                f"- Python: `{capabilities.get('python')}`",
                f"- z3: `{capabilities.get('z3_version')}`",
                f"- sympy: `{capabilities.get('sympy_version')}`",
                f"- mypy source-file count (`matharc/v02/**/*.py`): **{mypy_file_count}**",
                f"- unittest discovered/run: **{summary.get('tests_discovered')} / {summary.get('tests_run')}**",
                f"- unittest skipped: **{summary.get('skipped')}**",
                f"- SMT discovered/executed/skipped: **{summary.get('smt_tests_discovered')} / {summary.get('smt_tests_executed')} / {summary.get('smt_tests_skipped')}**",
                f"- published Claude smoke artifacts: **{len(list(smoke_dir.glob('*.json'))) if smoke_dir.exists() else 0}**",
                f"- `make ci-full` exit: **{ci_exit}**",
                f"- `make clean-ci` exit: **{clean_exit}**",
                "",
                "## Content-addressed milestone artifacts",
                "",
                "| Artifact | SHA-256 | Bytes |",
                "|---|---|---:|",
                *artifact_rows,
                "",
                "## Logs",
                "",
                "The full local logs are generated under `artifacts/ci/` and are intentionally not treated as a substitute for the committed summary/digests above.",
                "",
                "## Claim boundary",
                "",
                "This baseline proves the committed engineering gate reproduced on this machine and in a clean archived checkout. A published Claude smoke row, when present, proves only a sanitized synthetic proposal-only model turn. Neither is evidence that any open mathematical conjecture is solved.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"G0-c baseline written: {target}")
    print("Commit this file with the milestone; do not hand-edit test/skip counts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
