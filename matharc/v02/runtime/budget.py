"""Runtime resource accounting and deterministic semantic de-duplication."""
from __future__ import annotations

import hashlib
import json
import math
import threading
from dataclasses import dataclass, field
from typing import Any, Mapping


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _finite_non_negative(value: Any, name: str, *, integer: bool = False) -> int | float:
    """Validate a budget/receipt number before it can affect admission."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a non-negative number")
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    if integer and not isinstance(value, int):
        raise ValueError(f"{name} must be a non-negative integer")
    return int(value) if integer else float(value)


def _normalise_budget(value: Mapping[str, Any] | None) -> dict[str, float | int]:
    """Map declaration aliases to ledger dimensions and reject malformed input."""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("budget must be a mapping")
    aliases = {
        "wall_seconds": ("wall_seconds", "max_seconds", "timeout_seconds"),
        "input_tokens": ("input_tokens", "max_input_tokens"),
        "output_tokens": ("output_tokens", "max_output_tokens"),
        "cost_usd": ("cost_usd", "max_cost", "max_cost_usd"),
    }
    known = {name for names in aliases.values() for name in names}
    unknown = set(value) - known
    if unknown:
        raise ValueError(f"unsupported budget dimensions: {sorted(unknown)}")
    result: dict[str, float | int] = {}
    for dimension, names in aliases.items():
        present = [name for name in names if name in value and value[name] is not None]
        if not present:
            continue
        first = value[present[0]]
        # Conflicting aliases are unsafe: do not silently choose one.
        if any(value[name] != first for name in present[1:]):
            raise ValueError(f"conflicting budget declarations for {dimension}")
        result[dimension] = _finite_non_negative(first, dimension, integer=dimension.endswith("tokens"))
    return result


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
            _finite_non_negative(value, name)
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, execution_id: str | None = None) -> "ResourceReceipt":
        if not isinstance(value, Mapping):
            raise ValueError("resource receipt must be a mapping")
        def selected(names: tuple[str, ...], default: Any) -> Any:
            present = [name for name in names if name in value and value[name] is not None]
            if not present:
                return default
            first = value[present[0]]
            if any(value[name] != first for name in present[1:]):
                raise ValueError(f"conflicting resource receipt fields: {', '.join(present)}")
            return first
        wall = _finite_non_negative(selected(("wall_seconds", "duration_seconds"), 0.0), "wall_seconds")
        inputs = _finite_non_negative(selected(("input_tokens",), 0), "input_tokens", integer=True)
        outputs = _finite_non_negative(selected(("output_tokens",), 0), "output_tokens", integer=True)
        cost = _finite_non_negative(selected(("cost_usd",), 0.0), "cost_usd")
        return cls(
            execution_id=execution_id or value.get("execution_id", ""),
            wall_seconds=wall,
            input_tokens=inputs,
            output_tokens=outputs,
            cost_usd=cost,
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
    _reservations: dict[str, dict[str, float | int]] = field(default_factory=dict, repr=False)
    runtime_store: Any | None = field(default=None, repr=False)
    _persist_receipts: bool = field(default=True, repr=False)

    def __post_init__(self) -> None:
        for name in ("wall_seconds_limit", "cost_usd_limit", "input_token_limit", "output_token_limit"):
            value = getattr(self, name)
            if value is not None:
                _finite_non_negative(value, name, integer=name.endswith("token_limit"))
        if self.runtime_store is not None:
            self._persist_receipts = False
            for event in getattr(self.runtime_store, "events", ()):
                if getattr(event, "event_type", None) != "SCHEDULER_RECEIPT":
                    continue
                payload = dict(getattr(event, "payload", {}) or {})
                try:
                    self.record_receipt(payload)
                except (TypeError, ValueError):
                    raise ValueError("invalid persisted scheduler receipt")
            self._persist_receipts = True

    def record_receipt(self, receipt: ResourceReceipt | Mapping[str, Any], *, strict: bool = False) -> ResourceReceipt:
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
            existing = next((existing for existing in self.receipts if existing.execution_id == item.execution_id), None)
            if existing is not None:
                if strict and existing != item:
                    raise ValueError(f"conflicting resource receipt for execution_id: {item.execution_id}")
                return existing
            self._reservations.pop(item.execution_id, None)
            self.receipts.append(item)
            self.spent_wall_seconds += float(item.wall_seconds)
            self.spent_input_tokens += item.input_tokens
            self.spent_output_tokens += item.output_tokens
            self.spent_cost_usd += float(item.cost_usd)
            store = self.runtime_store
            persist = self._persist_receipts
        if persist and store is not None:
            append = getattr(store, "append_event", None) or getattr(store, "append", None)
            if callable(append):
                append("SCHEDULER_RECEIPT", {
                    "execution_id": item.execution_id,
                    "wall_seconds": item.wall_seconds,
                    "input_tokens": item.input_tokens,
                    "output_tokens": item.output_tokens,
                    "cost_usd": item.cost_usd,
                    "status": item.status,
                    "semantic_key": item.semantic_key,
                })
        return item

    def admit(self, declaration: Mapping[str, Any] | ResourceReceipt | None = None, *, execution_id: str) -> bool:
        """Atomically reserve a declared upper bound before a worker starts."""
        if not isinstance(execution_id, str) or not execution_id.strip():
            raise ValueError("execution_id is required for admission")
        if isinstance(declaration, ResourceReceipt):
            values = {"wall_seconds": declaration.wall_seconds, "input_tokens": declaration.input_tokens,
                      "output_tokens": declaration.output_tokens, "cost_usd": declaration.cost_usd}
        else:
            values = _normalise_budget(declaration)
        with self._lock:
            if execution_id in self._reservations:
                return self._reservations[execution_id] == values
            totals = {
                "wall_seconds": self.spent_wall_seconds + sum(float(item.get("wall_seconds", 0)) for item in self._reservations.values()),
                "input_tokens": self.spent_input_tokens + sum(int(item.get("input_tokens", 0)) for item in self._reservations.values()),
                "output_tokens": self.spent_output_tokens + sum(int(item.get("output_tokens", 0)) for item in self._reservations.values()),
                "cost_usd": self.spent_cost_usd + sum(float(item.get("cost_usd", 0)) for item in self._reservations.values()),
            }
            limits = {"wall_seconds": self.wall_seconds_limit, "input_tokens": self.input_token_limit,
                      "output_tokens": self.output_token_limit, "cost_usd": self.cost_usd_limit}
            if any(limit is not None and totals[name] + values.get(name, 0) > limit for name, limit in limits.items()):
                return False
            self._reservations[execution_id] = dict(values)
            return True

    reserve = admit

    def release(self, execution_id: str) -> None:
        with self._lock:
            self._reservations.pop(execution_id, None)

    @property
    def reservations(self) -> dict[str, dict[str, float | int]]:
        with self._lock:
            return {key: dict(value) for key, value in self._reservations.items()}

    def restore_receipt(self, receipt: ResourceReceipt | Mapping[str, Any]) -> ResourceReceipt:
        """Replay a persisted receipt without allowing duplicate charging."""
        return self.record_receipt(receipt)

    def validate_receipt(self, receipt: ResourceReceipt | Mapping[str, Any]) -> ResourceReceipt:
        """Strictly validate and record a receipt, including conflict detection."""
        item = receipt if isinstance(receipt, ResourceReceipt) else ResourceReceipt.from_mapping(receipt)
        with self._lock:
            reservation = self._reservations.get(item.execution_id, {})
            dimensions = {"wall_seconds": item.wall_seconds, "input_tokens": item.input_tokens,
                          "output_tokens": item.output_tokens, "cost_usd": item.cost_usd}
            limits = {"wall_seconds": self.wall_seconds_limit, "input_tokens": self.input_token_limit,
                      "output_tokens": self.output_token_limit, "cost_usd": self.cost_usd_limit}
            if any(name in reservation and value > reservation[name] for name, value in dimensions.items()):
                raise ValueError(f"receipt exceeds admitted declaration for execution_id: {item.execution_id}")
            prior = {"wall_seconds": self.spent_wall_seconds, "input_tokens": self.spent_input_tokens,
                     "output_tokens": self.spent_output_tokens, "cost_usd": self.spent_cost_usd}
            for name, limit in limits.items():
                if limit is not None and prior[name] + dimensions[name] - reservation.get(name, 0) > limit:
                    raise ValueError(f"receipt exceeds remaining runtime budget: {name}")
        return self.record_receipt(item, strict=True)

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
    def __init__(self, runtime_store: Any | None = None) -> None:
        self._seen: dict[str, str] = {}
        self._lock = threading.Lock()
        self.runtime_store = runtime_store
        self._restore(runtime_store)

    def _restore(self, runtime_store: Any | None) -> None:
        if runtime_store is None:
            return
        for event in getattr(runtime_store, "events", ()):
            if getattr(event, "event_type", None) != "SCHEDULER_CLAIMED":
                continue
            payload = dict(getattr(event, "payload", {}) or {})
            key, execution_id = payload.get("semantic_key"), payload.get("execution_id")
            if key and execution_id:
                self._seen[str(key)] = str(execution_id)

    def claim(self, experiment: Any, *, execution_id: str, snapshot_digest: str | None = None,
              runtime_store: Any | None = None) -> bool:
        key = semantic_experiment_key(experiment, snapshot_digest=snapshot_digest)
        with self._lock:
            if key in self._seen:
                return False
            self._seen[key] = execution_id
            store = runtime_store or self.runtime_store
            if store is not None:
                append = getattr(store, "append_event", None) or getattr(store, "append", None)
                if callable(append):
                    append("SCHEDULER_CLAIMED", {"execution_id": execution_id, "semantic_key": key})
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
