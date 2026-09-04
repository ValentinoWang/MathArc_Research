from __future__ import annotations

import unittest
from pathlib import Path

from scripts.check_runtime_ownership import check_runtime_ownership, is_runtime_owned


class RuntimeOwnershipTests(unittest.TestCase):
    def test_runtime_and_declared_tests_are_owned(self) -> None:
        result = check_runtime_ownership(
            [
                "matharc/v02/runtime/contracts.py",
                "matharc/v02/trace.py",
                "scripts/check_runtime_ownership.py",
                "tests/test_runtime_authority_boundaries.py",
                "deploy/matharc-research.service",
            ]
        )
        self.assertTrue(result["valid"], result)

    def test_harness_paths_are_outside_product_runtime(self) -> None:
        self.assertFalse(is_runtime_owned("develop/Harness/fullstack-ai-harness.md"))
        self.assertFalse(is_runtime_owned(".harness/overlays/project-harness-adapter.yaml"))
        self.assertFalse(is_runtime_owned("agents-results/2026-09-04/report.md"))

    def test_repository_absolute_paths_normalize(self) -> None:
        root = Path.cwd()
        self.assertTrue(is_runtime_owned(root / "matharc/v02/trace.py", root=root))


if __name__ == "__main__":
    unittest.main()
