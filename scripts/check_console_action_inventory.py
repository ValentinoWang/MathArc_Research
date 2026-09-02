#!/usr/bin/env python3
"""Fail closed when the U2 console action contract drifts from emitted actions.

Guard card (candidate, fast, project scope): console action-inventory drift.
The source inventory is section 9.14 of the problem-intelligence-plan view.
This guard deliberately parses reachable dynamic templates as well as literal
attributes; a selector such as ``[data-act=\"signin\"]`` is not an emission.
Repair: update the §9.14 inventory and the prototype dispatcher together, or
remove/enable an unreachable dynamic template before promoting U2.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/.ssot/view-sources/00-main.md"
DEFAULT_PROTOTYPE = ROOT / "docs/prototypes/problem-intel-console.html"
EXPECTED_ACTION_COUNT = 57
ACTION_CLASSES = frozenset({"local-ui-state", "navigate", "simulated-write", "wired-read", "wired-write"})


def _section(source: str, start: str, end: str) -> str:
    try:
        return source[source.index(start) : source.index(end, source.index(start))]
    except ValueError as exc:
        raise ValueError(f"missing contract section between {start!r} and {end!r}") from exc


def documented_actions(contract_source: str) -> dict[str, tuple[str, str]]:
    section = _section(contract_source, "#### 57 个动作", "#### 异常")
    actions: dict[str, tuple[str, str]] = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 6 or not cells[1].startswith("`"):
            continue
        action_match = re.fullmatch(r"`([^`]+)`", cells[1])
        class_match = re.fullmatch(r"`([^`]+)`", cells[4])
        if action_match is None or class_match is None:
            continue
        action = action_match.group(1)
        if action in actions:
            raise ValueError(f"duplicate documented action {action!r}")
        actions[action] = (cells[2], class_match.group(1))
    return actions


def dispatcher_actions(prototype_source: str) -> set[str]:
    return set(re.findall(r'(?:else )?if\(a==="([^"]+)"\)', prototype_source))


def literal_emissions(prototype_source: str) -> set[str]:
    # The negative lookbehind excludes selector strings like '[data-act="signin"]'.
    return {
        match.group(1)
        for match in re.finditer(r'(?<!\[)data-act="([^"$]+)"', prototype_source)
    }


def _balanced_call(source: str, start: int) -> str | None:
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(source)):
        character = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in "'\"`":
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return source[start + 1 : index]
    return None


def _final_string_argument(arguments: str) -> str | None:
    matches = re.findall(r'(["\'])([A-Za-z0-9_-]+)\1', arguments)
    return matches[-1][1] if matches else None


def dynamic_template_actions(prototype_source: str) -> tuple[set[str], tuple[str, ...]]:
    """Return emitted actions and dynamic helpers with no call site.

    This is intentionally source-aware rather than a literal ``data-act`` scan:
    svgNodes/routesHtml are reachable with named actions, while pklist currently
    has the same template shape but no caller and must remain a hard failure.
    """
    declarations = list(
        re.finditer(r'(?m)^(?:function\s+|const\s+)([A-Za-z_$][\w$]*)\b', prototype_source)
    )
    helper_names: set[str] = set()
    for index, declaration in enumerate(declarations):
        end = declarations[index + 1].start() if index + 1 < len(declarations) else len(prototype_source)
        if 'data-act="${act}"' in prototype_source[declaration.start() : end]:
            helper_names.add(declaration.group(1))
    emitted: set[str] = set()
    dead: list[str] = []
    for helper in sorted(helper_names):
        calls: list[str] = []
        for match in re.finditer(rf'\b{re.escape(helper)}\s*\(', prototype_source):
            prefix = prototype_source[max(0, match.start() - 16) : match.start()]
            if re.search(r'(?:function|const)\s*$', prefix):
                continue
            arguments = _balanced_call(prototype_source, prototype_source.index("(", match.start()))
            if arguments is not None:
                calls.append(arguments)
        actions = {action for arguments in calls if (action := _final_string_argument(arguments)) is not None}
        if not calls:
            dead.append(helper)
        emitted.update(actions)
    return emitted, tuple(dead)


def validate(contract_source: str, prototype_source: str) -> tuple[str, ...]:
    failures: list[str] = []
    try:
        documented = documented_actions(contract_source)
    except ValueError as exc:
        return (f"action-inventory contract: {exc}; repair §9.14 before running U2.",)

    if len(documented) != EXPECTED_ACTION_COUNT:
        failures.append(
            f"action-inventory contract: expected {EXPECTED_ACTION_COUNT} documented actions, found {len(documented)}; repair §9.14."
        )
    unsupported = sorted({kind for _, kind in documented.values()} - ACTION_CLASSES)
    if unsupported:
        failures.append(f"action-inventory contract: unsupported action classes {unsupported}; repair §9.14.")

    emitted = literal_emissions(prototype_source)
    dynamic, dead_helpers = dynamic_template_actions(prototype_source)
    emitted.update(dynamic)
    dispatched = dispatcher_actions(prototype_source)
    documented_set = set(documented)
    for label, observed in (("emitted", emitted), ("dispatcher", dispatched)):
        missing = sorted(documented_set - observed)
        extra = sorted(observed - documented_set)
        if missing or extra:
            failures.append(
                f"action-inventory {label}: missing={missing} extra={extra}; repair prototype and §9.14 together."
            )
    for helper in dead_helpers:
        failures.append(
            f"action-inventory dynamic-template: {helper} emits data-act but has no reachable call site; remove it or add a caller."
        )
    return tuple(failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--prototype", type=Path, default=DEFAULT_PROTOTYPE)
    args = parser.parse_args(argv)
    try:
        failures = validate(args.contract.read_text(encoding="utf-8"), args.prototype.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        print(f"console action inventory: FAIL: {exc}")
        return 1
    if failures:
        print("console action inventory: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("console action inventory: PASS (57 documented, emitted, and dispatched actions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
