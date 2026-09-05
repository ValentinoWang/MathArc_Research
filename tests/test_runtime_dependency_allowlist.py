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

    def test_missing_dependency_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.py"
            result = check_dependencies([path])
            self.assertFalse(result["valid"], result)
            self.assertEqual(result["unknown"][str(path)], ["<missing path>"])

    def test_symlink_dependency_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.py"
            link = root / "runtime.py"
            target.write_text("import json\n", encoding="utf-8")
            link.symlink_to(target)
            result = check_dependencies([link])
            self.assertFalse(result["valid"], result)
            self.assertEqual(result["unknown"][str(link)], ["<symlink path>"])

    def test_hardlink_dependency_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.py"
            link = root / "runtime.py"
            source.write_text("import json\n", encoding="utf-8")
            link.hardlink_to(source)
            result = check_dependencies([link])
            self.assertFalse(result["valid"], result)
            self.assertEqual(result["unknown"][str(link)], ["<hardlink path>"])

    def test_local_transitive_dependency_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "matharc"
            package.mkdir()
            (package / "__init__.py").write_text("\n", encoding="utf-8")
            (package / "entry.py").write_text("import matharc.transitive\n", encoding="utf-8")
            (package / "transitive.py").write_text("import requests\n", encoding="utf-8")
            result = check_dependencies([package / "entry.py"])
            self.assertFalse(result["valid"], result)
            self.assertEqual(result["unknown"][str(package / "transitive.py")], ["requests"])


if __name__ == "__main__":
    unittest.main()
