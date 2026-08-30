"""Structured falsification contracts and route-level evaluation records.

This module is the first v0.3-core slice of DEV_PATH_V03 F0/F0.5/F1. It
turns a route's prose kill-test into a versioned, content-addressed contract
and records what was *actually* tested. Records live inside ResearchTrace
metadata for backward-compatible v0.2 serialization; callers must use the
helpers here rather than inventing a second "kill test executed" flag.

Trust semantics are deliberately asymmetric:
- deterministic bounded checks may produce PASS_BOUNDED;
- property/random testing without a counterexample is always INCONCLUSIVE;
- COUNTEREXAMPLE requires an independently verified witness artifact;
- UNKNOWN/timeout/tool failures never become PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping

from .schema import ToolCallRecord, ToolStatus, canonical_json, digest_json, utc_now

if TYPE_CHECKING:
    from .trace import ResearchTrace


class FalsificationContractError(ValueError):
    """Raised when a kill-test/evaluation contract is unsafe or inconsistent."""


class KillTestKind(str, Enum):
    ENUMERATION = "enumeration"
    PROPERTY_RANDOM = "property_random"
    SAT_SEARCH = "sat_search"
    INSTANCE_EVAL = "instance_eval"


class RouteEvaluationOutcome(str, Enum):
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    PASS_BOUNDED = "PASS_BOUNDED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"


def _strict_keys(cls: type[Any], payload: Mapping[str, Any]) -> None:
    allowed = {item.name for item in fields(cls)}
    unknown = set(payload) - allowed
    if unknown:
        raise FalsificationContractError(
            f"unknown fields for {cls.__name__}: {sorted(unknown)}"
        )


@dataclass(slots=True, frozen=True)
class KillTestSpec:
    kind: KillTestKind
    generator_spec: Mapping[str, Any]
    discriminator_spec: Mapping[str, Any]
    tested_scope: str
    version: str = "1"
    max_cases: int | None = None
    seed: int | None = None
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.tested_scope.strip():
            raise FalsificationContractError("tested_scope must be explicit")
        if not self.version.strip():
            raise FalsificationContractError("kill-test version must be non-empty")
        if self.max_cases is not None and self.max_cases <= 0:
            raise FalsificationContractError("max_cases must be positive")
        try:
            canonical_json(dict(self.generator_spec))
            canonical_json(dict(self.discriminator_spec))
        except (TypeError, ValueError) as exc:
            raise FalsificationContractError(
                "generator_spec and discriminator_spec must be canonical JSON values"
            ) from exc

    def semantic_dict(self) -> dict[str, Any]:
        """Return only fields that define the executable mathematical contract.

        created_at is provenance, not semantics. Including it in the spec hash
        would make two byte-for-byte equivalent kill tests receive different
        identities merely because they were constructed at different times.
        """

        return {
            "kind": self.kind.value,
            "generator_spec": dict(self.generator_spec),
            "discriminator_spec": dict(self.discriminator_spec),
            "tested_scope": self.tested_scope,
            "version": self.version,
            "max_cases": self.max_cases,
            "seed": self.seed,
        }

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.semantic_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self.semantic_dict(), "created_at": self.created_at}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "KillTestSpec":
        _strict_keys(cls, payload)
        generator = payload.get("generator_spec", {})
        discriminator = payload.get("discriminator_spec", {})
        if not isinstance(generator, Mapping) or not isinstance(discriminator, Mapping):
            raise FalsificationContractError("kill-test specs must be JSON objects")
        return cls(
            kind=KillTestKind(str(payload["kind"])),
            generator_spec=dict(generator),
            discriminator_spec=dict(discriminator),
            tested_scope=str(payload["tested_scope"]),
            version=str(payload.get("version", "1")),
            max_cases=(
                int(payload["max_cases"])
                if payload.get("max_cases") is not None
                else None
            ),
            seed=(int(payload["seed"]) if payload.get("seed") is not None else None),
            created_at=str(payload.get("created_at") or utc_now()),
        )


@dataclass(slots=True, frozen=True)
class RouteEvaluationRecord:
    evaluation_id: str
    route_id: str
    route_revision: int
    claim_id: str
    claim_revision: int
    kill_test_spec_digest: str
    tool_call_id: str
    outcome: RouteEvaluationOutcome
    tested_scope: str
    verifier_group: str
    replay_command: str
    witness_artifact_id: str = ""
    witness_verified: bool = False
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.evaluation_id.strip() or not self.route_id.strip() or not self.claim_id.strip():
            raise FalsificationContractError("evaluation, route and claim ids are required")
        if self.route_revision < 0 or self.claim_revision < 0:
            raise FalsificationContractError("revisions cannot be negative")
        if len(self.kill_test_spec_digest) != 64:
            raise FalsificationContractError("kill_test_spec_digest must be SHA-256")
        if not self.tested_scope.strip():
            raise FalsificationContractError("tested_scope must be explicit")
        if self.outcome is RouteEvaluationOutcome.COUNTEREXAMPLE:
            if not self.witness_artifact_id.strip() or not self.witness_verified:
                raise FalsificationContractError(
                    "COUNTEREXAMPLE requires an independently verified witness artifact"
                )
            if not self.verifier_group.strip():
                raise FalsificationContractError(
                    "COUNTEREXAMPLE requires a verifier independence group"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "route_id": self.route_id,
            "route_revision": self.route_revision,
            "claim_id": self.claim_id,
            "claim_revision": self.claim_revision,
            "kill_test_spec_digest": self.kill_test_spec_digest,
            "tool_call_id": self.tool_call_id,
            "outcome": self.outcome.value,
            "tested_scope": self.tested_scope,
            "verifier_group": self.verifier_group,
            "replay_command": self.replay_command,
            "witness_artifact_id": self.witness_artifact_id,
            "witness_verified": self.witness_verified,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RouteEvaluationRecord":
        _strict_keys(cls, payload)
        return cls(
            evaluation_id=str(payload["evaluation_id"]),
            route_id=str(payload["route_id"]),
            route_revision=int(payload.get("route_revision", 0)),
            claim_id=str(payload["claim_id"]),
            claim_revision=int(payload.get("claim_revision", 0)),
            kill_test_spec_digest=str(payload["kill_test_spec_digest"]),
            tool_call_id=str(payload["tool_call_id"]),
            outcome=RouteEvaluationOutcome(str(payload["outcome"])),
            tested_scope=str(payload["tested_scope"]),
            verifier_group=str(payload.get("verifier_group", "")),
            replay_command=str(payload.get("replay_command", "")),
            witness_artifact_id=str(payload.get("witness_artifact_id", "")),
            witness_verified=bool(payload.get("witness_verified", False)),
            created_at=str(payload.get("created_at") or utc_now()),
        )


_KILL_TESTS_KEY = "v03_kill_test_specs"
_ROUTE_EVALUATIONS_KEY = "v03_route_evaluations"


def attach_kill_test_spec(trace: "ResearchTrace", route_id: str, spec: KillTestSpec) -> None:
    """Attach one canonical spec to a route without changing v0.2 trace schema."""

    if route_id not in trace.routes:
        raise FalsificationContractError(f"unknown route: {route_id}")
    store = trace.metadata.setdefault(_KILL_TESTS_KEY, {})
    if not isinstance(store, dict):
        raise FalsificationContractError("kill-test metadata store is malformed")
    route = trace.routes[route_id]
    store[route_id] = {
        "route_revision": 0,
        "route_updated_at": route.updated_at,
        "spec_digest_sha256": spec.digest_sha256,
        "spec": spec.to_dict(),
    }
    trace.updated_at = utc_now()


def get_kill_test_spec(trace: "ResearchTrace", route_id: str) -> KillTestSpec | None:
    store = trace.metadata.get(_KILL_TESTS_KEY, {})
    if not isinstance(store, Mapping):
        return None
    raw = store.get(route_id)
    if not isinstance(raw, Mapping):
        return None
    spec = raw.get("spec")
    if not isinstance(spec, Mapping):
        return None
    parsed = KillTestSpec.from_dict(spec)
    expected = str(raw.get("spec_digest_sha256", ""))
    if expected and parsed.digest_sha256 != expected:
        raise FalsificationContractError(f"kill-test spec digest drift for route {route_id}")
    return parsed


def iter_route_evaluations(trace: "ResearchTrace") -> tuple[RouteEvaluationRecord, ...]:
    values = trace.metadata.get(_ROUTE_EVALUATIONS_KEY, [])
    if not isinstance(values, list):
        raise FalsificationContractError("route evaluation metadata store is malformed")
    records: list[RouteEvaluationRecord] = []
    for raw in values:
        if not isinstance(raw, Mapping):
            raise FalsificationContractError("route evaluation entry must be an object")
        records.append(RouteEvaluationRecord.from_dict(raw))
    return tuple(records)


def record_route_evaluation(trace: "ResearchTrace", record: RouteEvaluationRecord) -> None:
    if record.route_id not in trace.routes:
        raise FalsificationContractError(f"unknown route: {record.route_id}")
    if record.claim_id not in trace.claims:
        raise FalsificationContractError(f"unknown claim: {record.claim_id}")
    if record.tool_call_id not in trace.tool_calls:
        raise FalsificationContractError(f"unknown tool call: {record.tool_call_id}")
    claim = trace.claims[record.claim_id]
    if record.claim_revision != claim.revision:
        raise FalsificationContractError(
            f"evaluation claim revision {record.claim_revision} is stale; current={claim.revision}"
        )
    spec = get_kill_test_spec(trace, record.route_id)
    if spec is None:
        raise FalsificationContractError(
            f"route {record.route_id} has no structured KillTestSpec"
        )
    if spec.digest_sha256 != record.kill_test_spec_digest:
        raise FalsificationContractError("evaluation does not match the current kill-test spec")
    existing = {item.evaluation_id for item in iter_route_evaluations(trace)}
    if record.evaluation_id in existing:
        raise FalsificationContractError(f"duplicate route evaluation: {record.evaluation_id}")
    store = trace.metadata.setdefault(_ROUTE_EVALUATIONS_KEY, [])
    if not isinstance(store, list):
        raise FalsificationContractError("route evaluation metadata store is malformed")
    store.append(record.to_dict())
    trace.updated_at = utc_now()


def evaluation_from_tool_call(
    trace: "ResearchTrace",
    *,
    evaluation_id: str,
    route_id: str,
    claim_id: str,
    tool_call: ToolCallRecord,
    verified_counterexample_artifact_id: str = "",
    verifier_group: str = "",
) -> RouteEvaluationRecord:
    spec = get_kill_test_spec(trace, route_id)
    if spec is None:
        raise FalsificationContractError(f"route {route_id} has no structured KillTestSpec")
    claim = trace.claims[claim_id]
    counterexample = bool(verified_counterexample_artifact_id)
    if counterexample:
        outcome = RouteEvaluationOutcome.COUNTEREXAMPLE
    elif tool_call.status is ToolStatus.ERROR:
        outcome = RouteEvaluationOutcome.ERROR
    elif spec.kind is KillTestKind.PROPERTY_RANDOM:
        # "No counterexample in random trials" never receives PASS semantics.
        outcome = RouteEvaluationOutcome.INCONCLUSIVE
    elif tool_call.status is ToolStatus.PASS:
        outcome = RouteEvaluationOutcome.PASS_BOUNDED
    else:
        # A generic FAIL is not automatically a mathematical counterexample;
        # it needs an independently checked witness artifact first.
        outcome = RouteEvaluationOutcome.INCONCLUSIVE
    return RouteEvaluationRecord(
        evaluation_id=evaluation_id,
        route_id=route_id,
        route_revision=0,
        claim_id=claim_id,
        claim_revision=claim.revision,
        kill_test_spec_digest=spec.digest_sha256,
        tool_call_id=tool_call.call_id,
        outcome=outcome,
        tested_scope=spec.tested_scope,
        verifier_group=verifier_group or tool_call.independence_group,
        replay_command=tool_call.replay_command,
        witness_artifact_id=verified_counterexample_artifact_id,
        witness_verified=counterexample,
    )


def qualifying_evaluation_for_route(
    trace: "ResearchTrace", route_id: str, claim_id: str
) -> RouteEvaluationRecord | None:
    claim = trace.claims[claim_id]
    spec = get_kill_test_spec(trace, route_id)
    if spec is None:
        return None
    candidates = [
        item
        for item in iter_route_evaluations(trace)
        if item.route_id == route_id
        and item.claim_id == claim_id
        and item.claim_revision == claim.revision
        and item.kill_test_spec_digest == spec.digest_sha256
        and item.outcome is RouteEvaluationOutcome.PASS_BOUNDED
    ]
    return candidates[-1] if candidates else None


def promotion_route_blockers(trace: "ResearchTrace", claim_id: str) -> tuple[str, ...]:
    """Return structured active routes lacking a current PASS_BOUNDED record.

    Legacy v0.2 routes that only have the historical prose `kill_test` field are
    deliberately ignored here. This makes F2 opt-in by attaching KillTestSpec,
    preserving old traces while making every structured v0.3 route fail closed.
    """

    claim = trace.claims[claim_id]
    blockers: list[str] = []
    for route_id in claim.route_ids:
        route = trace.routes.get(route_id)
        if route is None or route.status.value != "ACTIVE":
            continue
        if get_kill_test_spec(trace, route_id) is None:
            continue
        if qualifying_evaluation_for_route(trace, route_id, claim_id) is None:
            blockers.append(route_id)
    return tuple(blockers)
