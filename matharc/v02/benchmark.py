from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Mapping


@dataclass(slots=True)
class BenchmarkResult:
    system_name: str
    suite_id: str
    suite_version: str
    case_id: str
    seed: int
    metrics: dict[str, float]
    release_state: str
    false_promotion: bool
    replay_pass: bool
    budget_units: float
    runtime_seconds: float
    artifact_digest_sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def pair_key(self) -> tuple[str, int]:
        return self.case_id, self.seed

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_name": self.system_name,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "case_id": self.case_id,
            "seed": self.seed,
            "metrics": self.metrics,
            "release_state": self.release_state,
            "false_promotion": self.false_promotion,
            "replay_pass": self.replay_pass,
            "budget_units": self.budget_units,
            "runtime_seconds": self.runtime_seconds,
            "artifact_digest_sha256": self.artifact_digest_sha256,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BenchmarkResult":
        return cls(
            system_name=str(payload["system_name"]),
            suite_id=str(payload["suite_id"]),
            suite_version=str(payload["suite_version"]),
            case_id=str(payload["case_id"]),
            seed=int(payload["seed"]),
            metrics={str(key): float(value) for key, value in payload["metrics"].items()},
            release_state=str(payload["release_state"]),
            false_promotion=bool(payload["false_promotion"]),
            replay_pass=bool(payload["replay_pass"]),
            budget_units=float(payload["budget_units"]),
            runtime_seconds=float(payload["runtime_seconds"]),
            artifact_digest_sha256=str(payload["artifact_digest_sha256"]),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(slots=True)
class MetricDelta:
    metric: str
    direction: str
    candidate_mean: float
    baseline_mean: float
    paired_delta: float
    confidence_low: float
    confidence_high: float
    wins: int
    ties: int
    losses: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "direction": self.direction,
            "candidate_mean": self.candidate_mean,
            "baseline_mean": self.baseline_mean,
            "paired_delta": self.paired_delta,
            "confidence_low": self.confidence_low,
            "confidence_high": self.confidence_high,
            "wins": self.wins,
            "ties": self.ties,
            "losses": self.losses,
        }


@dataclass(slots=True)
class BenchmarkComparison:
    candidate_name: str
    baseline_name: str
    suite_id: str
    suite_version: str
    paired_case_count: int
    equal_budget: bool
    all_replay_pass: bool
    candidate_false_promotions: int
    baseline_false_promotions: int
    deltas: tuple[MetricDelta, ...]
    qualification_state: str
    superiority_claim_allowed: bool
    reasons: tuple[str, ...]
    required_minimum_pairs: int
    bootstrap_samples: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "baseline_name": self.baseline_name,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "paired_case_count": self.paired_case_count,
            "equal_budget": self.equal_budget,
            "all_replay_pass": self.all_replay_pass,
            "candidate_false_promotions": self.candidate_false_promotions,
            "baseline_false_promotions": self.baseline_false_promotions,
            "deltas": [item.to_dict() for item in self.deltas],
            "qualification_state": self.qualification_state,
            "superiority_claim_allowed": self.superiority_claim_allowed,
            "reasons": list(self.reasons),
            "required_minimum_pairs": self.required_minimum_pairs,
            "bootstrap_samples": self.bootstrap_samples,
            "claim_boundary": (
                "The comparison applies only to this pinned suite, version, budget, "
                "adapter, and set of paired seeds. It is not a universal ranking."
            ),
        }


def _quantile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        return math.nan
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = probability * (len(sorted_values) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction


def _paired_bootstrap_interval(
    values: list[float],
    *,
    samples: int,
    confidence: float,
    seed: int,
) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    rng = random.Random(seed)
    means: list[float] = []
    size = len(values)
    for _ in range(samples):
        means.append(fmean(values[rng.randrange(size)] for _ in range(size)))
    means.sort()
    alpha = (1.0 - confidence) / 2.0
    return _quantile(means, alpha), _quantile(means, 1.0 - alpha)


def compare_agents(
    candidate_results: Iterable[BenchmarkResult],
    baseline_results: Iterable[BenchmarkResult],
    *,
    metric_directions: Mapping[str, str],
    primary_metrics: Iterable[str],
    minimum_pairs: int = 30,
    bootstrap_samples: int = 5000,
    confidence: float = 0.95,
    budget_relative_tolerance: float = 1e-9,
    random_seed: int = 1729,
) -> BenchmarkComparison:
    candidate = list(candidate_results)
    baseline = list(baseline_results)
    if not candidate or not baseline:
        candidate_name = candidate[0].system_name if candidate else "candidate"
        baseline_name = baseline[0].system_name if baseline else "baseline"
        return BenchmarkComparison(
            candidate_name=candidate_name,
            baseline_name=baseline_name,
            suite_id="UNKNOWN",
            suite_version="UNKNOWN",
            paired_case_count=0,
            equal_budget=False,
            all_replay_pass=False,
            candidate_false_promotions=sum(item.false_promotion for item in candidate),
            baseline_false_promotions=sum(item.false_promotion for item in baseline),
            deltas=(),
            qualification_state="INSUFFICIENT_EVIDENCE",
            superiority_claim_allowed=False,
            reasons=("candidate or baseline results are missing",),
            required_minimum_pairs=minimum_pairs,
            bootstrap_samples=bootstrap_samples,
        )

    suite_ids = {item.suite_id for item in (*candidate, *baseline)}
    versions = {item.suite_version for item in (*candidate, *baseline)}
    candidate_names = {item.system_name for item in candidate}
    baseline_names = {item.system_name for item in baseline}
    structural_reasons: list[str] = []
    if len(suite_ids) != 1:
        structural_reasons.append("results do not use one common benchmark suite")
    if len(versions) != 1:
        structural_reasons.append("results do not use one pinned benchmark version")
    if len(candidate_names) != 1 or len(baseline_names) != 1:
        structural_reasons.append("each side must identify exactly one system")

    candidate_map = {item.pair_key: item for item in candidate}
    baseline_map = {item.pair_key: item for item in baseline}
    paired_keys = sorted(candidate_map.keys() & baseline_map.keys())
    if len(candidate_map) != len(candidate):
        structural_reasons.append("candidate has duplicate case/seed records")
    if len(baseline_map) != len(baseline):
        structural_reasons.append("baseline has duplicate case/seed records")
    if candidate_map.keys() != baseline_map.keys():
        structural_reasons.append("candidate and baseline are not fully paired")

    equal_budget = True
    all_replay_pass = True
    for key in paired_keys:
        left = candidate_map[key]
        right = baseline_map[key]
        scale = max(1.0, abs(left.budget_units), abs(right.budget_units))
        if abs(left.budget_units - right.budget_units) > budget_relative_tolerance * scale:
            equal_budget = False
        all_replay_pass = all_replay_pass and left.replay_pass and right.replay_pass
    if not equal_budget:
        structural_reasons.append("paired runs do not have equal declared budgets")
    if not all_replay_pass:
        structural_reasons.append("one or more paired artifacts fail cold replay")
    if len(paired_keys) < minimum_pairs:
        structural_reasons.append(
            f"only {len(paired_keys)} paired runs; at least {minimum_pairs} are required"
        )

    primary = tuple(primary_metrics)
    missing_directions = set(primary) - set(metric_directions)
    if missing_directions:
        structural_reasons.append(
            f"primary metrics lack directions: {sorted(missing_directions)}"
        )

    deltas: list[MetricDelta] = []
    for metric, direction in metric_directions.items():
        if direction not in {"maximize", "minimize"}:
            raise ValueError(f"invalid direction for {metric}: {direction}")
        if any(
            metric not in candidate_map[key].metrics
            or metric not in baseline_map[key].metrics
            for key in paired_keys
        ):
            structural_reasons.append(f"paired records are missing metric {metric}")
            continue
        candidate_values = [candidate_map[key].metrics[metric] for key in paired_keys]
        baseline_values = [baseline_map[key].metrics[metric] for key in paired_keys]
        signed = [
            (left - right) if direction == "maximize" else (right - left)
            for left, right in zip(candidate_values, baseline_values)
        ]
        low, high = _paired_bootstrap_interval(
            signed,
            samples=bootstrap_samples,
            confidence=confidence,
            seed=random_seed + sum(ord(char) for char in metric),
        )
        tolerance = 1e-12
        deltas.append(
            MetricDelta(
                metric=metric,
                direction=direction,
                candidate_mean=fmean(candidate_values) if candidate_values else math.nan,
                baseline_mean=fmean(baseline_values) if baseline_values else math.nan,
                paired_delta=fmean(signed) if signed else math.nan,
                confidence_low=low,
                confidence_high=high,
                wins=sum(value > tolerance for value in signed),
                ties=sum(abs(value) <= tolerance for value in signed),
                losses=sum(value < -tolerance for value in signed),
            )
        )

    candidate_false_promotions = sum(
        candidate_map[key].false_promotion for key in paired_keys
    )
    baseline_false_promotions = sum(
        baseline_map[key].false_promotion for key in paired_keys
    )
    if candidate_false_promotions:
        structural_reasons.append(
            f"candidate made {candidate_false_promotions} false claim promotions"
        )

    delta_by_name = {item.metric: item for item in deltas}
    nonpositive_primary = [
        metric
        for metric in primary
        if metric not in delta_by_name
        or not math.isfinite(delta_by_name[metric].confidence_low)
        or delta_by_name[metric].confidence_low <= 0.0
    ]
    if nonpositive_primary:
        structural_reasons.append(
            "positive confidence lower bound is absent for primary metrics: "
            + ", ".join(nonpositive_primary)
        )

    if structural_reasons:
        qualification = (
            "NOT_SUPERIOR"
            if len(paired_keys) >= minimum_pairs and candidate_false_promotions
            else "INSUFFICIENT_EVIDENCE"
        )
        allowed = False
    else:
        qualification = "QUALIFIED_SUPERIOR_ON_PINNED_SUITE"
        allowed = True

    return BenchmarkComparison(
        candidate_name=next(iter(candidate_names), "candidate"),
        baseline_name=next(iter(baseline_names), "baseline"),
        suite_id=next(iter(suite_ids), "UNKNOWN") if len(suite_ids) == 1 else "MIXED",
        suite_version=next(iter(versions), "UNKNOWN") if len(versions) == 1 else "MIXED",
        paired_case_count=len(paired_keys),
        equal_budget=equal_budget,
        all_replay_pass=all_replay_pass,
        candidate_false_promotions=candidate_false_promotions,
        baseline_false_promotions=baseline_false_promotions,
        deltas=tuple(deltas),
        qualification_state=qualification,
        superiority_claim_allowed=allowed,
        reasons=tuple(structural_reasons) if structural_reasons else (
            "all pre-registered qualification gates passed",
        ),
        required_minimum_pairs=minimum_pairs,
        bootstrap_samples=bootstrap_samples,
    )


def compare_against_all(
    candidate_results: Iterable[BenchmarkResult],
    baselines: Mapping[str, Iterable[BenchmarkResult]],
    **kwargs: Any,
) -> dict[str, Any]:
    candidate = list(candidate_results)
    comparisons = {
        name: compare_agents(candidate, list(results), **kwargs).to_dict()
        for name, results in sorted(baselines.items())
    }
    allowed = bool(comparisons) and all(
        result["superiority_claim_allowed"] for result in comparisons.values()
    )
    return {
        "comparisons": comparisons,
        "all_baselines_qualified": allowed,
        "permitted_claim": (
            "The candidate is superior to every listed baseline on the pinned, "
            "equal-budget benchmark protocol."
            if allowed
            else "No all-baseline superiority claim is permitted."
        ),
        "claim_boundary": (
            "Unlisted systems, changed versions, other budgets, and other theorem "
            "distributions are outside the comparison."
        ),
    }


def load_results(path: str | Path) -> list[BenchmarkResult]:
    source = Path(path)
    if source.suffix == ".jsonl":
        payloads = [
            json.loads(line)
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        value = json.loads(source.read_text(encoding="utf-8"))
        payloads = value if isinstance(value, list) else value.get("results", [])
    return [BenchmarkResult.from_dict(item) for item in payloads]


def save_results(results: Iterable[BenchmarkResult], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {"schema_version": "1.0", "results": [item.to_dict() for item in results]},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return target
