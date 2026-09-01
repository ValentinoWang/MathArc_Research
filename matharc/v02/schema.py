from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, TypeVar


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class ClaimStatus(_StringEnum):
    PROPOSED = "PROPOSED"
    OPEN = "OPEN"
    CANDIDATE = "CANDIDATE"
    PROVED = "PROVED"
    REFUTED = "REFUTED"
    BLOCKED = "BLOCKED"
    RETRACTED = "RETRACTED"


class RouteStatus(_StringEnum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    FALSIFIED = "FALSIFIED"
    CLOSED = "CLOSED"
    ABANDONED = "ABANDONED"


class EvidenceStatus(_StringEnum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    STALE = "STALE"


class ToolStatus(_StringEnum):
    REQUESTED = "REQUESTED"
    RUNNING = "RUNNING"
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class SpawnDecisionStatus(_StringEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class FailureClass(_StringEnum):
    FALSE_STATEMENT = "FALSE_STATEMENT"
    SCOPE_OVERREACH = "SCOPE_OVERREACH"
    FINITE_TO_GLOBAL = "FINITE_TO_GLOBAL"
    HIDDEN_ASSUMPTION = "HIDDEN_ASSUMPTION"
    TYPE_OR_DOMAIN_ERROR = "TYPE_OR_DOMAIN_ERROR"
    DEFINITION_DRIFT = "DEFINITION_DRIFT"
    QUANTIFIER_REVERSAL = "QUANTIFIER_REVERSAL"
    DEPENDENCY_GAP = "DEPENDENCY_GAP"
    NON_INDEPENDENT_CHECKER = "NON_INDEPENDENT_CHECKER"
    NUMERICAL_INSTABILITY = "NUMERICAL_INSTABILITY"
    LITERATURE_MISMATCH = "LITERATURE_MISMATCH"
    ROUTE_DUPLICATION = "ROUTE_DUPLICATION"
    TOOL_OR_CHECKER_BUG = "TOOL_OR_CHECKER_BUG"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    UNKNOWN = "UNKNOWN"


class EvidenceKind(_StringEnum):
    FORMAL_PROOF = "FORMAL_PROOF"
    CHECKED_DERIVATION = "CHECKED_DERIVATION"
    EXACT_CERTIFICATE = "EXACT_CERTIFICATE"
    EXACT_COMPUTATION = "EXACT_COMPUTATION"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    LITERATURE_RESULT = "LITERATURE_RESULT"
    HUMAN_AUDIT = "HUMAN_AUDIT"
    NUMERICAL_EXPERIMENT = "NUMERICAL_EXPERIMENT"
    HEURISTIC = "HEURISTIC"


_FORBIDDEN_REASONING_KEYS = {
    "chain_of_thought",
    "private_chain_of_thought",
    "hidden_reasoning",
    "scratchpad",
    "private_reasoning",
    "token_trace",
}


def _strict_payload(cls: type[Any], payload: Mapping[str, Any]) -> None:
    allowed = {item.name for item in fields(cls)}
    unknown = set(payload) - allowed
    forbidden = set(payload) & _FORBIDDEN_REASONING_KEYS
    if forbidden:
        raise ValueError(
            "private token-by-token reasoning fields are forbidden; use the "
            f"auditable public_reasoning schema instead: {sorted(forbidden)}"
        )
    if unknown:
        raise ValueError(f"unknown fields for {cls.__name__}: {sorted(unknown)}")


_StringEnumT = TypeVar("_StringEnumT", bound=_StringEnum)


def _enum(enum_type: type[_StringEnumT], value: Any) -> _StringEnumT:
    return enum_type(str(value))


def _tuple_of_str(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise ValueError("expected an array of strings, not a string")
    return tuple(str(item) for item in value)


@dataclass(slots=True)
class TheoremContract:
    contract_id: str
    problem: str
    target_claim_ids: tuple[str, ...]
    scope: str
    assumptions: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    non_claims: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "problem": self.problem,
            "target_claim_ids": list(self.target_claim_ids),
            "scope": self.scope,
            "assumptions": list(self.assumptions),
            "success_criteria": list(self.success_criteria),
            "non_claims": list(self.non_claims),
            "source_refs": list(self.source_refs),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TheoremContract":
        _strict_payload(cls, payload)
        return cls(
            contract_id=str(payload["contract_id"]),
            problem=str(payload["problem"]),
            target_claim_ids=_tuple_of_str(payload["target_claim_ids"]),
            scope=str(payload["scope"]),
            assumptions=_tuple_of_str(payload.get("assumptions")),
            success_criteria=_tuple_of_str(payload.get("success_criteria")),
            non_claims=_tuple_of_str(payload.get("non_claims")),
            source_refs=_tuple_of_str(payload.get("source_refs")),
            created_at=str(payload.get("created_at") or utc_now()),
        )


@dataclass(slots=True)
class ClaimRecord:
    claim_id: str
    statement: str
    scope: str
    status: ClaimStatus = ClaimStatus.OPEN
    dependencies: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    route_ids: tuple[str, ...] = ()
    weight: float = 1.0
    critical: bool = False
    boundary: str = ""
    owner: str = ""
    revision: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "scope": self.scope,
            "status": self.status.value,
            "dependencies": list(self.dependencies),
            "evidence_ids": list(self.evidence_ids),
            "route_ids": list(self.route_ids),
            "weight": self.weight,
            "critical": self.critical,
            "boundary": self.boundary,
            "owner": self.owner,
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ClaimRecord":
        _strict_payload(cls, payload)
        return cls(
            claim_id=str(payload["claim_id"]),
            statement=str(payload["statement"]),
            scope=str(payload["scope"]),
            status=_enum(ClaimStatus, payload.get("status", ClaimStatus.OPEN.value)),
            dependencies=_tuple_of_str(payload.get("dependencies")),
            evidence_ids=_tuple_of_str(payload.get("evidence_ids")),
            route_ids=_tuple_of_str(payload.get("route_ids")),
            weight=float(payload.get("weight", 1.0)),
            critical=bool(payload.get("critical", False)),
            boundary=str(payload.get("boundary", "")),
            owner=str(payload.get("owner", "")),
            revision=int(payload.get("revision", 0)),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
        )


@dataclass(slots=True)
class ResearchRoute:
    route_id: str
    name: str
    hypothesis: str
    mechanism_signature: tuple[str, ...]
    kill_test: str
    status: RouteStatus = RouteStatus.PROPOSED
    claim_ids: tuple[str, ...] = ()
    parent_route_id: str | None = None
    rationale: str = ""
    expected_discriminator: str = ""
    created_by: str = ""
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    derived_from_failure: str | None = None
    transformation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "mechanism_signature": list(self.mechanism_signature),
            "kill_test": self.kill_test,
            "status": self.status.value,
            "claim_ids": list(self.claim_ids),
            "parent_route_id": self.parent_route_id,
            "rationale": self.rationale,
            "expected_discriminator": self.expected_discriminator,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "derived_from_failure": self.derived_from_failure,
            "transformation_id": self.transformation_id,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResearchRoute":
        if "derived_from_failure_id" in payload:
            if "derived_from_failure" in payload:
                raise ValueError(
                    "route cannot provide both derived_from_failure and "
                    "derived_from_failure_id"
                )
            payload = dict(payload)
            payload["derived_from_failure"] = payload.pop("derived_from_failure_id")
        _strict_payload(cls, payload)
        return cls(
            route_id=str(payload["route_id"]),
            name=str(payload["name"]),
            hypothesis=str(payload["hypothesis"]),
            mechanism_signature=_tuple_of_str(payload["mechanism_signature"]),
            kill_test=str(payload["kill_test"]),
            status=_enum(RouteStatus, payload.get("status", RouteStatus.PROPOSED.value)),
            claim_ids=_tuple_of_str(payload.get("claim_ids")),
            parent_route_id=(
                str(payload["parent_route_id"])
                if payload.get("parent_route_id") is not None
                else None
            ),
            rationale=str(payload.get("rationale", "")),
            expected_discriminator=str(payload.get("expected_discriminator", "")),
            created_by=str(payload.get("created_by", "")),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
            derived_from_failure=(
                str(payload["derived_from_failure"])
                if payload.get("derived_from_failure") is not None
                else None
            ),
            transformation_id=(
                str(payload["transformation_id"])
                if payload.get("transformation_id") is not None
                else None
            ),
        )


@dataclass(slots=True)
class EvidenceRecord:
    evidence_id: str
    claim_ids: tuple[str, ...]
    kind: EvidenceKind
    status: EvidenceStatus
    summary: str
    artifact_uri: str
    digest_sha256: str
    producer: str
    verifier: str
    independence_group: str
    replay_command: str = ""
    statement_correspondence: str = ""
    assumptions_checked: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)

    @property
    def replayable(self) -> bool:
        if self.kind in {
            EvidenceKind.EXACT_CERTIFICATE,
            EvidenceKind.EXACT_COMPUTATION,
            EvidenceKind.FORMAL_PROOF,
        }:
            return bool(self.replay_command and self.digest_sha256)
        return bool(self.digest_sha256 and self.statement_correspondence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim_ids": list(self.claim_ids),
            "kind": self.kind.value,
            "status": self.status.value,
            "summary": self.summary,
            "artifact_uri": self.artifact_uri,
            "digest_sha256": self.digest_sha256,
            "producer": self.producer,
            "verifier": self.verifier,
            "independence_group": self.independence_group,
            "replay_command": self.replay_command,
            "statement_correspondence": self.statement_correspondence,
            "assumptions_checked": list(self.assumptions_checked),
            "limitations": list(self.limitations),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EvidenceRecord":
        _strict_payload(cls, payload)
        return cls(
            evidence_id=str(payload["evidence_id"]),
            claim_ids=_tuple_of_str(payload["claim_ids"]),
            kind=_enum(EvidenceKind, payload["kind"]),
            status=_enum(EvidenceStatus, payload["status"]),
            summary=str(payload["summary"]),
            artifact_uri=str(payload["artifact_uri"]),
            digest_sha256=str(payload["digest_sha256"]),
            producer=str(payload["producer"]),
            verifier=str(payload["verifier"]),
            independence_group=str(payload["independence_group"]),
            replay_command=str(payload.get("replay_command", "")),
            statement_correspondence=str(payload.get("statement_correspondence", "")),
            assumptions_checked=_tuple_of_str(payload.get("assumptions_checked")),
            limitations=_tuple_of_str(payload.get("limitations")),
            created_at=str(payload.get("created_at") or utc_now()),
        )


@dataclass(slots=True)
class ToolCallRecord:
    call_id: str
    tool: str
    purpose: str
    status: ToolStatus
    input_digest_sha256: str
    output_digest_sha256: str
    linked_claim_ids: tuple[str, ...]
    independence_group: str
    replay_command: str
    started_at: str
    ended_at: str
    exit_code: int | None = None
    stdout_artifact_uri: str = ""
    stderr_artifact_uri: str = ""
    environment_digest_sha256: str = ""
    expected_discriminator: str = ""

    @property
    def replayable(self) -> bool:
        return bool(
            self.replay_command
            and self.input_digest_sha256
            and self.output_digest_sha256
            and self.environment_digest_sha256
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "tool": self.tool,
            "purpose": self.purpose,
            "status": self.status.value,
            "input_digest_sha256": self.input_digest_sha256,
            "output_digest_sha256": self.output_digest_sha256,
            "linked_claim_ids": list(self.linked_claim_ids),
            "independence_group": self.independence_group,
            "replay_command": self.replay_command,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "exit_code": self.exit_code,
            "stdout_artifact_uri": self.stdout_artifact_uri,
            "stderr_artifact_uri": self.stderr_artifact_uri,
            "environment_digest_sha256": self.environment_digest_sha256,
            "expected_discriminator": self.expected_discriminator,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ToolCallRecord":
        _strict_payload(cls, payload)
        return cls(
            call_id=str(payload["call_id"]),
            tool=str(payload["tool"]),
            purpose=str(payload["purpose"]),
            status=_enum(ToolStatus, payload["status"]),
            input_digest_sha256=str(payload["input_digest_sha256"]),
            output_digest_sha256=str(payload["output_digest_sha256"]),
            linked_claim_ids=_tuple_of_str(payload["linked_claim_ids"]),
            independence_group=str(payload["independence_group"]),
            replay_command=str(payload["replay_command"]),
            started_at=str(payload["started_at"]),
            ended_at=str(payload["ended_at"]),
            exit_code=(int(payload["exit_code"]) if payload.get("exit_code") is not None else None),
            stdout_artifact_uri=str(payload.get("stdout_artifact_uri", "")),
            stderr_artifact_uri=str(payload.get("stderr_artifact_uri", "")),
            environment_digest_sha256=str(payload.get("environment_digest_sha256", "")),
            expected_discriminator=str(payload.get("expected_discriminator", "")),
        )


@dataclass(frozen=True, slots=True)
class SpawnRequest:
    """A worker's declarative request for one governed child descriptor."""

    request_id: str
    brief: str
    role: str
    budget: float
    depth: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("spawn request_id must be non-empty")
        if not isinstance(self.brief, str) or not self.brief.strip():
            raise ValueError("spawn brief must be non-empty")
        if not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("spawn role must be non-empty")
        if isinstance(self.budget, bool) or not isinstance(self.budget, (int, float)):
            raise ValueError("spawn budget must be a finite positive number")
        budget = float(self.budget)
        if not math.isfinite(budget) or budget <= 0.0:
            raise ValueError("spawn budget must be a finite positive number")
        if isinstance(self.depth, bool) or not isinstance(self.depth, int):
            raise ValueError("spawn depth must be an integer")
        if self.depth < 0:
            raise ValueError("spawn depth cannot be negative")
        object.__setattr__(self, "request_id", self.request_id.strip())
        object.__setattr__(self, "brief", self.brief.strip())
        object.__setattr__(self, "role", self.role.strip())
        object.__setattr__(self, "budget", budget)

    @property
    def requested_budget(self) -> float:
        return self.budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "brief": self.brief,
            "role": self.role,
            "budget": self.budget,
            "depth": self.depth,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SpawnRequest":
        if not isinstance(payload, Mapping):
            raise ValueError("spawn request must be an object")
        normalized = dict(payload)
        if "spawn_id" in normalized:
            if "request_id" in normalized:
                raise ValueError("spawn request cannot provide both request_id and spawn_id")
            normalized["request_id"] = normalized.pop("spawn_id")
        if "requested_budget" in normalized:
            if "budget" in normalized:
                raise ValueError(
                    "spawn request cannot provide both budget and requested_budget"
                )
            normalized["budget"] = normalized.pop("requested_budget")
        _strict_payload(cls, normalized)
        return cls(
            request_id=normalized["request_id"],
            brief=normalized["brief"],
            role=normalized["role"],
            budget=normalized["budget"],
            depth=normalized.get("depth", 1),
        )


@dataclass(frozen=True, slots=True)
class SpawnDescriptor:
    """The only artifact produced by an approved spawn request."""

    request_id: str
    brief: str
    role: str
    budget: float
    depth: int
    round_id: str
    step_id: str

    @property
    def requested_budget(self) -> float:
        return self.budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "brief": self.brief,
            "role": self.role,
            "budget": self.budget,
            "depth": self.depth,
            "round_id": self.round_id,
            "step_id": self.step_id,
        }


@dataclass(frozen=True, slots=True)
class SpawnDecisionRecord:
    """Append-only, immutable audit record for one spawn request."""

    request_id: str
    status: SpawnDecisionStatus
    brief: str
    role: str
    requested_budget: float
    depth: int
    reason: str
    round_id: str
    step_id: str
    descriptor: SpawnDescriptor | None = None
    created_at: str = field(default_factory=utc_now)

    @property
    def approved(self) -> bool:
        return self.status is SpawnDecisionStatus.APPROVED

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "decision": self.status.value,
            "brief": self.brief,
            "role": self.role,
            "requested_budget": self.requested_budget,
            "depth": self.depth,
            "reason": self.reason,
            "round_id": self.round_id,
            "step_id": self.step_id,
            "descriptor": self.descriptor.to_dict() if self.descriptor else None,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class PublicReasoningStep:
    step_id: str
    role: str
    objective: str
    premises: tuple[str, ...]
    proposed_move: str
    observation: str
    falsification_test: str
    decision: str
    linked_claim_ids: tuple[str, ...] = ()
    linked_route_ids: tuple[str, ...] = ()
    linked_tool_call_ids: tuple[str, ...] = ()
    confidence: float | None = None
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "role": self.role,
            "objective": self.objective,
            "premises": list(self.premises),
            "proposed_move": self.proposed_move,
            "observation": self.observation,
            "falsification_test": self.falsification_test,
            "decision": self.decision,
            "linked_claim_ids": list(self.linked_claim_ids),
            "linked_route_ids": list(self.linked_route_ids),
            "linked_tool_call_ids": list(self.linked_tool_call_ids),
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PublicReasoningStep":
        _strict_payload(cls, payload)
        confidence = payload.get("confidence")
        if confidence is not None:
            confidence = float(confidence)
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("confidence must be in [0, 1]")
        return cls(
            step_id=str(payload["step_id"]),
            role=str(payload["role"]),
            objective=str(payload["objective"]),
            premises=_tuple_of_str(payload["premises"]),
            proposed_move=str(payload["proposed_move"]),
            observation=str(payload["observation"]),
            falsification_test=str(payload["falsification_test"]),
            decision=str(payload["decision"]),
            linked_claim_ids=_tuple_of_str(payload.get("linked_claim_ids")),
            linked_route_ids=_tuple_of_str(payload.get("linked_route_ids")),
            linked_tool_call_ids=_tuple_of_str(payload.get("linked_tool_call_ids")),
            confidence=confidence,
            timestamp=str(payload.get("timestamp") or utc_now()),
        )


@dataclass(slots=True)
class FailureRecord:
    failure_id: str
    claim_id: str
    route_id: str
    failure_class: FailureClass
    trigger: str
    diagnosis: str
    minimal_witness: str
    repair: str
    reusable_lesson: str
    evidence_ids: tuple[str, ...] = ()
    invalidated_claim_ids: tuple[str, ...] = ()
    exact: bool = False
    reused_count: int = 0
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "claim_id": self.claim_id,
            "route_id": self.route_id,
            "failure_class": self.failure_class.value,
            "trigger": self.trigger,
            "diagnosis": self.diagnosis,
            "minimal_witness": self.minimal_witness,
            "repair": self.repair,
            "reusable_lesson": self.reusable_lesson,
            "evidence_ids": list(self.evidence_ids),
            "invalidated_claim_ids": list(self.invalidated_claim_ids),
            "exact": self.exact,
            "reused_count": self.reused_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FailureRecord":
        _strict_payload(cls, payload)
        return cls(
            failure_id=str(payload["failure_id"]),
            claim_id=str(payload["claim_id"]),
            route_id=str(payload["route_id"]),
            failure_class=_enum(FailureClass, payload["failure_class"]),
            trigger=str(payload["trigger"]),
            diagnosis=str(payload["diagnosis"]),
            minimal_witness=str(payload["minimal_witness"]),
            repair=str(payload["repair"]),
            reusable_lesson=str(payload["reusable_lesson"]),
            evidence_ids=_tuple_of_str(payload.get("evidence_ids")),
            invalidated_claim_ids=_tuple_of_str(payload.get("invalidated_claim_ids")),
            exact=bool(payload.get("exact", False)),
            reused_count=int(payload.get("reused_count", 0)),
            created_at=str(payload.get("created_at") or utc_now()),
        )
