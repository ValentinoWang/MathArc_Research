"""Check that product-runtime Python imports stay on a small allowlist."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Iterable
from pathlib import Path

# Keep this explicit: adding a third-party runtime dependency requires a
# deliberate review and a new entry here.
STDLIB_ALLOWLIST = frozenset({
    "__future__", "argparse", "ast", "asyncio", "collections", "contextlib", "copy", "dataclasses",
    "datetime", "enum", "functools", "hashlib", "hmac", "http", "itertools",
    "json", "logging", "math", "os", "pathlib", "re", "shutil", "sqlite3", "sys", "types",
    "tempfile", "time", "traceback", "typing", "uuid", "zipfile",
})
LOCAL_ALLOWLIST = frozenset({"matharc"})
ALLOWED_RUNTIME_DEPENDENCIES = frozenset((*STDLIB_ALLOWLIST, *LOCAL_ALLOWLIST))
ALLOWLIST = ALLOWED_RUNTIME_DEPENDENCIES


def imported_roots(source: str, filename: str = "<runtime>") -> set[str]:
    tree = ast.parse(source, filename=filename)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def check_dependencies(
    paths: Iterable[str | Path], *, allowed: Iterable[str] = ()
) -> dict[str, object]:
    # ``stdlib_module_names`` is the interpreter's canonical list (available
    # on supported Python versions); the explicit set documents the intended
    # baseline and keeps this guard usable on older interpreters.
    interpreter_stdlib = set(getattr(sys, "stdlib_module_names", ()))
    permitted = set(STDLIB_ALLOWLIST) | interpreter_stdlib | set(LOCAL_ALLOWLIST) | set(allowed)
    files: dict[str, list[str]] = {}
    unknown: dict[str, list[str]] = {}
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            nested = check_dependencies(sorted(path.rglob("*.py")), allowed=allowed)
            files.update(nested["files"])
            unknown.update(nested["unknown"])
            continue
        name = str(path)
        roots = sorted(imported_roots(path.read_text(encoding="utf-8"), name))
        files[name] = roots
        bad = [root for root in roots if root not in permitted and root not in sys.builtin_module_names]
        if bad:
            unknown[name] = bad
    return {"valid": not unknown, "allowed": sorted(permitted), "files": files, "unknown": unknown}


def validate(paths: Iterable[str | Path], *, allowed: Iterable[str] = ()) -> tuple[str, ...]:
    result = check_dependencies(paths, allowed=allowed)
    return tuple(
        f"unknown runtime dependency in {filename}: {dependency}"
        for filename, dependencies in result["unknown"].items()
        for dependency in dependencies
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--allow", action="append", default=[])
    args = parser.parse_args(argv)
    result = check_dependencies(args.paths, allowed=args.allow)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
