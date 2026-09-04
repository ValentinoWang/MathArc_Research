"""Fail-closed ownership boundary for the native MathArc runtime.

The governance/Harness tree is intentionally outside the product runtime.  This
module is dependency-free so it can run in a clean deployment image.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path

RUNTIME_ROOTS = ("matharc/v02/runtime/",)
RUNTIME_FILES = {
    "matharc/v02/trace.py",
    "scripts/check_runtime_ownership.py",
    "scripts/check_runtime_dependency_allowlist.py",
}
TEST_PREFIXES = ("tests/test_runtime_",)
DEPLOY_PREFIXES = ("deploy/",)
FORBIDDEN_PREFIXES = (
    "develop/",
    ".agents/",
    ".harness/",
    "agents-results/",
    ".codex/",
)
OWNERSHIP_ALLOWLIST = frozenset((*RUNTIME_FILES, *RUNTIME_ROOTS, *TEST_PREFIXES, *DEPLOY_PREFIXES))
RUNTIME_OWNERSHIP = {
    "product_runtime": ("matharc/v02/runtime/", "matharc/v02/trace.py"),
    "runtime_guards": ("scripts/check_runtime_ownership.py", "scripts/check_runtime_dependency_allowlist.py"),
    "deployment": ("deploy/",),
    "tests": ("tests/test_runtime_",),
    "governance_excluded": FORBIDDEN_PREFIXES,
}


def normalize(path: str | Path, root: str | Path | None = None) -> str:
    # Always resolve against a concrete root before classifying.  Without
    # this, a lexical ``runtime/../develop`` path could bypass the forbidden
    # prefixes, and symlinked files could be classified by their link name.
    root_path = Path(root or Path.cwd()).resolve()
    value = Path(path)
    if not value.is_absolute():
        value = root_path / value
    value = value.resolve(strict=False)
    try:
        return value.relative_to(root_path).as_posix()
    except ValueError:
        return value.as_posix()


def is_runtime_owned(path: str | Path, *, root: str | Path | None = None) -> bool:
    rel = normalize(path, root)
    if rel.startswith(FORBIDDEN_PREFIXES):
        return False
    return (
        rel in RUNTIME_FILES
        or rel.startswith(RUNTIME_ROOTS)
        or rel.startswith(TEST_PREFIXES)
        or rel.startswith(DEPLOY_PREFIXES)
    )


def check_runtime_ownership(
    paths: Iterable[str | Path], *, root: str | Path | None = None
) -> dict[str, object]:
    checked = [normalize(path, root) for path in paths]
    violations = [path for path in checked if not is_runtime_owned(path)]
    return {
        "valid": not violations,
        "checked": checked,
        "violations": violations,
        "allowed_roots": [*RUNTIME_ROOTS, *TEST_PREFIXES, *DEPLOY_PREFIXES],
        "forbidden_roots": list(FORBIDDEN_PREFIXES),
    }


def validate(paths: Iterable[str | Path], *, root: str | Path | None = None) -> tuple[str, ...]:
    """Script-style API used by static tests and other guards."""
    result = check_runtime_ownership(paths, root=root)
    return tuple(f"runtime ownership violation: {path}" for path in result["violations"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="paths to classify")
    parser.add_argument("--root", type=Path, help="repository root")
    args = parser.parse_args(argv)
    result = check_runtime_ownership(args.paths, root=args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
