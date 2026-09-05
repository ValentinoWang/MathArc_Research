from __future__ import annotations

import unittest
import tempfile
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

    def test_traversal_cannot_enter_runtime_allowlist(self) -> None:
        self.assertFalse(is_runtime_owned("matharc/v02/runtime/../../develop/Harness/fullstack-ai-harness.md"))
        self.assertFalse(is_runtime_owned("matharc/v02/runtime/../../../.harness/overlays/project-harness-adapter.yaml"))

    def test_symlinked_runtime_path_is_classified_by_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "outside").mkdir()
            (root / "matharc/v02").mkdir(parents=True)
            (root / "matharc/v02/runtime").symlink_to(root / "outside", target_is_directory=True)
            self.assertFalse(is_runtime_owned("matharc/v02/runtime/escape.py", root=root))

    def test_missing_path_under_allowed_prefix_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "matharc/v02/runtime").mkdir(parents=True)
            self.assertFalse(is_runtime_owned("matharc/v02/runtime/missing.py", root=root))

    def test_hardlinked_runtime_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "matharc/v02/runtime"
            runtime.mkdir(parents=True)
            source = root / "outside.py"
            linked = runtime / "linked.py"
            source.write_text("# hardlink fixture\n", encoding="utf-8")
            linked.hardlink_to(source)
            self.assertFalse(is_runtime_owned(linked, root=root))


if __name__ == "__main__":
    unittest.main()
