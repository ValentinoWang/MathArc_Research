from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from matharc.v02.event_log import EVENT_TYPES


ROOT = Path(__file__).resolve().parents[1]


def _transition_literals() -> set[str]:
    values: set[str] = set()
    for path in (ROOT / "matharc" / "v02").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_seal_transition"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                values.add(node.args[0].value)
    return values


def _live_event_type_keys(page: str) -> list[str]:
    match = re.search(r"event_type:\[(.*?)\],\n", page, flags=re.DOTALL)
    if match is None:
        raise AssertionError("LIVE_ENUM_KEYS.event_type was not found")
    return re.findall(r'"([A-Z][A-Z0-9_]*)"', match.group(1))


class EventTypeContractTests(unittest.TestCase):
    def test_production_transitions_match_canonical_event_vocabulary(self) -> None:
        self.assertEqual(len(EVENT_TYPES), 21)
        self.assertEqual(len(set(EVENT_TYPES)), len(EVENT_TYPES))
        self.assertEqual(_transition_literals(), set(EVENT_TYPES))

    def test_live_enum_and_blueprint_bind_to_canonical_vocabulary(self) -> None:
        console = (ROOT / "docs/prototypes/problem-intel-console.html").read_text(
            encoding="utf-8"
        )
        self.assertEqual(_live_event_type_keys(console), list(EVENT_TYPES))
        self.assertIn(
            "event_type keys mirror matharc/v02/event_log.py:EVENT_TYPES",
            console,
        )

        blueprint = (ROOT / "docs/prototypes/console-dev-blueprint.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("事件类型共 21 个", blueprint)
        self.assertIn("21（演示链用其 14）", blueprint)
        self.assertIn("matharc/v02/event_log.py:EVENT_TYPES", blueprint)
        self.assertNotIn("事件类型共 18 个", blueprint)


if __name__ == "__main__":
    unittest.main()
