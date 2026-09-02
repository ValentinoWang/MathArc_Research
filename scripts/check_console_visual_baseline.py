#!/usr/bin/env python3
"""Fail closed when the U1 console visual baseline contract drifts.

This is a source-level guard.  It does not claim that screenshots, browser
captures, or human visual review exist; those remain unavailable while U1 is
planned and inactive.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


TOKEN_TABLE_SHA256 = "c45b37e6f8e8da0bfb837efef0209c560109a9a169e2b3a40d1bb5ebc71fb2fb"
CLASS_COUNT = 235
CLASS_LIST_SHA256 = "7843c36a73d65c6e8be464863c0a46c17aef63944a0e25c1b10de63334938dcc"
LIGHT_ONLY_TOKENS = frozenset({"--serif", "--sans", "--mono", "--topbar-h"})
SHELL_CLASSES = frozenset(
    {
        "topbar",
        "brand",
        "planes",
        "nowtask",
        "miniprog",
        "who",
        "shell",
        "rail",
        "main",
        "side",
        "nav",
        "railhead",
        "card",
    }
)
REQUIRED_IDS = frozenset({"console-provenance", "view-data-boundary"})
ALLOWED_BUILD_STATUSES = frozenset({"已落地", "待接线", "部分待建", "需新建", "已推迟"})
EXPECTED_BUILD_STATUS_COUNTS = {
    "已落地": 18,
    "待接线": 3,
    "部分待建": 4,
    "需新建": 5,
    "已推迟": 2,
}
EXPECTED_VIEWPORT_LAYOUTS = {
    "1240x1080": "two-column",
    "1366x1080": "three-column",
    "1440x1080": "three-column",
    "1536x1080": "three-column",
    "1728x1080": "three-column",
    "1920x1080": "three-column",
    "390x844": "single-column",
    "820x1180": "single-column",
}
STYLE_PATTERN = re.compile(r"<style>(.*?)</style>", re.DOTALL | re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"(--[A-Za-z0-9-]+)\s*:\s*([^;{}]+)")
CLASS_PATTERN = re.compile(r"\.([A-Za-z_][\w-]*)")


class VisualBaselineError(ValueError):
    """Raised when a U1 static visual-baseline invariant is not satisfied."""


def _read(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise VisualBaselineError(f"cannot read {label}: {path}: {exc}") from exc


def _block(source: str, selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{", source)
    if match is None:
        raise VisualBaselineError(f"missing CSS block: {selector}")
    depth = 1
    index = match.end()
    while index < len(source) and depth:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1
    if depth:
        raise VisualBaselineError(f"unterminated CSS block: {selector}")
    return source[match.end() : index - 1]


def _tokens(block: str) -> dict[str, str]:
    tokens: dict[str, str] = {}
    for name, value in TOKEN_PATTERN.findall(block):
        if name in tokens:
            raise VisualBaselineError(f"duplicate token declaration in one mode: {name}")
        tokens[name] = value.strip()
    return tokens


def _stylesheet(page: str) -> str:
    matches = STYLE_PATTERN.findall(page)
    if len(matches) != 1:
        raise VisualBaselineError(f"expected exactly one inline stylesheet, found {len(matches)}")
    return matches[0]


def _class_names(stylesheet: str) -> set[str]:
    # The frozen U1 extraction is line-oriented.  Restricting it to selector
    # lines prevents decimal CSS values such as `.08` from becoming classes.
    selector_lines = "\n".join(line for line in stylesheet.splitlines() if "{" in line)
    return set(CLASS_PATTERN.findall(selector_lines))


def _parse_status_rows(contract: str) -> list[list[str]]:
    marker = "#### 32 个视图的接线事实"
    end_marker = "建设状态分布："
    try:
        section = contract.split(marker, 1)[1].split(end_marker, 1)[0]
    except IndexError as exc:
        raise VisualBaselineError("missing U1 32-view construction-status table") from exc

    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 8:
            raise VisualBaselineError(f"malformed U1 construction-status row: {line}")
        rows.append(cells)
    if len(rows) != 32:
        raise VisualBaselineError(f"U1 construction-status table must contain 32 views, found {len(rows)}")
    return rows


def _validate_tokens(stylesheet: str, failures: list[str]) -> None:
    try:
        light = _tokens(_block(stylesheet, ":root"))
        system_dark = _tokens(
            _block(_block(stylesheet, "@media (prefers-color-scheme:dark)"), ':root:not([data-theme="light"])')
        )
        explicit_dark = _tokens(_block(stylesheet, ':root[data-theme="dark"]'))
    except VisualBaselineError as exc:
        failures.append(str(exc))
        return

    if len(light) != 30:
        failures.append(f"light token mode must define 30 tokens, found {len(light)}")
    if len(system_dark) != 26 or len(explicit_dark) != 26:
        failures.append(
            "both dark token modes must define 26 tokens: "
            f"system={len(system_dark)} explicit={len(explicit_dark)}"
        )
    if set(light) - set(system_dark) != LIGHT_ONLY_TOKENS or set(light) - set(explicit_dark) != LIGHT_ONLY_TOKENS:
        failures.append("dark token modes must omit only the four documented inherited light tokens")
    if system_dark != explicit_dark:
        failures.append("system-dark and explicit-dark token modes differ")

    rows = "\n".join(
        "|".join((name, light.get(name, ""), system_dark.get(name, ""), explicit_dark.get(name, "")))
        for name in sorted(light)
    )
    observed = hashlib.sha256(rows.encode("utf-8")).hexdigest()
    if observed != TOKEN_TABLE_SHA256:
        failures.append(f"token table digest drift: expected {TOKEN_TABLE_SHA256}, observed {observed}")


def _validate_shell(stylesheet: str, page: str, failures: list[str]) -> None:
    classes = _class_names(stylesheet)
    missing_classes = sorted(SHELL_CLASSES - classes)
    if missing_classes:
        failures.append(f"missing application-shell classes: {missing_classes}")
    missing_ids = sorted(identifier for identifier in REQUIRED_IDS if not re.search(rf"\bid\s*=\s*[\"']{re.escape(identifier)}[\"']", page))
    if missing_ids:
        failures.append(f"missing application-shell identity elements: {missing_ids}")

    if len(classes) != CLASS_COUNT:
        failures.append(f"class baseline count drift: expected {CLASS_COUNT}, observed {len(classes)}")
    observed = hashlib.sha256("\n".join(sorted(classes)).encode("utf-8")).hexdigest()
    if observed != CLASS_LIST_SHA256:
        failures.append(f"class baseline digest drift: expected {CLASS_LIST_SHA256}, observed {observed}")

    media_count = len(re.findall(r"@media\s*\(", stylesheet))
    if media_count != 14:
        failures.append(f"media-rule count drift: expected 14, observed {media_count}")
    for width, layout in EXPECTED_VIEWPORT_LAYOUTS.items():
        observed_layout = "three-column"
        numeric_width = int(width.split("x", 1)[0])
        if numeric_width <= 820:
            observed_layout = "single-column"
        elif numeric_width <= 1240:
            observed_layout = "two-column"
        if observed_layout != layout:
            failures.append(f"viewport layout mapping drift: {width} must be {layout}")
    for required_css in (
        "grid-template-columns:232px minmax(0,1fr) 300px",
        "@media (max-width:1240px)",
        "@media (max-width:820px)",
        "grid-template-columns:200px minmax(0,1fr)",
        "grid-template-columns:minmax(0,1fr)",
    ):
        if required_css not in stylesheet:
            failures.append(f"missing documented shell breakpoint rule: {required_css}")


def _validate_build_statuses(contract: str, blueprint: str, failures: list[str]) -> None:
    try:
        rows = _parse_status_rows(contract)
    except VisualBaselineError as exc:
        failures.append(str(exc))
        return

    view_ids = [row[0].strip("`") for row in rows]
    if len(set(view_ids)) != len(view_ids):
        failures.append("U1 construction-status table has duplicate view IDs")
    status_counts = {status: sum(row[-1] == status for row in rows) for status in ALLOWED_BUILD_STATUSES}
    invalid = sorted({row[-1] for row in rows} - ALLOWED_BUILD_STATUSES)
    if invalid:
        failures.append(f"U1 construction-status table has invalid statuses: {invalid}")
    if status_counts != EXPECTED_BUILD_STATUS_COUNTS:
        failures.append(
            "U1 construction-status distribution drift: "
            f"expected {EXPECTED_BUILD_STATUS_COUNTS}, observed {status_counts}"
        )
    for row in rows:
        if row[-1] == "已落地" and not row[5].startswith("有"):
            failures.append(f"implemented view lacks automated evidence: {row[0]}")

    for status in ALLOWED_BUILD_STATUSES:
        if status not in blueprint:
            failures.append(f"blueprint does not declare construction status vocabulary: {status}")


def validate_baseline(prototype_path: Path, blueprint_path: Path, contract_path: Path) -> tuple[str, ...]:
    """Return all contract failures, never treating partial input as a pass."""

    failures: list[str] = []
    try:
        page = _read(prototype_path, "console prototype")
        stylesheet = _stylesheet(page)
    except VisualBaselineError as exc:
        return (str(exc),)
    _validate_tokens(stylesheet, failures)
    _validate_shell(stylesheet, page, failures)
    try:
        blueprint = _read(blueprint_path, "console blueprint")
        contract = _read(contract_path, "U1 view contract")
    except VisualBaselineError as exc:
        failures.append(str(exc))
        return tuple(failures)
    _validate_build_statuses(contract, blueprint, failures)
    return tuple(failures)


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype", type=Path, default=root / "docs/prototypes/problem-intel-console.html")
    parser.add_argument("--blueprint", type=Path, default=root / "docs/prototypes/console-dev-blueprint.html")
    parser.add_argument(
        "--contract",
        type=Path,
        default=root / "agents-results/2026-08-31/problem-intelligence-plane/.ssot/view-sources/00-main.md",
    )
    args = parser.parse_args(argv)
    failures = validate_baseline(args.prototype, args.blueprint, args.contract)
    if failures:
        print("console visual baseline: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(
            "Repair: restore the U1 §9.13/§9.15 contract or update the approved baseline before activating U1.",
            file=sys.stderr,
        )
        return 1
    print("console visual baseline: PASS (U1 static contract only; no runtime visual evidence claimed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
