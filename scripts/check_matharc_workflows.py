from __future__ import annotations

from pathlib import Path

GENERIC_WORKFLOW = "matharc-research-ci.yml"
HISTORICAL_MANUAL_WORKFLOWS = frozenset(
    {
        "matharc-finalize-v01.yml",
        "matharc-v02-bootstrap.yml",
        "matharc-v02-materialize.yml",
    }
)
EXPECTED_WORKFLOWS = HISTORICAL_MANUAL_WORKFLOWS | {GENERIC_WORKFLOW}
AUTOMATIC_EVENTS = frozenset({"push", "pull_request"})


def _declared_events(path: Path) -> frozenset[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("on:") + 1
    except ValueError as exc:
        raise ValueError(f"workflow has no top-level on block: {path}") from exc

    events: set[str] = set()
    for line in lines[start:]:
        if line and not line[0].isspace():
            break
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            events.add(line.strip()[:-1])
    return frozenset(events)


def _push_branches(path: Path) -> tuple[str, ...]:
    branches: list[str] = []
    in_push = False
    in_branches = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "  push:":
            in_push = True
            in_branches = False
            continue
        if in_push and line.startswith("  ") and not line.startswith("    "):
            break
        if in_push and line == "    branches:":
            in_branches = True
            continue
        if in_branches and line.startswith("      - "):
            branches.append(line.removeprefix("      - ").strip('"'))
            continue
        if in_branches and line and not line.startswith("      "):
            break
    return tuple(branches)


def evaluate_policy(workflows_dir: Path) -> tuple[str, ...]:
    paths = [
        *workflows_dir.glob("matharc-*.yml"),
        *workflows_dir.glob("matharc-*.yaml"),
    ]
    matharc_workflows = {path.name: path for path in paths}
    failures: list[str] = []
    actual_names = frozenset(matharc_workflows)
    if actual_names != EXPECTED_WORKFLOWS:
        missing = sorted(EXPECTED_WORKFLOWS - actual_names)
        unexpected = sorted(actual_names - EXPECTED_WORKFLOWS)
        failures.append(f"MathArc workflow set differs: missing={missing} unexpected={unexpected}")

    automatic: set[str] = set()
    for name, path in matharc_workflows.items():
        events = _declared_events(path)
        if events & AUTOMATIC_EVENTS:
            automatic.add(name)
        if name in HISTORICAL_MANUAL_WORKFLOWS and events != {"workflow_dispatch"}:
            failures.append(f"historical workflow must be manual-only: {name} events={sorted(events)}")

    if automatic != {GENERIC_WORKFLOW}:
        failures.append(
            f"automatic MathArc workflows must be only {GENERIC_WORKFLOW}: {sorted(automatic)}"
        )

    generic = matharc_workflows.get(GENERIC_WORKFLOW)
    if generic is not None:
        branches = _push_branches(generic)
        if branches != ("main",):
            failures.append(f"{GENERIC_WORKFLOW} push branches must be exactly main: {branches}")
        if "make ci-full" not in generic.read_text(encoding="utf-8"):
            failures.append(f"{GENERIC_WORKFLOW} must invoke make ci-full")
    return tuple(failures)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    workflows_dir = project_root.parents[1] / ".github" / "workflows"
    failures = evaluate_policy(workflows_dir)
    if failures:
        print("MATHARC WORKFLOW POLICY: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MATHARC WORKFLOW POLICY: PASS")
    print("automatic: matharc-research-ci.yml -> make ci-full")
    print("historical workflows: manual-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
