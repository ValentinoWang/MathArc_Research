from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_frozen_review_inputs import (
    R1_INPUT_PROFILE,
    R1_REQUIRED_INPUTS,
    FrozenInputError,
    validate_frozen_inputs,
)


ROOT = Path(__file__).parents[1]
R1_EVIDENCE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane/evidence/R1.json"


class FrozenReviewInputTests(unittest.TestCase):
    def _fixture(self, root: Path, count: int = 6) -> Path:
        inputs = []
        for index in range(count):
            path = root / f"input-{index}.txt"
            path.write_text(f"frozen-{index}\n", encoding="utf-8")
            inputs.append({"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        manifest = root / "frozen-inputs.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "review_campaign_id": "synthetic-campaign",
                    "input_profile": R1_INPUT_PROFILE,
                    "frozen_head": "1" * 40,
                    "remote_head": "1" * 40,
                    "inputs": inputs,
                }
            ),
            encoding="utf-8",
        )
        return manifest

    def _validate_fixture(self, root: Path, manifest: Path) -> tuple[str, ...]:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        return validate_frozen_inputs(
            root,
            manifest,
            required_inputs=frozenset(item["path"] for item in payload["inputs"]),
        )

    def test_validates_every_declared_input_not_only_a_prefix(self) -> None:
        with TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            manifest = self._fixture(root)
            self.assertEqual(6, len(self._validate_fixture(root, manifest)))
            (root / "input-4.txt").write_text("drifted\n", encoding="utf-8")
            with self.assertRaisesRegex(FrozenInputError, "frozen input drift: input-4.txt"):
                self._validate_fixture(root, manifest)

    def test_rejects_duplicate_missing_and_escaping_paths(self) -> None:
        with TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            manifest = self._fixture(root, count=1)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["inputs"].append(dict(payload["inputs"][0]))
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FrozenInputError, "duplicate frozen input path"):
                self._validate_fixture(root, manifest)

            payload["inputs"] = [{"path": "missing.txt", "sha256": "0" * 64}]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FrozenInputError, "missing frozen input"):
                self._validate_fixture(root, manifest)

            outside = root.parent / f"{root.name}-outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            try:
                payload["inputs"] = [
                    {"path": f"../{outside.name}", "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}
                ]
                manifest.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(FrozenInputError, "escapes project root"):
                    self._validate_fixture(root, manifest)
            finally:
                outside.unlink()

    def test_rejects_non_normalized_and_duplicate_resolved_paths(self) -> None:
        with TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            manifest = self._fixture(root, count=1)
            digest = hashlib.sha256((root / "input-0.txt").read_bytes()).hexdigest()
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            for relative, message in (
                ("./input-0.txt", "normalized project-relative POSIX"),
                ("nested/../input-0.txt", "escapes project root"),
                ("nested\\input-0.txt", "normalized project-relative POSIX"),
            ):
                with self.subTest(relative=relative):
                    payload["inputs"] = [{"path": relative, "sha256": digest}]
                    manifest.write_text(
                        json.dumps(payload),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(FrozenInputError, message):
                        validate_frozen_inputs(root, manifest)

            alias = root / "alias.txt"
            os.link(root / "input-0.txt", alias)
            payload["inputs"] = [
                {"path": "input-0.txt", "sha256": digest},
                {"path": "alias.txt", "sha256": digest},
            ]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FrozenInputError, "duplicate resolved frozen input path"):
                self._validate_fixture(root, manifest)

    def test_rejects_symlinks_even_when_target_hash_matches(self) -> None:
        with TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            target = root / "target.txt"
            target.write_text("target\n", encoding="utf-8")
            link = root / "link.txt"
            os.symlink(target.name, link)
            manifest = root / "frozen-inputs.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "review_campaign_id": "synthetic-campaign",
                        "input_profile": R1_INPUT_PROFILE,
                        "frozen_head": "1" * 40,
                        "remote_head": "1" * 40,
                        "inputs": [{"path": link.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(FrozenInputError, "non-symlink regular file"):
                self._validate_fixture(root, manifest)

    def test_rejects_omitted_required_input_and_manifest_identity_drift(self) -> None:
        with TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            inputs = []
            for relative in sorted(R1_REQUIRED_INPUTS):
                candidate = root / relative
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_text(relative, encoding="utf-8")
                inputs.append({"path": relative, "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()})
            manifest = root / "frozen-inputs.json"
            payload = {
                "schema_version": 1,
                "review_campaign_id": "r1-v11-synthetic",
                "input_profile": R1_INPUT_PROFILE,
                "frozen_head": "1" * 40,
                "remote_head": "1" * 40,
                "inputs": inputs,
            }
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(R1_REQUIRED_INPUTS, frozenset(validate_frozen_inputs(root, manifest)))

            payload["inputs"].pop()
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FrozenInputError, "input set mismatch"):
                validate_frozen_inputs(root, manifest)

            payload["inputs"] = inputs
            payload["remote_head"] = "2" * 40
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FrozenInputError, "local and remote heads differ"):
                validate_frozen_inputs(root, manifest)

            payload["remote_head"] = payload["frozen_head"]
            payload["unexpected"] = True
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FrozenInputError, "fields do not match"):
                validate_frozen_inputs(root, manifest)

    def test_cli_failure_names_repair_path(self) -> None:
        with TemporaryDirectory(dir=ROOT) as temporary_root:
            root = Path(temporary_root)
            manifest = self._fixture(root, count=1)
            (root / "input-0.txt").write_text("drifted\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/validate_frozen_review_inputs.py"),
                    str(manifest),
                    "--project-root",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, completed.returncode)
            self.assertIn("frozen input drift", completed.stderr)
            self.assertIn("Repair: regenerate the manifest", completed.stderr)

    def test_current_r1_acceptance_requires_v11_complete_manifest_validation(self) -> None:
        evidence = json.loads(R1_EVIDENCE.read_text(encoding="utf-8"))
        frozen_validation = evidence["frozen_input_validation"]
        self.assertEqual(11, evidence["acceptance_contract_version"])
        self.assertEqual(11, frozen_validation["contract_version"])
        self.assertEqual(
            hashlib.sha256((ROOT / "scripts/validate_frozen_review_inputs.py").read_bytes()).hexdigest(),
            frozen_validation["validator_sha256"],
        )
        if evidence["acceptance_self_check"] != "pass":
            self.assertEqual("BLOCKED_PENDING_FROZEN_CANDIDATE", frozen_validation["disposition"])
            self.assertIsNone(frozen_validation["manifest"])
            self.assertIsNone(frozen_validation["manifest_sha256"])
            return

        self.assertEqual("PASS", frozen_validation["disposition"])
        manifest = ROOT / frozen_validation["manifest"]
        self.assertEqual(frozen_validation["manifest_sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest())
        observed = validate_frozen_inputs(ROOT, manifest)
        self.assertEqual(R1_REQUIRED_INPUTS, frozenset(observed))
        self.assertEqual(frozen_validation["validated_input_count"], len(observed))


if __name__ == "__main__":
    unittest.main()
