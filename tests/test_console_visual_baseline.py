from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_console_visual_baseline import validate_baseline


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "docs/prototypes/problem-intel-console.html"
BLUEPRINT = ROOT / "docs/prototypes/console-dev-blueprint.html"
CONTRACT = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/.ssot/view-sources/00-main.md"


class ConsoleVisualBaselineTests(unittest.TestCase):
    def _copy_authorities(self, directory: Path) -> tuple[Path, Path, Path]:
        prototype = directory / "problem-intel-console.html"
        blueprint = directory / "console-dev-blueprint.html"
        contract = directory / "00-main.md"
        prototype.write_text(PROTOTYPE.read_text(encoding="utf-8"), encoding="utf-8")
        blueprint.write_text(BLUEPRINT.read_text(encoding="utf-8"), encoding="utf-8")
        contract.write_text(CONTRACT.read_text(encoding="utf-8"), encoding="utf-8")
        return prototype, blueprint, contract

    def test_green_current_authorities_match_the_frozen_u1_static_contract(self) -> None:
        self.assertEqual((), validate_baseline(PROTOTYPE, BLUEPRINT, CONTRACT))

    def test_red_token_drift_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            prototype, blueprint, contract = self._copy_authorities(Path(temporary_directory))
            prototype.write_text(
                prototype.read_text(encoding="utf-8").replace("--accent:#00736B", "--accent:#000000", 1),
                encoding="utf-8",
            )
            failures = validate_baseline(prototype, blueprint, contract)
        self.assertTrue(any("token table digest drift" in failure for failure in failures), failures)

    def test_red_unknown_construction_status_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            prototype, blueprint, contract = self._copy_authorities(Path(temporary_directory))
            source = contract.read_text(encoding="utf-8")
            marker = "#### 32 个视图的接线事实"
            before, section = source.split(marker, 1)
            section = section.replace("| 已落地 |", "| unknown |", 1)
            contract.write_text(before + marker + section, encoding="utf-8")
            failures = validate_baseline(prototype, blueprint, contract)
        self.assertTrue(any("invalid statuses" in failure for failure in failures), failures)

    def test_red_landing_descendant_selector_leakage_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            prototype, blueprint, contract = self._copy_authorities(Path(temporary_directory))
            prototype.write_text(
                prototype.read_text(encoding="utf-8").replace(".nots > div{", ".nots div{", 1),
                encoding="utf-8",
            )
            failures = validate_baseline(prototype, blueprint, contract)
        self.assertTrue(any("must not use the descendant selector" in failure for failure in failures), failures)

    def test_missing_authority_cannot_pass(self) -> None:
        failures = validate_baseline(ROOT / "missing-prototype.html", BLUEPRINT, CONTRACT)
        self.assertTrue(any("cannot read console prototype" in failure for failure in failures), failures)


if __name__ == "__main__":
    unittest.main()
