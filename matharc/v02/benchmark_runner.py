from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .benchmark import BenchmarkComparison, BenchmarkResult, compare_agents, save_results
from .schema import canonical_json, digest_json, utc_now


def _stream_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


@dataclass(slots=True, frozen=True)
class BudgetSpec:
    wall_time_seconds: float
    max_output_bytes: int
    token_budget: int
    model_call_budget: int
    tool_cpu_seconds: float

    def __post_init__(self) -> None:
        if self.wall_time_seconds <= 0:
            raise ValueError("wall_time_seconds must be positive")
        if self.max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
        if self.token_budget < 0 or self.model_call_budget < 0 or self.tool_cpu_seconds < 0:
            raise ValueError("budget values cannot be negative")

    @property
    def normalized_units(self) -> float:
        # A declared accounting unit, not a claim of hardware equivalence.
        return (
            self.wall_time_seconds
            + self.tool_cpu_seconds
            + self.token_budget / 1000.0
            + 10.0 * self.model_call_budget
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "wall_time_seconds": self.wall_time_seconds,
            "max_output_bytes": self.max_output_bytes,
            "token_budget": self.token_budget,
            "model_call_budget": self.model_call_budget,
            "tool_cpu_seconds": self.tool_cpu_seconds,
            "normalized_units": self.normalized_units,
            "enforcement_boundary": (
                "The local runner enforces wall time and output bytes. Token, model-call "
                "and downstream tool-CPU budgets require adapter-level accounting and are audited from output."
            ),
        }


@dataclass(slots=True, frozen=True)
class BenchmarkCase:
    case_id: str
    family_id: str
    problem: str
    theorem_contract: dict[str, Any]
    case_payload: dict[str, Any]
    required_metrics: tuple[str, ...]
    acceptance_contract: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "family_id": self.family_id,
            "problem": self.problem,
            "theorem_contract": self.theorem_contract,
            "case_payload": self.case_payload,
            "required_metrics": list(self.required_metrics),
            "acceptance_contract": self.acceptance_contract,
        }


@dataclass(slots=True, frozen=True)
class SubprocessAgentSpec:
    system_name: str
    system_version: str
    command: tuple[str, ...]
    cwd: str
    adapter_id: str
    environment_lock_digest_sha256: str
    extra_env: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.command:
            raise ValueError("agent command cannot be empty")
        if len(self.environment_lock_digest_sha256) != 64:
            raise ValueError("environment lock digest must be SHA-256")

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_name": self.system_name,
            "system_version": self.system_version,
            "command": list(self.command),
            "cwd": self.cwd,
            "adapter_id": self.adapter_id,
            "environment_lock_digest_sha256": self.environment_lock_digest_sha256,
            "extra_env": dict(self.extra_env),
        }


@dataclass(slots=True)
class AgentExecution:
    result: BenchmarkResult
    request_digest_sha256: str
    stdout_digest_sha256: str
    stderr_digest_sha256: str
    returncode: int | None
    status: str
    adapter_reported_usage: dict[str, float]
    artifact_directory: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.to_dict(),
            "request_digest_sha256": self.request_digest_sha256,
            "stdout_digest_sha256": self.stdout_digest_sha256,
            "stderr_digest_sha256": self.stderr_digest_sha256,
            "returncode": self.returncode,
            "status": self.status,
            "adapter_reported_usage": self.adapter_reported_usage,
            "artifact_directory": self.artifact_directory,
        }


@dataclass(slots=True)
class PairedBenchmarkRun:
    suite_id: str
    suite_version: str
    budget: BudgetSpec
    candidate: SubprocessAgentSpec
    baseline: SubprocessAgentSpec
    executions: tuple[AgentExecution, ...]
    comparison: BenchmarkComparison
    order_policy: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "budget": self.budget.to_dict(),
            "candidate": self.candidate.to_dict(),
            "baseline": self.baseline.to_dict(),
            "executions": [item.to_dict() for item in self.executions],
            "comparison": self.comparison.to_dict(),
            "order_policy": self.order_policy,
            "created_at": self.created_at,
            "claim_boundary": (
                "Comparison applies only to these adapters, cases, seeds, versions and budget."
            ),
        }


class PairedBenchmarkRunner:
    """Launch candidate and baseline under the same enforceable harness contract."""

    def __init__(
        self,
        *,
        suite_id: str,
        suite_version: str,
        candidate: SubprocessAgentSpec,
        baseline: SubprocessAgentSpec,
        budget: BudgetSpec,
        output_root: str | Path,
        metric_directions: Mapping[str, str],
        primary_metrics: Iterable[str],
        minimum_pairs: int = 30,
        bootstrap_samples: int = 5000,
    ) -> None:
        self.suite_id = suite_id
        self.suite_version = suite_version
        self.candidate = candidate
        self.baseline = baseline
        self.budget = budget
        self.output_root = Path(output_root)
        self.metric_directions = dict(metric_directions)
        self.primary_metrics = tuple(primary_metrics)
        self.minimum_pairs = minimum_pairs
        self.bootstrap_samples = bootstrap_samples

    def run(
        self,
        cases: Iterable[BenchmarkCase],
        seeds: Iterable[int],
    ) -> PairedBenchmarkRun:
        case_list = list(cases)
        seed_list = list(seeds)
        if not case_list:
            raise ValueError("benchmark has no cases")
        if not seed_list:
            raise ValueError("benchmark has no seeds")
        self.output_root.mkdir(parents=True, exist_ok=True)
        executions: list[AgentExecution] = []
        for case in case_list:
            for seed in seed_list:
                # Deterministically alternate execution order to reduce a fixed
                # cache/thermal/order advantage while preserving full pairing.
                specs = [self.candidate, self.baseline]
                if int(hashlib.sha256(f"{case.case_id}:{seed}".encode()).hexdigest(), 16) % 2:
                    specs.reverse()
                for spec in specs:
                    executions.append(self._execute(spec, case, seed))
        candidate_results = [
            item.result
            for item in executions
            if item.result.system_name == self.candidate.system_name
        ]
        baseline_results = [
            item.result
            for item in executions
            if item.result.system_name == self.baseline.system_name
        ]
        comparison = compare_agents(
            candidate_results,
            baseline_results,
            metric_directions=self.metric_directions,
            primary_metrics=self.primary_metrics,
            minimum_pairs=self.minimum_pairs,
            bootstrap_samples=self.bootstrap_samples,
        )
        run = PairedBenchmarkRun(
            suite_id=self.suite_id,
            suite_version=self.suite_version,
            budget=self.budget,
            candidate=self.candidate,
            baseline=self.baseline,
            executions=tuple(executions),
            comparison=comparison,
            order_policy="deterministic parity alternation by SHA-256(case_id:seed)",
        )
        self._save(run, candidate_results, baseline_results)
        return run

    def _execute(
        self,
        spec: SubprocessAgentSpec,
        case: BenchmarkCase,
        seed: int,
    ) -> AgentExecution:
        artifact_directory = (
            self.output_root
            / "executions"
            / self._safe(spec.system_name)
            / self._safe(case.case_id)
            / str(seed)
        )
        artifact_directory.mkdir(parents=True, exist_ok=True)
        request = {
            "schema_version": "1.0",
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "system_name": spec.system_name,
            "system_version": spec.system_version,
            "adapter_id": spec.adapter_id,
            "case": case.to_dict(),
            "seed": seed,
            "budget": self.budget.to_dict(),
            "output_contract": {
                "required": [
                    "release_state",
                    "metrics",
                    "false_promotion",
                    "replay_pass",
                    "usage",
                ],
                "artifact_directory": str(artifact_directory.resolve()),
                "proof_authority": "external output is benchmark evidence, not a MathArc claim promotion",
            },
        }
        stdin_text = canonical_json(request)
        request_path = artifact_directory / "request.json"
        request_path.write_text(
            json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment.update(dict(spec.extra_env))
        environment.update(
            {
                "MATHARC_BENCHMARK_SEED": str(seed),
                "MATHARC_ARTIFACT_DIRECTORY": str(artifact_directory.resolve()),
                "MATHARC_TOKEN_BUDGET": str(self.budget.token_budget),
                "MATHARC_MODEL_CALL_BUDGET": str(self.budget.model_call_budget),
                "MATHARC_TOOL_CPU_SECONDS": str(self.budget.tool_cpu_seconds),
            }
        )
        started = time.perf_counter()
        returncode: int | None = None
        stdout = ""
        stderr = ""
        status = "ERROR"
        parsed: dict[str, Any] | None = None
        try:
            completed = subprocess.run(
                list(spec.command),
                input=stdin_text,
                text=True,
                capture_output=True,
                cwd=spec.cwd,
                env=environment,
                timeout=self.budget.wall_time_seconds,
                check=False,
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            if len(stdout.encode("utf-8")) > self.budget.max_output_bytes:
                status = "OUTPUT_LIMIT"
                stderr += "\nMathArc: stdout exceeded max_output_bytes."
            elif completed.returncode != 0:
                status = "NONZERO_EXIT"
            else:
                value = json.loads(stdout)
                if not isinstance(value, dict):
                    raise ValueError("agent response root must be an object")
                parsed = value
                self._validate_response(case, value)
                status = "PASS"
        except subprocess.TimeoutExpired as exc:
            stdout = _stream_text(exc.stdout)
            stderr = _stream_text(exc.stderr) + "\nMathArc: wall-time limit exceeded."
            status = "TIMEOUT"
        except Exception as exc:
            stderr += f"\nMathArc: {type(exc).__name__}: {exc}"
            status = "ERROR"
        runtime = time.perf_counter() - started
        (artifact_directory / "stdout.txt").write_text(stdout, encoding="utf-8")
        (artifact_directory / "stderr.txt").write_text(stderr, encoding="utf-8")

        if parsed is None:
            metrics = {metric: 0.0 for metric in case.required_metrics}
            release_state = "ADAPTER_ERROR"
            false_promotion = False
            replay_pass = False
            usage: dict[str, float] = {}
        else:
            metrics = {key: float(value) for key, value in parsed["metrics"].items()}
            release_state = str(parsed["release_state"])
            false_promotion = bool(parsed["false_promotion"])
            replay_pass = bool(parsed["replay_pass"])
            usage = {key: float(value) for key, value in parsed["usage"].items()}
            if not self._usage_within_budget(usage):
                status = "BUDGET_VIOLATION"
                replay_pass = False

        output_digest = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
        result = BenchmarkResult(
            system_name=spec.system_name,
            suite_id=self.suite_id,
            suite_version=self.suite_version,
            case_id=case.case_id,
            seed=seed,
            metrics=metrics,
            release_state=release_state,
            false_promotion=false_promotion,
            replay_pass=replay_pass and status == "PASS",
            budget_units=self.budget.normalized_units,
            runtime_seconds=runtime,
            artifact_digest_sha256=output_digest,
            metadata={
                "system_version": spec.system_version,
                "adapter_id": spec.adapter_id,
                "environment_lock_digest_sha256": spec.environment_lock_digest_sha256,
                "execution_status": status,
                "family_id": case.family_id,
            },
        )
        execution = AgentExecution(
            result=result,
            request_digest_sha256=hashlib.sha256(stdin_text.encode()).hexdigest(),
            stdout_digest_sha256=output_digest,
            stderr_digest_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            returncode=returncode,
            status=status,
            adapter_reported_usage=usage,
            artifact_directory=str(artifact_directory),
        )
        (artifact_directory / "execution.json").write_text(
            json.dumps(execution.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return execution

    def _validate_response(self, case: BenchmarkCase, payload: Mapping[str, Any]) -> None:
        required = {
            "release_state",
            "metrics",
            "false_promotion",
            "replay_pass",
            "usage",
        }
        missing = required - set(payload)
        if missing:
            raise ValueError(f"agent response misses fields: {sorted(missing)}")
        forbidden = {
            "chain_of_thought",
            "private_chain_of_thought",
            "scratchpad",
            "private_reasoning",
        }
        if forbidden & set(payload):
            raise ValueError("agent response contains forbidden private-reasoning fields")
        if not isinstance(payload["metrics"], Mapping):
            raise ValueError("metrics must be an object")
        absent_metrics = set(case.required_metrics) - set(payload["metrics"])
        if absent_metrics:
            raise ValueError(f"agent response misses metrics: {sorted(absent_metrics)}")
        if not isinstance(payload["usage"], Mapping):
            raise ValueError("usage must be an object")

    def _usage_within_budget(self, usage: Mapping[str, float]) -> bool:
        checks = {
            "tokens": self.budget.token_budget,
            "model_calls": self.budget.model_call_budget,
            "tool_cpu_seconds": self.budget.tool_cpu_seconds,
        }
        for key, limit in checks.items():
            if key not in usage:
                return False
            if float(usage[key]) < 0 or float(usage[key]) > limit:
                return False
        return True

    def _save(
        self,
        run: PairedBenchmarkRun,
        candidate_results: list[BenchmarkResult],
        baseline_results: list[BenchmarkResult],
    ) -> None:
        (self.output_root / "run.json").write_text(
            json.dumps(run.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        save_results(candidate_results, self.output_root / "candidate-results.json")
        save_results(baseline_results, self.output_root / "baseline-results.json")
        (self.output_root / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "suite_id": self.suite_id,
                    "suite_version": self.suite_version,
                    "budget_digest_sha256": digest_json(self.budget.to_dict()),
                    "case_pair_count": len(candidate_results),
                    "candidate_adapter_digest_sha256": digest_json(self.candidate.to_dict()),
                    "baseline_adapter_digest_sha256": digest_json(self.baseline.to_dict()),
                    "comparison_qualification": run.comparison.qualification_state,
                    "superiority_claim_allowed": run.comparison.superiority_claim_allowed,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _safe(value: str) -> str:
        result = "".join(char if char.isalnum() or char in "-_." else "_" for char in value)
        return result[:120] or "unnamed"
