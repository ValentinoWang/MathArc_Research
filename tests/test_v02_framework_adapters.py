from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from matharc.v02.framework_adapters import (
    FormalSuiteManifestAdapter,
    FrameworkAdapterSpec,
    FrameworkRegistry,
    LeanCliFormalizer,
    RepositoryPin,
)
from matharc.v02.schema import EvidenceStatus, ToolStatus


def init_repo(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "MathArc Test"], cwd=root, check=True)
    (root / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def pin(root: Path, commit: str) -> RepositoryPin:
    return RepositoryPin(
        framework_name="test framework",
        repository_url="https://example.invalid/test.git",
        commit_sha=commit,
        checkout_path=str(root),
    )


class FrameworkAdapterTests(unittest.TestCase):
    def test_repository_pin_accepts_exact_commit_and_rejects_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = init_repo(root)
            exact = pin(root, commit).verify_checkout()
            self.assertTrue(exact["valid"], exact)
            (root / "second.txt").write_text("second\n", encoding="utf-8")
            subprocess.run(["git", "add", "second.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "second"], cwd=root, check=True)
            drifted = pin(root, commit).verify_checkout()
            self.assertFalse(drifted["valid"])
            self.assertIn("pinned", drifted["errors"][0])

    def test_formal_suite_manifest_pins_file_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "theorems").mkdir()
            (root / "theorems" / "A.lean").write_text(
                "theorem A : True := by trivial\n", encoding="utf-8"
            )
            commit = init_repo(root)
            subprocess.run(["git", "add", "theorems/A.lean"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "add theorem"], cwd=root, check=True)
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            adapter = FormalSuiteManifestAdapter(pin(root, commit), suite_id="PINNED")
            cases = adapter.discover(("**/*.lean",))
            self.assertEqual(len(cases), 1)
            payload = cases[0].theorem_contract
            expected = hashlib.sha256(
                (root / "theorems" / "A.lean").read_bytes()
            ).hexdigest()
            self.assertEqual(payload["file_sha256"], expected)
            self.assertEqual(payload["commit_sha"], commit)

    def test_formalizer_accepts_only_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = root / "Proof.lean"
            proof.write_text("theorem demo : True := by trivial\n", encoding="utf-8")
            commit = init_repo(root)
            subprocess.run(["git", "add", "Proof.lean"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "proof"], cwd=root, check=True)
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            formalizer = LeanCliFormalizer(
                project_root=root,
                environment_pin=pin(root, commit),
                command_prefix=(
                    sys.executable,
                    "-c",
                    "import pathlib,sys; assert pathlib.Path(sys.argv[1]).is_file(); print('kernel ok')",
                ),
            )
            result = formalizer.verify_file(
                claim_id="C",
                evidence_id="E",
                call_id="T",
                lean_file="Proof.lean",
                statement_correspondence="The formal theorem is exactly C.",
            )
            self.assertEqual(result.tool_call.status, ToolStatus.PASS)
            self.assertEqual(result.evidence.status, EvidenceStatus.ACCEPTED)
            self.assertEqual(len(result.evidence.digest_sha256), 64)
            self.assertIn("Proof.lean", result.tool_call.replay_command)

            rejected = LeanCliFormalizer(
                project_root=root,
                environment_pin=pin(root, commit),
                command_prefix=(sys.executable, "-c", "raise SystemExit(1)"),
            ).verify_file(
                claim_id="C",
                evidence_id="E2",
                call_id="T2",
                lean_file="Proof.lean",
                statement_correspondence="The formal theorem is exactly C.",
            )
            self.assertEqual(rejected.tool_call.status, ToolStatus.FAIL)
            self.assertEqual(rejected.evidence.status, EvidenceStatus.REJECTED)

    def test_framework_bridge_is_proposal_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = init_repo(root)
            bridge = FrameworkAdapterSpec(
                adapter_id="test-bridge",
                role="prover",
                pin=pin(root, commit),
                bridge_command=(
                    sys.executable,
                    "-c",
                    "import json,sys; json.load(sys.stdin); print(json.dumps({'public_reasoning': {'objective':'x','premises':[],'proposed_move':'x','observation':'x','falsification':'x','decision':'candidate'}}))",
                ),
            ).build_proposal_worker()
            self.assertEqual(bridge.role, "prover")
            self.assertIn("MATHARC_FRAMEWORK_COMMIT", bridge.extra_env)

    def test_registry_loads_declared_open_source_targets(self) -> None:
        root = Path(__file__).resolve().parents[1]
        registry = FrameworkRegistry.load(root / "benchmarks" / "agent_registry_v02.json")
        names = {item["name"] for item in registry.systems}
        self.assertIn("Math Research Agent", names)
        self.assertIn("LeanDojo", names)
        self.assertIn("LeanStar", names)
        self.assertIn("PutnamBench", names)
        self.assertFalse(any(item["measured"] for item in registry.systems))


if __name__ == "__main__":
    unittest.main()
