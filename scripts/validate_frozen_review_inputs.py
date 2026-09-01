#!/usr/bin/env python3
"""Fail closed when any file in a frozen review manifest drifts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
CAMPAIGN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
R1_INPUT_PROFILE = "r1-regression-evaluation-v11"
R1_REQUIRED_INPUTS = frozenset(
    {
        ".harness/guards/frozen-review-inputs.md",
        ".harness/guards/independent-review-provenance.md",
        "acceptance/human/R1-regression-evaluation/binding.md",
        "acceptance/human/R1-regression-evaluation/checklist.md",
        "agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/"
        "R1-regression-evaluation/acceptance-contract.md",
        "agents-results/2026-08-31/problem-intelligence-plane/evidence/A4.json",
        "agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/"
        "four-route-regression.json",
        "matharc/v02/regression_evaluation.py",
        "scripts/validate_frozen_review_inputs.py",
        "tests/test_frozen_review_inputs.py",
        "tests/test_v02_regression_evaluation.py",
    }
)


class FrozenInputError(ValueError):
    """Raised when a frozen review manifest is malformed or stale."""


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FrozenInputError(f"cannot read frozen manifest: {exc}") from exc
    if not isinstance(payload, dict):
        raise FrozenInputError("frozen manifest must be a JSON object")
    required_fields = {"schema_version", "review_campaign_id", "input_profile", "frozen_head", "remote_head", "inputs"}
    if set(payload) != required_fields:
        raise FrozenInputError("frozen manifest fields do not match the v11 schema")
    if payload["schema_version"] != 1:
        raise FrozenInputError("frozen manifest schema_version must be 1")
    campaign_id = payload["review_campaign_id"]
    if not isinstance(campaign_id, str) or not CAMPAIGN_ID_PATTERN.fullmatch(campaign_id):
        raise FrozenInputError("frozen manifest review_campaign_id is invalid")
    if payload["input_profile"] != R1_INPUT_PROFILE:
        raise FrozenInputError(f"frozen manifest input_profile must be {R1_INPUT_PROFILE}")
    frozen_head = payload["frozen_head"]
    remote_head = payload["remote_head"]
    if not isinstance(frozen_head, str) or not GIT_COMMIT_PATTERN.fullmatch(frozen_head):
        raise FrozenInputError("frozen manifest frozen_head must be a lowercase Git commit")
    if not isinstance(remote_head, str) or not GIT_COMMIT_PATTERN.fullmatch(remote_head):
        raise FrozenInputError("frozen manifest remote_head must be a lowercase Git commit")
    if frozen_head != remote_head:
        raise FrozenInputError("frozen manifest local and remote heads differ")
    inputs = payload.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise FrozenInputError("frozen manifest inputs must be a non-empty array")
    return payload


def validate_frozen_inputs(
    project_root: Path,
    manifest_path: Path,
    *,
    required_inputs: frozenset[str] = R1_REQUIRED_INPUTS,
) -> tuple[str, ...]:
    root = project_root.resolve(strict=True)
    try:
        manifest_metadata = manifest_path.lstat()
        manifest = manifest_path.resolve(strict=True)
    except OSError as exc:
        raise FrozenInputError(f"cannot resolve frozen manifest: {manifest_path}") from exc
    if manifest_path.is_symlink() or not stat.S_ISREG(manifest_metadata.st_mode):
        raise FrozenInputError("frozen manifest must be a non-symlink regular file")
    try:
        manifest.relative_to(root)
    except ValueError as exc:
        raise FrozenInputError("frozen manifest escapes project root") from exc
    payload = _load_manifest(manifest)
    observed: list[str] = []
    seen: set[str] = set()
    seen_file_identities: set[tuple[int, int]] = set()

    for index, item in enumerate(payload["inputs"]):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise FrozenInputError(f"input {index} must contain exactly path and sha256")
        relative = item["path"]
        expected = item["sha256"]
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise FrozenInputError(f"input {index} path must be a non-empty relative path")
        relative_path = Path(relative)
        if ".." in relative_path.parts:
            raise FrozenInputError(f"frozen input escapes project root: {relative}")
        if "\\" in relative or relative_path.as_posix() != relative or "." in relative_path.parts:
            raise FrozenInputError(f"input {index} path must be normalized project-relative POSIX: {relative}")
        if relative in seen:
            raise FrozenInputError(f"duplicate frozen input path: {relative}")
        seen.add(relative)
        if not isinstance(expected, str) or not SHA256_PATTERN.fullmatch(expected):
            raise FrozenInputError(f"input {index} sha256 must be a lowercase SHA-256 digest")

        candidate = root / relative
        try:
            metadata = candidate.lstat()
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise FrozenInputError(f"missing frozen input: {relative}") from exc
        if candidate.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise FrozenInputError(f"frozen input must be a non-symlink regular file: {relative}")
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise FrozenInputError(f"frozen input escapes project root: {relative}") from exc
        file_identity = (metadata.st_dev, metadata.st_ino)
        if file_identity in seen_file_identities:
            raise FrozenInputError(f"duplicate resolved frozen input path: {relative}")
        seen_file_identities.add(file_identity)

        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != expected:
            raise FrozenInputError(f"frozen input drift: {relative}: expected {expected}, observed {actual}")
        observed.append(relative)
    observed_set = set(observed)
    if observed_set != required_inputs:
        missing = sorted(required_inputs - observed_set)
        extra = sorted(observed_set - required_inputs)
        raise FrozenInputError(f"frozen manifest input set mismatch: missing={missing}, extra={extra}")
    return tuple(observed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        observed = validate_frozen_inputs(args.project_root, args.manifest)
    except FrozenInputError as exc:
        print(
            "frozen review inputs: FAIL: "
            f"{exc}. Repair: regenerate the manifest from the frozen candidate and retry.",
            file=sys.stderr,
        )
        return 1
    print(f"frozen review inputs: PASS ({len(observed)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
