from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .benchmark_runner import BenchmarkCase
from .schema import (
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ToolCallRecord,
    ToolStatus,
    canonical_json,
    digest_json,
    utc_now,
)
from .workers import SubprocessProposalWorker

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


@dataclass(slots=True, frozen=True)
class RepositoryPin:
    framework_name: str
    repository_url: str
    commit_sha: str
    checkout_path: str

    def __post_init__(self) -> None:
        if not _SHA40.fullmatch(self.commit_sha.lower()):
            raise ValueError("commit_sha must be a full forty-character hexadecimal SHA")
        if not self.repository_url.strip():
            raise ValueError("repository_url cannot be empty")

    def verify_checkout(self) -> dict[str, Any]:
        checkout = Path(self.checkout_path)
        if not checkout.is_dir():
            return {
                "valid": False,
                "errors": [f"checkout does not exist: {checkout}"],
                "framework_name": self.framework_name,
            }
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        errors: list[str] = []
        actual = completed.stdout.strip().lower() if completed.returncode == 0 else ""
        if completed.returncode != 0:
            errors.append(f"git rev-parse failed: {completed.stderr.strip()}")
        elif actual != self.commit_sha.lower():
            errors.append(f"checkout commit {actual} != pinned {self.commit_sha.lower()}")
        return {
            "valid": not errors,
            "errors": errors,
            "framework_name": self.framework_name,
            "repository_url": self.repository_url,
            "pinned_commit": self.commit_sha.lower(),
            "actual_commit": actual,
            "checkout_path": str(checkout.resolve()),
            "pin_digest_sha256": digest_json(self.to_dict()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework_name": self.framework_name,
            "repository_url": self.repository_url,
            "commit_sha": self.commit_sha.lower(),
            "checkout_path": self.checkout_path,
        }


@dataclass(slots=True, frozen=True)
class FrameworkAdapterSpec:
    adapter_id: str
    role: str
    pin: RepositoryPin
    bridge_command: tuple[str, ...]
    timeout_seconds: float = 300.0
    max_output_bytes: int = 2_000_000
    extra_env: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.bridge_command:
            raise ValueError("bridge_command cannot be empty")
        if self.timeout_seconds <= 0 or self.max_output_bytes <= 0:
            raise ValueError("adapter limits must be positive")

    def build_proposal_worker(self) -> SubprocessProposalWorker:
        verification = self.pin.verify_checkout()
        if not verification["valid"]:
            raise ValueError("; ".join(verification["errors"]))
        environment = dict(self.extra_env)
        environment.update(
            {
                "MATHARC_FRAMEWORK_NAME": self.pin.framework_name,
                "MATHARC_FRAMEWORK_COMMIT": self.pin.commit_sha,
                "MATHARC_ADAPTER_ID": self.adapter_id,
            }
        )
        return SubprocessProposalWorker(
            role=self.role,
            command=self.bridge_command,
            cwd=self.pin.checkout_path,
            timeout_seconds=self.timeout_seconds,
            max_output_bytes=self.max_output_bytes,
            extra_env=environment,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "role": self.role,
            "pin": self.pin.to_dict(),
            "bridge_command": list(self.bridge_command),
            "timeout_seconds": self.timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
            "extra_env": dict(self.extra_env),
            "trust_boundary": "proposal-only; no direct PROVED transition",
        }


@dataclass(slots=True)
class FormalizerResult:
    tool_call: ToolCallRecord
    evidence: EvidenceRecord
    stdout: str
    stderr: str
    environment_digest_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_call": self.tool_call.to_dict(),
            "evidence": self.evidence.to_dict(),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "environment_digest_sha256": self.environment_digest_sha256,
        }


class LeanCliFormalizer:
    """Kernel-gated adapter for a pinned Lean project.

    The default command is `lake env lean`.  A caller may supply a compatible
    command for testing, but accepted evidence is still scoped to the declared
    environment and exact command recorded in the tool call.
    """

    def __init__(
        self,
        *,
        project_root: str | Path,
        environment_pin: RepositoryPin,
        command_prefix: Sequence[str] = ("lake", "env", "lean"),
        timeout_seconds: float = 300.0,
    ) -> None:
        self.project_root = Path(project_root)
        self.environment_pin = environment_pin
        self.command_prefix = tuple(str(item) for item in command_prefix)
        self.timeout_seconds = timeout_seconds
        if not self.command_prefix:
            raise ValueError("Lean command prefix cannot be empty")

    def verify_file(
        self,
        *,
        claim_id: str,
        evidence_id: str,
        call_id: str,
        lean_file: str | Path,
        statement_correspondence: str,
        assumptions_checked: Iterable[str] = (),
    ) -> FormalizerResult:
        pin = self.environment_pin.verify_checkout()
        if not pin["valid"]:
            raise ValueError("; ".join(pin["errors"]))
        file_path = Path(lean_file)
        if not file_path.is_absolute():
            file_path = self.project_root / file_path
        file_path = file_path.resolve()
        if not file_path.is_file():
            raise FileNotFoundError(file_path)
        if self.project_root.resolve() not in file_path.parents:
            raise ValueError("Lean file must be inside the pinned project root")
        relative = file_path.relative_to(self.project_root.resolve())
        command = (*self.command_prefix, str(relative))
        environment_digest = self._environment_digest(pin)
        source = file_path.read_bytes()
        started_at = utc_now()
        completed = subprocess.run(
            list(command),
            cwd=self.project_root,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        ended_at = utc_now()
        status = ToolStatus.PASS if completed.returncode == 0 else ToolStatus.FAIL
        stdout_digest = _sha_text(completed.stdout)
        proof_artifact_digest = _sha_bytes(
            source
            + b"\0"
            + completed.stdout.encode("utf-8")
            + b"\0"
            + environment_digest.encode("ascii")
        )
        replay = " ".join(shlex.quote(item) for item in command)
        tool_call = ToolCallRecord(
            call_id=call_id,
            tool="lean-kernel",
            purpose=f"Kernel-check formal proof artifact for {claim_id}.",
            status=status,
            input_digest_sha256=_sha_bytes(source),
            output_digest_sha256=stdout_digest,
            linked_claim_ids=(claim_id,),
            independence_group=f"lean-kernel:{environment_digest[:16]}",
            replay_command=replay,
            started_at=started_at,
            ended_at=ended_at,
            exit_code=completed.returncode,
            environment_digest_sha256=environment_digest,
            expected_discriminator="Lean exits zero after checking the pinned file",
        )
        evidence = EvidenceRecord(
            evidence_id=evidence_id,
            claim_ids=(claim_id,),
            kind=EvidenceKind.FORMAL_PROOF,
            status=(
                EvidenceStatus.ACCEPTED
                if completed.returncode == 0
                else EvidenceStatus.REJECTED
            ),
            summary=(
                "Pinned Lean kernel accepted the proof file."
                if completed.returncode == 0
                else "Pinned Lean kernel rejected the proof file."
            ),
            artifact_uri=str(file_path),
            digest_sha256=proof_artifact_digest,
            producer="Lean proof author/search worker",
            verifier=f"Lean kernel at {self.environment_pin.commit_sha}",
            independence_group=f"lean-kernel:{environment_digest[:16]}",
            replay_command=replay,
            statement_correspondence=statement_correspondence,
            assumptions_checked=tuple(str(item) for item in assumptions_checked),
            limitations=(
                "The formal result is only as broad as the encoded theorem statement.",
                "Informal-to-formal statement correspondence remains an explicit audit obligation.",
            ),
        )
        return FormalizerResult(
            tool_call=tool_call,
            evidence=evidence,
            stdout=completed.stdout,
            stderr=completed.stderr,
            environment_digest_sha256=environment_digest,
        )

    def _environment_digest(self, pin_verification: Mapping[str, Any]) -> str:
        files: dict[str, str] = {}
        for name in ("lean-toolchain", "lake-manifest.json", "lakefile.lean", "lakefile.toml"):
            path = self.project_root / name
            if path.is_file():
                files[name] = _sha_bytes(path.read_bytes())
        return digest_json(
            {
                "pin": dict(pin_verification),
                "command_prefix": list(self.command_prefix),
                "environment_files": files,
            }
        )


class FormalSuiteManifestAdapter:
    """Create pinned benchmark cases from formal theorem files.

    This adapter can index PutnamBench or another formal suite without assuming
    a specific repository layout.  The caller supplies globs and a pinned
    checkout; every case payload contains the exact file digest and commit.
    """

    def __init__(
        self,
        pin: RepositoryPin,
        *,
        suite_id: str,
        family_id: str = "FORMAL-COMPLETION",
    ) -> None:
        self.pin = pin
        self.suite_id = suite_id
        self.family_id = family_id

    def discover(
        self,
        patterns: Iterable[str] = ("**/*.lean",),
        *,
        required_metrics: Iterable[str] = ("audited_closure",),
    ) -> list[BenchmarkCase]:
        verification = self.pin.verify_checkout()
        if not verification["valid"]:
            raise ValueError("; ".join(verification["errors"]))
        root = Path(self.pin.checkout_path).resolve()
        files: dict[str, Path] = {}
        for pattern in patterns:
            for path in root.glob(pattern):
                if path.is_file() and ".git" not in path.parts:
                    relative = path.resolve().relative_to(root).as_posix()
                    files[relative] = path.resolve()
        cases: list[BenchmarkCase] = []
        for relative, path in sorted(files.items()):
            digest = _sha_bytes(path.read_bytes())
            case_id = f"{self.suite_id}:{relative}"
            cases.append(
                BenchmarkCase(
                    case_id=case_id,
                    family_id=self.family_id,
                    problem=f"Complete or verify the pinned formal theorem file {relative}.",
                    theorem_contract={
                        "formal_file": relative,
                        "repository": self.pin.repository_url,
                        "commit_sha": self.pin.commit_sha,
                        "file_sha256": digest,
                    },
                    case_payload={
                        "checkout_root": str(root),
                        "formal_file": relative,
                        "file_sha256": digest,
                    },
                    required_metrics=tuple(required_metrics),
                    acceptance_contract={
                        "kernel_check": True,
                        "cold_replay": True,
                        "statement_correspondence": True,
                    },
                )
            )
        return cases


class FrameworkRegistry:
    def __init__(self, payload: Mapping[str, Any]) -> None:
        self.payload = dict(payload)
        if str(self.payload.get("schema_version")) != "1.0":
            raise ValueError("unsupported framework registry schema")
        systems = self.payload.get("systems")
        if not isinstance(systems, list):
            raise ValueError("framework registry systems must be a list")
        names = [str(item.get("name", "")) for item in systems]
        if any(not name for name in names) or len(names) != len(set(names)):
            raise ValueError("framework registry names must be unique and non-empty")

    @property
    def systems(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(item) for item in self.payload["systems"])

    def get(self, name: str) -> dict[str, Any]:
        for item in self.systems:
            if item.get("name") == name:
                return item
        raise KeyError(name)

    @classmethod
    def load(cls, path: str | Path) -> "FrameworkRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("framework registry root must be an object")
        return cls(payload)
