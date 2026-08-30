from __future__ import annotations

import ast
import unittest
from pathlib import Path


class ClaimArchitectureTests(unittest.TestCase):
    """Freeze the existing migration boundary until the vertical slice unifies it.

    v0.1 and v0.2 currently carry two historical claim-status vocabularies.  The
    phase-0 guard prevents a third parallel stack from appearing.  Phase 1 can
    replace this fixture with a single canonical definition once a real session
    has exercised both runtimes end to end.
    """

    def test_no_third_claim_status_definition_can_appear(self) -> None:
        package_root = Path(__file__).resolve().parents[1] / "matharc"
        definitions: list[str] = []
        for path in package_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "ClaimStatus":
                    definitions.append(path.relative_to(package_root).as_posix())
        self.assertEqual(sorted(definitions), ["models.py", "v02/schema.py"])

    def test_no_ambiguous_class_named_claim_is_introduced(self) -> None:
        package_root = Path(__file__).resolve().parents[1] / "matharc"
        definitions: list[str] = []
        for path in package_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "Claim":
                    definitions.append(path.relative_to(package_root).as_posix())
        self.assertEqual(definitions, [])


if __name__ == "__main__":
    unittest.main()
