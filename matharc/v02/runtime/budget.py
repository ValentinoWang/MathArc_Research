"""Runtime resource accounting and deterministic semantic de-duplication."""
from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from typing import Any, Mapping


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def semantic_experiment_key(experiment: Any, *, snapshot_digest: str | None = None) -> str:
    """Return a stable key for the meaning of an experiment, excluding run IDs."""
    if hasattr(experiment, "to_dict"):
        experiment = experiment.to_dict()
    elif hasattr(experiment, "__dict__"):
        experiment = vars(experiment)
    if isinstance(experiment, Mapping):
        identity_fields = {"execution_id", "run_id", "attempt", "worker_id", "member_id", "id", "task_id", "created_at"}
        stripped = {k: v for k, v in experiment.items() if k not in identity_fields}
        # An identity-only task still denotes a distinct work item; retain it
        # instead of collapsing every such task into the same empty payload.
        experiment = stripped if stripped else dict(experiment)
    payload = {"experiment": experiment, "snapshot_digest": snapshot_digest}
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ResourceReceipt:
    execution_id: str
    wall_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    status: str = "completed"
    semantic_key: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise ValueError("execution_id is required")
        for name in ("wall_seconds", "cost_usd"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, execution_id: str | None = None) -> "ResourceReceipt":
        return cls(
            execution_id=execution_id or value.get("execution_id", ""),
            wall_seconds=float(value.get("wall_seconds", value.get("duration_seconds", 0.0)) or 0.0),
            input_tokens=int(value.get("input_tokens", 0) or 0),
            output_tokens=int(value.get("output_tokens", 0) or 0),
            cost_usd=float(value.get("cost_usd", 0.0) or 0.0),
            status=str(value.get("status", "completed")),
            semantic_key=value.get("semantic_key"),
        )


@dataclass(slots=True)
class ResourceLedger:
    wall_seconds_limit: float | None = None
    input_token_limit: int | None = None
    output_token_limit: int | None = None
    cost_usd_limit: float | None = None
    spent_wall_seconds: float = 0.0
    spent_input_tokens: int = 0
    spent_output_tokens: int = 0
    spent_cost_usd: float = 0.0
    receipts: list[ResourceReceipt] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        for name in ("wall_seconds_limit", "cost_usd_limit", "input_token_limit", "output_token_limit"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
                raise ValueError(f"{name} must be non-negative when provided")

    def record_receipt(self, receipt: ResourceReceipt | Mapping[str, Any]) -> ResourceReceipt:
        """Charge measured values from an execution receipt; self-reports are ignored."""
        if isinstance(receipt, ResourceReceipt):
            item = receipt
        elif isinstance(receipt, Mapping):
            item = ResourceReceipt.from_mapping(receipt)
        else:
            # Accept the canonical WorkerExecutionResult protocol without
            # importing contracts.py (which would create a runtime cycle).
            item = ResourceReceipt(
                execution_id=str(getattr(receipt, "execution_id", "")),
                wall_seconds=float(getattr(receipt, "elapsed_seconds", 0.0) or 0.0),
                status=str(getattr(getattr(receipt, "status", None), "value", getattr(receipt, "status", "completed"))),
            )
        with self._lock:
            if any(existing.execution_id == item.execution_id for existing in self.receipts):
                return item
            self.receipts.append(item)
            self.spent_wall_seconds += float(item.wall_seconds)
            self.spent_input_tokens += item.input_tokens
            self.spent_output_tokens += item.output_tokens
            self.spent_cost_usd += float(item.cost_usd)
        return item

    charge = record_receipt
    record_execution = record_receipt

    def exhausted(self) -> bool:
        return (
            (self.wall_seconds_limit is not None and self.spent_wall_seconds >= self.wall_seconds_limit)
            or (self.input_token_limit is not None and self.spent_input_tokens >= self.input_token_limit)
            or (self.output_token_limit is not None and self.spent_output_tokens >= self.output_token_limit)
            or (self.cost_usd_limit is not None and self.spent_cost_usd >= self.cost_usd_limit)
        )

    def to_dict(self) -> dict[str, Any]:
        return {"limits": {"wall_seconds": self.wall_seconds_limit, "input_tokens": self.input_token_limit, "output_tokens": self.output_token_limit, "cost_usd": self.cost_usd_limit}, "spent": {"wall_seconds": self.spent_wall_seconds, "input_tokens": self.spent_input_tokens, "output_tokens": self.spent_output_tokens, "cost_usd": self.spent_cost_usd}, "receipts": [r.__dict__ if hasattr(r, "__dict__") else {"execution_id": r.execution_id, "wall_seconds": r.wall_seconds, "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "cost_usd": r.cost_usd, "status": r.status, "semantic_key": r.semantic_key} for r in self.receipts], "exhausted": self.exhausted()}


class SemanticDeduplicator:
    """Thread-safe claim-once registry for semantic experiment identities."""
    def __init__(self) -> None:
        self._seen: dict[str, str] = {}
        self._lock = threading.Lock()

    def claim(self, experiment: Any, *, execution_id: str, snapshot_digest: str | None = None) -> bool:
        key = semantic_experiment_key(experiment, snapshot_digest=snapshot_digest)
        with self._lock:
            if key in self._seen:
                return False
            self._seen[key] = execution_id
            return True

    def seen(self, experiment: Any, *, snapshot_digest: str | None = None) -> bool:
        return semantic_experiment_key(experiment, snapshot_digest=snapshot_digest) in self._seen

    def execution_for(self, experiment: Any, *, snapshot_digest: str | None = None) -> str | None:
        return self._seen.get(semantic_experiment_key(experiment, snapshot_digest=snapshot_digest))

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(self._seen)


BudgetLedger = ResourceLedger
semantic_key = semantic_experiment_key

__all__ = ["ResourceReceipt", "ResourceLedger", "BudgetLedger", "SemanticDeduplicator", "semantic_experiment_key", "semantic_key"]
