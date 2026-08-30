from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any, Mapping


def _available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _module_version(module: str) -> str | None:
    if not _available(module):
        return None
    loaded = __import__(module)
    if module == "z3":
        get_version = getattr(loaded, "get_version_string", None)
        if callable(get_version):
            return str(get_version())
    for attribute in ("__version__", "VERSION"):
        value = getattr(loaded, attribute, None)
        if value is not None and not callable(value):
            return str(value)
    return "available"


def capability_snapshot() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "matharc_importable": _available("matharc"),
        "mypy_available": _available("mypy"),
        "sympy_available": _available("sympy"),
        "sympy_version": _module_version("sympy"),
        "z3_available": _available("z3"),
        "z3_version": _module_version("z3"),
    }


def evaluate_capabilities(
    snapshot: Mapping[str, Any], *, require_formal: bool
) -> tuple[str, tuple[str, ...]]:
    """Return PASS/DEGRADED/FAIL without depending on the host environment."""

    failures: list[str] = []
    if not bool(snapshot.get("matharc_importable")):
        failures.append("matharc is not importable from this checkout")
    if not bool(snapshot.get("mypy_available")):
        failures.append("mypy is unavailable; run `make bootstrap` or `make bootstrap-full`")
    if require_formal:
        if not bool(snapshot.get("sympy_available")):
            failures.append("sympy is unavailable; authoritative CI requires the formal extra")
        if not bool(snapshot.get("z3_available")):
            failures.append("z3 is unavailable; authoritative CI requires the formal extra")

    if failures:
        return "FAIL", tuple(failures)
    if not bool(snapshot.get("z3_available")):
        return "DEGRADED", ()
    return "PASS", ()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-formal", action="store_true")
    parser.add_argument(
        "--output",
        default="artifacts/ci/capabilities.json",
        help="machine-readable capability record",
    )
    args = parser.parse_args(argv)

    snapshot = capability_snapshot()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=== MathArc Gate 0 capability preflight ===")
    for key in sorted(snapshot):
        print(f"{key}: {snapshot[key]}")

    status, failures = evaluate_capabilities(snapshot, require_formal=args.require_formal)
    if status == "FAIL":
        print("Gate 0 preflight: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 2
    if status == "DEGRADED":
        print(
            "Gate 0 preflight: DEGRADED (z3 unavailable; `make ci` may skip SMT tests and "
            "must not be cited as authoritative green)."
        )
        return 0

    print("Gate 0 preflight: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
