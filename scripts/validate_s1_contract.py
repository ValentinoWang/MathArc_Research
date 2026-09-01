"""Validate the S1 pre-acceptance paper dry-run contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DOSSIER_IDS = (
    "P-FRANKL-Q6",
    "P-ARXIV-2601-22401-COLLISION",
    "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS",
)
PAPER_DRY_RUN_COMMAND = (
    "python3 -m unittest -v "
    "tests.test_v02_problem_status.ProblemStatusTests."
    "test_three_paper_dry_run_fixtures_pin_exact_status_facts"
)
RUNTIME_VALIDATION_SCOPE = {
    "reserved_nodes": ["T1", "T2"],
    "allowed_operations": ["runtime-replay", "runtime-closure"],
    "s1_boundary": "S1 paper dry-run does not execute or accept T1/T2 runtime work",
}
FIXTURE_CONTRACT = (
    "agents-results/2026-08-31/problem-intelligence-plane/evidence/"
    "t2-fixtures/three-real-archives.json"
)


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _validate_dry_run(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label}.pre_acceptance_dry_run must be an object")
    if value.get("fixture_contract") != FIXTURE_CONTRACT:
        raise ValueError(f"{label} dry-run fixture contract is not the T2 contract")
    if value.get("dossier_fixture_ids") != list(DOSSIER_IDS):
        raise ValueError(f"{label} dry-run must pin the three dossier fixture IDs")
    if value.get("command") != PAPER_DRY_RUN_COMMAND:
        raise ValueError(f"{label} dry-run command drifted")
    if value.get("execution_mode") != "paper-only":
        raise ValueError(f"{label} dry-run must remain paper-only")


def validate(bundle_root: str | Path) -> None:
    """Fail closed when S1 generation/contract metadata loses its boundary."""

    root = Path(bundle_root)
    machine = root / ".ssot"
    planning = _object(machine / "planning-compiler.json")
    specs = [node for node in planning.get("nodes", []) if node.get("id") == "S1"]
    if len(specs) != 1:
        raise ValueError("planning compiler must define exactly one S1 node")
    node = _object(machine / "nodes/S1.json")
    execution = _object(machine / "execution-contracts/S1.json")
    for label, value in (
        ("planning compiler S1", specs[0]),
        ("machine S1 node", node),
        ("S1 execution contract", execution),
    ):
        _validate_dry_run(value.get("pre_acceptance_dry_run"), label)
    for label, value in (("machine S1 node", node), ("S1 execution contract", execution)):
        if value.get("runtime_validation_scope") != RUNTIME_VALIDATION_SCOPE:
            raise ValueError(f"{label} runtime validation scope drifted")
    t2 = _object(root / "evidence/t2-fixtures/three-real-archives.json")
    cases = t2.get("cases")
    if [case.get("problem_id") for case in cases or []] != list(DOSSIER_IDS):
        raise ValueError("T2 contract case order does not match S1 dossier IDs")
    fixture = root.parent.parent.parent / FIXTURE_CONTRACT
    if not fixture.is_file():
        raise ValueError(f"S1 dry-run fixture contract is missing: {fixture}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bundle-root",
        default="agents-results/2026-08-31/problem-intelligence-plane",
    )
    args = parser.parse_args(argv)
    try:
        validate(args.bundle_root)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"S1 contract validation: FAIL: {exc}")
        return 1
    print("S1 contract validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
