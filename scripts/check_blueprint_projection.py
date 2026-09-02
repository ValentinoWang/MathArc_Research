#!/usr/bin/env python3
"""Fail closed when the U2 view-wiring table and blueprint status projection drift.

Guard card (candidate, fast, project scope): console projection mapping drift.
The authoritative rows are §9.15 in the SSOT view source.  Blueprint §5 must
declare one ``data-view-id`` row per source row so status comparisons are not
based on ambiguous Chinese display labels.  Repair the blueprint mapping and
§9.15 together; do not infer a runtime wire from backend capability alone.
"""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/.ssot/view-sources/00-main.md"
DEFAULT_BLUEPRINT = ROOT / "docs/prototypes/console-dev-blueprint.html"
EXPECTED_VIEW_COUNT = 32
STATUSES = ("已落地", "待接线", "部分待建", "需新建", "已推迟")


def _section(source: str, start: str, end: str) -> str:
    try:
        return source[source.index(start) : source.index(end, source.index(start))]
    except ValueError as exc:
        raise ValueError(f"missing contract section between {start!r} and {end!r}") from exc


def _status(value: str) -> str | None:
    value = re.sub(r"\s+", "", value)
    return next((status for status in STATUSES if status in value), None)


def documented_views(contract_source: str) -> dict[str, str]:
    section = _section(contract_source, "#### 32 个视图的接线事实", "建设状态分布")
    views: dict[str, str] = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 10 or not cells[1].startswith("`"):
            continue
        view_match = re.fullmatch(r"`([^`]+)`", cells[1])
        status = _status(cells[8])
        if view_match is None or status is None:
            continue
        view = view_match.group(1)
        if view in views:
            raise ValueError(f"duplicate documented view {view!r}")
        views[view] = status
    return views


class _BlueprintRows(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[tuple[str | None, list[str]]] = []
        self._view_id: str | None = None
        self._depth = 0
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._view_id = dict(attrs).get("data-view-id")
            self._depth = 1
            self._text = []
        elif self._depth:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._depth:
            return
        self._depth -= 1
        if tag == "tr" and self._depth == 0:
            self.rows.append((self._view_id, self._text))

    def handle_data(self, data: str) -> None:
        if self._depth:
            self._text.append(data)


def blueprint_views(blueprint_source: str) -> dict[str, str]:
    section = _section(blueprint_source, '<section id="s5">', '<section id="s6">')
    parser = _BlueprintRows()
    parser.feed(section)
    rows: dict[str, str] = {}
    for view_id, text in parser.rows:
        if view_id is None:
            continue
        if view_id in rows:
            raise ValueError(f"duplicate blueprint data-view-id {view_id!r}")
        status = _status("".join(text))
        if status is None:
            raise ValueError(f"blueprint row {view_id!r} has no recognized construction status")
        rows[view_id] = status
    return rows


def validate(contract_source: str, blueprint_source: str) -> tuple[str, ...]:
    try:
        documented = documented_views(contract_source)
    except ValueError as exc:
        return (f"blueprint-projection contract: {exc}; repair §9.15 before running U2.",)
    failures: list[str] = []
    if len(documented) != EXPECTED_VIEW_COUNT:
        failures.append(
            f"blueprint-projection contract: expected {EXPECTED_VIEW_COUNT} §9.15 rows, found {len(documented)}; repair the source table."
        )
    try:
        blueprint = blueprint_views(blueprint_source)
    except ValueError as exc:
        return tuple(failures + [f"blueprint-projection mapping: {exc}; add one data-view-id row per §9.15 view."])
    missing = sorted(set(documented) - set(blueprint))
    extra = sorted(set(blueprint) - set(documented))
    if missing or extra:
        failures.append(
            f"blueprint-projection mapping: missing={missing} extra={extra}; add one data-view-id row per §9.15 view."
        )
    for view in sorted(set(documented) & set(blueprint)):
        if documented[view] != blueprint[view]:
            failures.append(
                f"blueprint-projection status: {view} is §9.15={documented[view]} but blueprint={blueprint[view]}; repair the §5 projection."
            )
    return tuple(failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--blueprint", type=Path, default=DEFAULT_BLUEPRINT)
    args = parser.parse_args(argv)
    try:
        failures = validate(args.contract.read_text(encoding="utf-8"), args.blueprint.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        print(f"blueprint projection: FAIL: {exc}")
        return 1
    if failures:
        print("blueprint projection: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("blueprint projection: PASS (32 documented view mappings match §5)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
