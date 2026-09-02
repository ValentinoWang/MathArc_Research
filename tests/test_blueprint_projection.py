from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
STATUSES = ("已落地", "待接线", "部分待建", "需新建", "已推迟")


def _load_guard() -> ModuleType:
    path = ROOT / "scripts/check_blueprint_projection.py"
    spec = importlib.util.spec_from_file_location("blueprint_projection_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contract(entries: list[tuple[str, str]]) -> str:
    rows = "\n".join(
        f"| `{view}` | plane | renderer | source | endpoint | yes | contract | {status} |"
        for view, status in entries
    )
    return f"#### 32 个视图的接线事实\n{rows}\n建设状态分布"


def _blueprint(entries: list[tuple[str, str]]) -> str:
    rows = "\n".join(
        f'<tr data-view-id="{view}"><td>{view}</td><td><span class="chip">{status}</span></td></tr>'
        for view, status in entries
    )
    return f'<section id="s5"><table>{rows}</table></section><section id="s6">'


class BlueprintProjectionGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = _load_guard()
        cls.entries = [(f"view_{index:02d}", STATUSES[index % len(STATUSES)]) for index in range(32)]

    def test_green_projection_has_one_matching_row_per_documented_view(self) -> None:
        self.assertEqual(self.guard.validate(_contract(self.entries), _blueprint(self.entries)), ())

    def test_red_status_drift_fails_closed(self) -> None:
        changed = [*self.entries]
        changed[4] = (changed[4][0], "已落地")
        failures = self.guard.validate(_contract(self.entries), _blueprint(changed))
        self.assertTrue(any("view_04" in item and "status" in item for item in failures))

    def test_red_missing_projection_row_fails_closed(self) -> None:
        failures = self.guard.validate(_contract(self.entries), _blueprint(self.entries[:-1]))
        self.assertTrue(any("view_31" in item and "missing" in item for item in failures))

    def test_current_blueprint_has_one_unambiguous_row_per_view(self) -> None:
        contract = (ROOT / "agents-results/2026-08-31/problem-intelligence-plane/.ssot/view-sources/00-main.md").read_text(encoding="utf-8")
        blueprint = (ROOT / "docs/prototypes/console-dev-blueprint.html").read_text(encoding="utf-8")
        self.assertEqual(self.guard.validate(contract, blueprint), ())


if __name__ == "__main__":
    unittest.main()
