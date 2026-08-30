from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object: {path}")
    return payload


def _resolve_declared(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"declared path escapes archive root: {relative!r}")
    return candidate


def _nonempty_file(root: Path, relative: str) -> bool:
    path = _resolve_declared(root, relative)
    return path.is_file() and path.stat().st_size > 0


def _valid_component_result(root: Path, relative: str) -> bool:
    path = _resolve_declared(root, relative)
    if not path.is_file() or path.stat().st_size == 0:
        return False
    try:
        payload = _load_object(path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    return payload.get("all_checks_passed", payload.get("all_expected")) is True


def audit_archive(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = _load_object(root / "archive_manifest.json")
    if manifest.get("schema") != "matharc.frankl-q6-round4-archive.1":
        raise ValueError("unsupported Round-4 archive manifest schema")

    aggregate_decl = manifest.get("aggregate_record")
    if not isinstance(aggregate_decl, dict):
        raise TypeError("aggregate_record must be an object")
    aggregate_relative = aggregate_decl.get("path")
    expected_sha256 = aggregate_decl.get("sha256")
    if not isinstance(aggregate_relative, str) or not isinstance(expected_sha256, str):
        raise TypeError("aggregate_record requires string path and sha256")
    aggregate_path = _resolve_declared(root, aggregate_relative)
    actual_sha256 = _sha256(aggregate_path) if aggregate_path.is_file() else None

    aggregate_structure_valid = False
    if actual_sha256 == expected_sha256:
        aggregate = _load_object(aggregate_path)
        conclusion = aggregate.get("conclusion")
        aggregate_structure_valid = (
            aggregate.get("schema_version") == 1
            and aggregate.get("all_checks_passed") is True
            and isinstance(conclusion, dict)
            and conclusion.get("full_frankl_conjecture") == "INCONCLUSIVE"
        )

    raw_sources = manifest.get("required_rebuild_sources")
    raw_results = manifest.get("required_component_results")
    if not isinstance(raw_sources, list) or not all(isinstance(item, str) for item in raw_sources):
        raise ValueError("required_rebuild_sources must be an array of paths")
    if not isinstance(raw_results, list) or not all(isinstance(item, str) for item in raw_results):
        raise ValueError("required_component_results must be an array of paths")
    sources = [str(item) for item in raw_sources]
    results = [str(item) for item in raw_results]
    missing_sources = sorted(item for item in sources if not _nonempty_file(root, item))
    missing_or_invalid_results = sorted(
        item for item in results if not _valid_component_result(root, item)
    )
    archive_integrity = actual_sha256 == expected_sha256 and aggregate_structure_valid
    replay_inputs_complete = not missing_sources and not missing_or_invalid_results

    return {
        "schema": "matharc.frankl-q6-round4-archive-audit.1",
        "archive_status": (
            "ARCHIVE_INTEGRITY_PASS" if archive_integrity else "ARCHIVE_INTEGRITY_FAIL"
        ),
        "aggregate_record": {
            "path": aggregate_relative,
            "expected_sha256": expected_sha256,
            "actual_sha256": actual_sha256,
            "structure_valid": aggregate_structure_valid,
        },
        "missing_rebuild_sources": missing_sources,
        "missing_or_invalid_component_results": missing_or_invalid_results,
        "full_cold_replay_status": (
            "INPUTS_PRESENT_NOT_EXECUTED" if replay_inputs_complete else "UNAVAILABLE"
        ),
        "current_theorem_acceptance": False,
        "claim_boundary": manifest.get("claim_boundary"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--require-rebuild-sources", action="store_true")
    parser.add_argument("--require-full-replay-inputs", action="store_true")
    args = parser.parse_args(argv)
    report = audit_archive(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["archive_status"] != "ARCHIVE_INTEGRITY_PASS":
        return 1
    if args.require_rebuild_sources and report["missing_rebuild_sources"]:
        return 2
    if (
        args.require_full_replay_inputs
        and report["full_cold_replay_status"] != "INPUTS_PRESENT_NOT_EXECUTED"
    ):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
