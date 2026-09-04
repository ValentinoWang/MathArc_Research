"""Crash recovery plans rooted at the last complete generation commit."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ..schema import digest_json


class RecoveryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    runtime_run_id: str
    generation_id: str
    next_generation_id: str
    commit_digest: str
    actions: tuple[str, ...]
    retryable_failures: tuple[str, ...] = ()
    rejected_failures: tuple[str, ...] = ()
    resulting_state: str = "RUNNING"
    plan_digest: str = ""

    def __post_init__(self) -> None:
        if not self.plan_digest:
            object.__setattr__(self, "plan_digest", digest_json(self.to_dict(include_digest=False)))

    @property
    def idempotency_key(self) -> str:
        return f"{self.runtime_run_id}+{self.generation_id}"

    def replay(self) -> "RecoveryPlan":
        return RecoveryPlan.from_dict(self.to_dict())

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {"runtime_run_id": self.runtime_run_id, "generation_id": self.generation_id,
                 "next_generation_id": self.next_generation_id, "commit_digest": self.commit_digest,
                 "actions": list(self.actions), "retryable_failures": list(self.retryable_failures),
                 "rejected_failures": list(self.rejected_failures), "resulting_state": self.resulting_state}
        if include_digest: value["plan_digest"] = self.plan_digest
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RecoveryPlan": return cls(**{k: value[k] for k in value if k != "plan_digest"}, plan_digest=str(value.get("plan_digest", "")))

    @classmethod
    def from_commits(cls, commits: Iterable[Any] | Any, **kwargs: Any) -> "RecoveryPlan":
        return build_recovery_plan(commits, **kwargs)


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value.to_dict() if hasattr(value, "to_dict") else value)


def build_recovery_plan(commits: Iterable[Any] | Any, *, runtime_run_id: str | None = None,
                        expected: Mapping[str, Any] | None = None, expected_snapshot: Any | None = None,
                        current_inputs: Any | None = None, max_retries: int = 1) -> RecoveryPlan:
    """Build a deterministic plan. ``expected`` pins task/source/evaluator/tool/contract digests."""
    if hasattr(commits, "state"):
        commits = commits.state.get("commits", [])
    complete = [_as_dict(item) for item in commits if _as_dict(item).get("complete", True)]
    if not complete: raise RecoveryError("no complete GenerationCommit available for recovery")
    commit = complete[-1]
    run_id = runtime_run_id or commit.get("runtime_run_id")
    if not run_id: raise RecoveryError("runtime_run_id is required")
    expected_values = dict(expected or {})
    if expected_snapshot is not None:
        expected_values["snapshot_digest"] = digest_json(expected_snapshot.to_dict() if hasattr(expected_snapshot, "to_dict") else expected_snapshot)
    if current_inputs is not None:
        expected_values["snapshot_digest"] = digest_json(current_inputs.to_dict() if hasattr(current_inputs, "to_dict") else current_inputs)
    for key, expected_value in expected_values.items():
        if key in commit and commit.get(key) != expected_value:
            raise RecoveryError(f"recovery identity mismatch for {key}")
    generation = str(commit.get("generation_id", ""))
    if not generation: raise RecoveryError("generation_id is required")
    number = int(generation[1:]) if generation[1:].isdigit() and generation[:1].lower() == "g" else None
    next_generation = f"g{number + 1}" if number is not None else f"{generation}.next"
    failures = commit.get("failures", commit.get("failure_classifications", [])) or []
    retryable, rejected = [], []
    for failure in failures:
        item = _as_dict(failure) if not isinstance(failure, str) else {"failure_class": failure}
        target = retryable if item.get("retryable", item.get("failure_class") in {"TIMEOUT", "TIMED_OUT", "RETRYABLE_FAILURE"}) else rejected
        target.append(str(item.get("execution_id", item.get("failure_class", "failure"))))
    actions = tuple(["resume_from_commit", "start_generation"] + (["retry_failures"] if retryable and max_retries > 0 else []))
    return RecoveryPlan(run_id, generation, next_generation, str(commit.get("commit_digest", digest_json(commit))), actions,
                        tuple(sorted(retryable)), tuple(sorted(rejected)), "RUNNING")


generate_recovery_plan = build_recovery_plan


def recover_from_store(store: Any, **kwargs: Any) -> RecoveryPlan:
    return build_recovery_plan(store, **kwargs)


class RecoveryPlanner:
    def __init__(self, store: Any) -> None:
        self.store = store

    def plan(self, **kwargs: Any) -> RecoveryPlan:
        return build_recovery_plan(self.store, **kwargs)




__all__ = ["RecoveryError", "RecoveryPlan", "RecoveryPlanner", "build_recovery_plan", "generate_recovery_plan", "recover_from_store"]
