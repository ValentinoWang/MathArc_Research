from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def _load_guard() -> ModuleType:
    path = ROOT / "scripts/check_console_action_inventory.py"
    spec = importlib.util.spec_from_file_location("console_action_inventory_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contract(actions: list[str]) -> str:
    rows = "\n".join(f"| `{action}` | view | effect | `local-ui-state` | no |" for action in actions)
    return f"#### 57 个动作\n{rows}\n门禁覆盖\n#### 异常"


def _prototype(actions: list[str], *, dead_template: bool = False) -> str:
    emitted = "".join(f'<button data-act="{action}"></button>' for action in actions)
    dispatcher = "\n".join(f'if(a==="{action}"){{}}' for action in actions)
    dead = 'const pklist = (act) => `<button data-act="${act}"></button>`;' if dead_template else ""
    return f"{emitted}\n{dispatcher}\n{dead}"


class ConsoleActionInventoryGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = _load_guard()
        cls.actions = [f"action-{index:02d}" for index in range(57)]

    def test_green_inventory_matches_literal_emissions_and_dispatcher(self) -> None:
        failures = self.guard.validate(_contract(self.actions), _prototype(self.actions))
        self.assertEqual(failures, ())

    def test_red_dead_dynamic_template_fails_closed(self) -> None:
        failures = self.guard.validate(_contract(self.actions), _prototype(self.actions, dead_template=True))
        self.assertTrue(any("pklist emits data-act but has no reachable call site" in item for item in failures))

    def test_dynamic_template_call_is_counted_as_an_emission(self) -> None:
        actions = [*self.actions[:-1], "dynamic"]
        source = _prototype(actions[:-1]) + '''
function svgNodes(act){ return `<button data-act="${act}"></button>`; }
svgNodes("dynamic");
if(a==="dynamic"){}
'''
        self.assertEqual(self.guard.validate(_contract(actions), source), ())

    def test_selector_is_not_counted_as_an_emission(self) -> None:
        source = _prototype(self.actions)
        source = source.replace('<button data-act="action-00"></button>', "")
        source += "document.querySelector('[data-act=\"action-00\"]');"
        failures = self.guard.validate(_contract(self.actions), source)
        self.assertTrue(any("action-00" in item and "emitted" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
