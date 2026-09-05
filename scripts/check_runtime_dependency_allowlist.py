"""Check that product-runtime Python imports stay on a small allowlist."""
from __future__ import annotations

import argparse
import ast
import json
from collections.abc import Iterable
from pathlib import Path

# Keep this explicit: adding a third-party runtime dependency requires a
# deliberate review and a new entry here.
STDLIB_ALLOWLIST = frozenset({
    "__future__", "argparse", "ast", "asyncio", "collections", "contextlib", "copy", "dataclasses",
    "datetime", "enum", "fcntl", "functools", "hashlib", "hmac", "http", "itertools",
    "json", "logging", "math", "os", "pathlib", "re", "shutil", "sqlite3", "sys", "types",
    "tempfile", "time", "traceback", "typing", "uuid", "zipfile", "concurrent", "inspect", "threading",
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


_PATH_ISSUES = {
    "missing": "<missing path>",
    "symlink": "<symlink path>",
    "hardlink": "<hardlink path>",
    "regular": "<not a regular file>",
    "unreadable": "<unreadable path>",
    "syntax": "<syntax error>",
}


def _path_issue(path: Path) -> str | None:
    """Return a conservative filesystem failure reason for a scan target."""
    try:
        if path.is_symlink():
            return _PATH_ISSUES["symlink"]
        if not path.exists():
            return _PATH_ISSUES["missing"]
        if not path.is_file():
            return _PATH_ISSUES["regular"]
        if path.stat().st_nlink > 1:
            return _PATH_ISSUES["hardlink"]
    except OSError:
        return _PATH_ISSUES["unreadable"]
    return None


def _resolve_module_targets(module: str, roots: Iterable[Path]) -> list[Path]:
    """Resolve a module plus package initializers executed on its import."""
    parts = tuple(part for part in module.split(".") if part)
    if not parts:
        return []
    for root in roots:
        package = root
        initializers: list[Path] = []
        for part in parts[:-1]:
            package /= part
            initializer = package / "__init__.py"
            if initializer.exists() or initializer.is_symlink():
                initializers.append(initializer)
        stem = root.joinpath(*parts)
        candidates = (*initializers, stem.with_suffix(".py"), stem / "__init__.py")
        existing = [candidate for candidate in candidates if candidate.exists() or candidate.is_symlink()]
        if existing:
            return existing
    return []


def _first_existing(candidates: Iterable[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists() or candidate.is_symlink():
            return candidate
    return None


def _relative_candidates(source: Path, level: int, module: str | None) -> Iterable[Path]:
    base = source.parent
    for _ in range(max(level - 1, 0)):
        base = base.parent
    if module:
        stem = base.joinpath(*module.split("."))
        return (stem.with_suffix(".py"), stem / "__init__.py")
    return ()


def _local_import_targets(
    tree: ast.AST,
    source: Path,
    roots: Iterable[Path],
    local_roots: set[str],
) -> Iterable[tuple[str, Path | None]]:
    """Yield local import names and their source files for graph traversal."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in local_roots:
                    targets = _resolve_module_targets(alias.name, roots)
                    if targets:
                        for target in targets:
                            yield alias.name, target
                    else:
                        yield alias.name, None
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if not node.module:
                    continue
                root = node.module.split(".", 1)[0]
                if root in local_roots:
                    targets = _resolve_module_targets(node.module, roots)
                    if targets:
                        for target in targets:
                            yield node.module, target
                    else:
                        yield node.module, None
                continue

            # A relative import is resolved from the importing file, so it
            # cannot be reduced to a top-level root without losing its target.
            if node.module:
                target = ".".join(("" for _ in range(node.level))) + node.module
                candidates = _relative_candidates(source, node.level, node.module)
                yield target, _first_existing(candidates)
            else:
                for alias in node.names:
                    target = ".".join(("" for _ in range(node.level))) + alias.name
                    candidates = _relative_candidates(source, node.level, alias.name)
                    yield target, _first_existing(candidates)


def _input_files(path: Path) -> tuple[list[Path], dict[str, list[str]]]:
    """Collect Python files while surfacing missing and symlinked inputs."""
    issues: dict[str, list[str]] = {}
    if path.is_symlink():
        return [], {str(path): [_PATH_ISSUES["symlink"]]}
    if not path.exists():
        return [], {str(path): [_PATH_ISSUES["missing"]]}
    if path.is_file():
        return [path], {}
    if not path.is_dir():
        return [], {str(path): [_PATH_ISSUES["regular"]]}

    files: list[Path] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.is_symlink():
            issues[str(candidate)] = [_PATH_ISSUES["symlink"]]
        elif candidate.is_file() and candidate.suffix == ".py":
            files.append(candidate)
    return files, issues


def check_dependencies(
    paths: Iterable[str | Path], *, allowed: Iterable[str] = ()
) -> dict[str, object]:
    # Keep the reviewed set explicit.  ``sys.stdlib_module_names`` is useful
    # for discovery, but unioning it here would silently authorize modules
    # such as subprocess, socket, pickle, and importlib.
    permitted = set(STDLIB_ALLOWLIST) | set(LOCAL_ALLOWLIST) | set(allowed)
    files: dict[str, list[str]] = {}
    unknown: dict[str, list[str]] = {}
    queue: list[Path] = []
    search_roots: list[Path] = []
    for raw in paths:
        path = Path(raw)
        input_files, initial_issues = _input_files(path)
        queue.extend(input_files)
        for name, issues in initial_issues.items():
            unknown[name] = sorted(set(issues))
        anchor = path if path.is_dir() else path.parent
        try:
            # Retain the caller's lexical spelling for result keys (notably
            # macOS ``/var`` versus ``/private/var``), while path validation
            # still resolves identities before accepting a file.
            anchor = anchor.absolute()
            search_roots.extend((anchor, *anchor.parents))
        except OSError:
            pass

    # Keep traversal bounded to files reachable from the explicit inputs.
    visited: set[Path] = set()
    # ``--allow`` may intentionally authorize a third-party root that has no
    # source file in this checkout.  Only the project-owned ``matharc`` root
    # participates in local transitive traversal.
    local_roots = set(LOCAL_ALLOWLIST)
    while queue:
        path = queue.pop(0)
        key = path.resolve(strict=False)
        if key in visited:
            continue
        visited.add(key)
        name = str(path)
        issue = _path_issue(path)
        if issue:
            unknown.setdefault(name, []).append(issue)
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=name)
        except (OSError, UnicodeError):
            files[name] = []
            unknown.setdefault(name, []).append(_PATH_ISSUES["unreadable"])
            continue
        except SyntaxError:
            files[name] = []
            unknown.setdefault(name, []).append(_PATH_ISSUES["syntax"])
            continue

        roots = sorted(imported_roots(source, name))
        files[name] = roots
        bad = [root for root in roots if root not in permitted]
        if bad:
            unknown.setdefault(name, []).extend(bad)

        for module, target in _local_import_targets(tree, path, search_roots, local_roots):
            if target is None:
                root = module.lstrip(".").split(".", 1)[0]
                # An approved project namespace may be supplied by an
                # installed distribution.  Fail only when that namespace is
                # present beside an explicit input but the imported module is
                # missing; otherwise it is an opaque, allowlisted dependency.
                if root and any((candidate / root).exists() for candidate in search_roots):
                    unknown.setdefault(name, []).append(module)
            else:
                queue.append(target)

    unknown = {name: sorted(set(dependencies)) for name, dependencies in unknown.items()}
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
