from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_runtime_dependency_allowlist import check_dependencies, imported_roots


class RuntimeDependencyAllowlistTests(unittest.TestCase):
    def test_local_and_stdlib_imports_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.py"
            path.write_text("import json\nfrom matharc.v02.trace import ResearchTrace\n", encoding="utf-8")
            result = check_dependencies([path])
            self.assertTrue(result["valid"], result)

    def test_unknown_dependency_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.py"
            path.write_text("import requests\n", encoding="utf-8")
            result = check_dependencies([path])
            self.assertFalse(result["valid"])
            self.assertEqual(result["unknown"][str(path)], ["requests"])

    def test_process_and_network_modules_are_not_implicitly_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.py"
            path.write_text("import subprocess\nimport socket\n", encoding="utf-8")
            result = check_dependencies([path])
            self.assertFalse(result["valid"], result)
            self.assertEqual(result["unknown"][str(path)], ["socket", "subprocess"])

    def test_ast_parser_does_not_execute_source(self) -> None:
        self.assertEqual(imported_roots("raise RuntimeError('must not execute')"), set())


if __name__ == "__main__":
    unittest.main()
