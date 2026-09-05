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
    def from_dict(cls, value: Mapping[str, Any]) -> "RecoveryPlan":
        allowed = {"runtime_run_id", "generation_id", "next_generation_id", "commit_digest", "actions",
                   "retryable_failures", "rejected_failures", "resulting_state", "plan_digest"}
        unknown = set(value) - allowed
        if unknown:
            raise RecoveryError(f"unknown recovery plan fields: {sorted(unknown)}")
        required = allowed - {"plan_digest"}
        missing = required - set(value)
        if missing:
            raise RecoveryError(f"missing recovery plan fields: {sorted(missing)}")
        expected = digest_json({key: value[key] for key in required})
        supplied = str(value.get("plan_digest", ""))
        if supplied and supplied != expected:
            raise RecoveryError("recovery plan digest mismatch")
        return cls(**{k: value[k] for k in value if k != "plan_digest"}, plan_digest=expected)

    @classmethod
    def from_commits(cls, commits: Iterable[Any] | Any, **kwargs: Any) -> "RecoveryPlan":
        return build_recovery_plan(commits, **kwargs)


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value.to_dict() if hasattr(value, "to_dict") else value)


def _generation_number(value: str) -> int | None:
    text = str(value)
    return int(text[1:]) if text[:1].lower() == "g" and text[1:].isdigit() else None


def _commit_digest(commit: Mapping[str, Any]) -> str:
    supplied = str(commit.get("commit_digest", ""))
    # Typed commits use a SHA-256 digest over the payload without the digest
    # field.  Legacy compact envelopes may carry an opaque marker (for
    # example, ``commit``), which remains valid for backwards compatibility.
    if supplied and len(supplied) == 64 and "results" in commit:
        expected = digest_json({key: value for key, value in commit.items()
                                if key not in {"commit_digest", "complete"}})
        if supplied != expected:
            raise RecoveryError("generation commit digest mismatch")
        return supplied
    return supplied or digest_json(dict(commit))


def build_recovery_plan(commits: Iterable[Any] | Any, *, runtime_run_id: str | None = None,
                        expected: Mapping[str, Any] | None = None, expected_snapshot: Any | None = None,
                        current_inputs: Any | None = None, max_retries: int = 1) -> RecoveryPlan:
    """Build a deterministic plan. ``expected`` pins task/source/evaluator/tool/contract digests."""
    if hasattr(commits, "state"):
        commits = commits.state.get("commits", [])
    all_commits = [_as_dict(item) for item in commits]
    complete = [item for item in all_commits if item.get("complete", item.get("closed", True))]
    if not complete: raise RecoveryError("no complete GenerationCommit available for recovery")
    # Generation order, rather than append order, is the recovery boundary.
    complete.sort(key=lambda item: (_generation_number(str(item.get("generation_id", "")))
                                   if _generation_number(str(item.get("generation_id", ""))) is not None else -1))
    run_ids = {item.get("runtime_run_id") for item in complete if item.get("runtime_run_id")}
    if runtime_run_id is not None:
        run_ids.add(runtime_run_id)
    if len(run_ids) > 1:
        raise RecoveryError("recovery commits contain multiple runtime_run_id values")
    commit = complete[-1]
    commit_run_id = commit.get("runtime_run_id")
    if runtime_run_id is not None and commit_run_id and runtime_run_id != commit_run_id:
        raise RecoveryError("recovery runtime_run_id does not match commit")
    run_id = runtime_run_id or commit_run_id
    if not run_id: raise RecoveryError("runtime_run_id is required")
    expected_values = dict(expected or {})
    if expected_snapshot is not None:
        expected_values["snapshot_digest"] = digest_json(expected_snapshot.to_dict() if hasattr(expected_snapshot, "to_dict") else expected_snapshot)
    if current_inputs is not None:
        expected_values["snapshot_digest"] = digest_json(current_inputs.to_dict() if hasattr(current_inputs, "to_dict") else current_inputs)
    for key, expected_value in expected_values.items():
        if key not in commit or commit.get(key) != expected_value:
            raise RecoveryError(f"recovery identity mismatch for {key}")
    generation = str(commit.get("generation_id", ""))
    if not generation: raise RecoveryError("generation_id is required")
    # Validate the chain before deriving the next generation.  Parent fields
    # are optional for legacy records, but when present they must bind exactly
    # to the preceding committed generation.
    numeric = [(item, _generation_number(str(item.get("generation_id", "")))) for item in complete]
    numeric = [(item, number) for item, number in numeric if number is not None]
    if numeric:
        for (prior, prior_number), (current, current_number) in zip(numeric, numeric[1:]):
            if current_number != prior_number + 1:
                raise RecoveryError("generation ids must be monotonic and contiguous")
            if "parent_generation_id" in current and current["parent_generation_id"] != prior.get("generation_id"):
                raise RecoveryError("parent_generation_id does not match previous commit")
            if "parent_commit_digest" in current:
                if current["parent_commit_digest"] != _commit_digest(prior):
                    raise RecoveryError("parent_commit_digest does not match previous commit")
    _commit_digest(commit)
    number = _generation_number(generation)
    next_generation = f"g{number + 1}" if number is not None else f"{generation}.next"
    failures = list(commit.get("failures", commit.get("failure_classifications", [])) or [])
    if not failures:
        # GenerationCommit stores authoritative execution outcomes in
        # ``results``.  Reconstruct failure classifications from that source
        # instead of trusting a redundant summary field.
        for result in commit.get("results", ()) or ():
            item = _as_dict(result)
            status = str(item.get("status", "")).upper()
            if status not in {"SUCCEEDED", "SUCCESS"}:
                failures.append(item)
    retryable, rejected = [], []
    for failure in failures:
        item = _as_dict(failure) if not isinstance(failure, str) else {"failure_class": failure}
        failure_class = str(item.get("failure_class", "")).upper()
        target = retryable if item.get("retryable", failure_class in {"TIMEOUT", "TIMED_OUT", "RETRYABLE_FAILURE"}
                              or str(item.get("status", "")).upper() in {"TIMED_OUT", "RETRYABLE_FAILURE"}) else rejected
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
