from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str, filename: str) -> ModuleType:
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Gate0CapabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight = _load_script("matharc_ci_preflight_contract", "ci_preflight.py")
        cls.unittest_gate = _load_script(
            "matharc_unittest_gate_contract", "run_unittest_suite.py"
        )
        cls.clean_checkout = _load_script(
            "matharc_clean_checkout_contract", "clean_checkout_ci.py"
        )

    def test_clean_checkout_includes_repository_registry_authority(self) -> None:
        self.assertEqual(
            self.clean_checkout._archive_paths(
                "Projects/MathArc_Research",
                (
                    ".github/workflows/matharc-research-ci.yml",
                    ".github/workflows/matharc-v02-bootstrap.yml",
                ),
            ),
            (
                "Projects/MathArc_Research",
                "registry.yaml",
                ".github/workflows/matharc-research-ci.yml",
                ".github/workflows/matharc-v02-bootstrap.yml",
            ),
        )

    def test_clean_checkout_selects_all_matharc_workflow_extensions(self) -> None:
        selected = self.clean_checkout._select_matharc_workflow_paths(
            (
                ".github/workflows/other.yml",
                ".github/workflows/matharc-b.yaml",
                ".github/workflows/matharc-a.yml",
                ".github/workflows/nested/matharc-hidden.yml",
            )
        )
        self.assertEqual(
            selected,
            (
                ".github/workflows/matharc-a.yml",
                ".github/workflows/matharc-b.yaml",
            ),
        )

    def test_developer_gate_without_z3_is_degraded_not_authoritative_pass(self) -> None:
        status, failures = self.preflight.evaluate_capabilities(
            {
                "matharc_importable": True,
                "mypy_available": True,
                "sympy_available": False,
                "z3_available": False,
            },
            require_formal=False,
        )
        self.assertEqual(status, "DEGRADED")
        self.assertEqual(failures, ())

    def test_authoritative_preflight_rejects_missing_formal_dependencies(self) -> None:
        status, failures = self.preflight.evaluate_capabilities(
            {
                "matharc_importable": True,
                "mypy_available": True,
                "sympy_available": False,
                "z3_available": False,
            },
            require_formal=True,
        )
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("sympy" in item for item in failures))
        self.assertTrue(any("z3" in item for item in failures))

    def test_smt_test_classification_does_not_depend_on_module_prefix(self) -> None:
        self.assertTrue(
            self.unittest_gate._is_smt_test(
                "tests.test_v02_smt_tools.SMTToolTests.test_sat_model"
            )
        )
        self.assertTrue(
            self.unittest_gate._is_smt_test(
                "test_v02_smt_tools.SMTToolTests.test_sat_model"
            )
        )
        self.assertFalse(
            self.unittest_gate._is_smt_test(
                "tests.test_v03_falsification.FalsificationTests.test_bounded"
            )
        )

    def test_authoritative_smt_gate_rejects_all_skipped(self) -> None:
        failures = self.unittest_gate.authoritative_smt_gate(
            z3_available=False,
            smt_discovered=10,
            smt_executed=0,
            smt_skipped=10,
        )
        self.assertTrue(failures)
        self.assertTrue(any("z3" in item for item in failures))
        self.assertTrue(any("no SMT tests actually executed" in item for item in failures))
        self.assertTrue(any("10 SMT tests were skipped" in item for item in failures))

    def test_authoritative_smt_gate_rejects_partial_skip(self) -> None:
        failures = self.unittest_gate.authoritative_smt_gate(
            z3_available=True,
            smt_discovered=10,
            smt_executed=9,
            smt_skipped=1,
        )
        self.assertEqual(failures, ("1 SMT tests were skipped",))

    def test_authoritative_smt_gate_accepts_full_execution(self) -> None:
        failures = self.unittest_gate.authoritative_smt_gate(
            z3_available=True,
            smt_discovered=10,
            smt_executed=10,
            smt_skipped=0,
        )
        self.assertEqual(failures, ())

    def test_authoritative_non_smt_skip_whitelist_accepts_exact_set(self) -> None:
        missing, unexpected = self.unittest_gate.authoritative_non_smt_skip_gate(
            self.unittest_gate.EXPECTED_NON_SMT_SKIP_IDS
        )
        self.assertEqual(missing, ())
        self.assertEqual(unexpected, ())

    def test_authoritative_non_smt_skip_whitelist_rejects_new_skip(self) -> None:
        actual = set(self.unittest_gate.EXPECTED_NON_SMT_SKIP_IDS)
        actual.add("tests.test_example.ExampleTests.test_new_skip")
        missing, unexpected = self.unittest_gate.authoritative_non_smt_skip_gate(actual)
        self.assertEqual(missing, ())
        self.assertEqual(
            unexpected,
            ("tests.test_example.ExampleTests.test_new_skip",),
        )

    def test_authoritative_non_smt_skip_whitelist_rejects_disappeared_skip(self) -> None:
        missing, unexpected = self.unittest_gate.authoritative_non_smt_skip_gate(
            {"unittest.loader.ModuleSkipped.tests.test_api_stream"}
        )
        self.assertEqual(
            missing,
            ("unittest.loader.ModuleSkipped.tests.test_codex_agent",),
        )
        self.assertEqual(unexpected, ())


if __name__ == "__main__":
    unittest.main()
