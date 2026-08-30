from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, IntEnum
from typing import Any, cast


class ScopeLevel(IntEnum):
    INSTANCE = 0
    FINITE_RANGE = 1
    PARAMETRIC_FAMILY = 2
    GLOBAL = 3


class TrustLevel(IntEnum):
    UNSUPPORTED = 0
    HEURISTIC = 1
    TESTED = 2
    EXACT = 3
    KERNEL_CHECKED = 4
    INDEPENDENT_REPLAY = 5


class ClaimStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    TESTED = "TESTED"
    BLOCKED = "BLOCKED"
    REFUTED = "REFUTED"
    INVALIDATED = "INVALIDATED"
    VERIFIED = "VERIFIED"


class EvidenceKind(str, Enum):
    NARRATIVE = "NARRATIVE"
    COMPUTATION = "COMPUTATION"
    EXACT_CERTIFICATE = "EXACT_CERTIFICATE"
    FORMAL_KERNEL = "FORMAL_KERNEL"
    INDEPENDENT_RECONSTRUCTION = "INDEPENDENT_RECONSTRUCTION"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    LITERATURE = "LITERATURE"


class ToolStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    UNKNOWN = "UNKNOWN"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


@dataclass
class VerifierPolicy:
    minimum_root_trust: TrustLevel = TrustLevel.EXACT
    require_independent_root_evidence: bool = True
    require_replay_command: bool = True
    require_all_critical_claims: bool = True


@dataclass
class TheoremContract:
    theorem_id: str
    title: str
    statement: str
    scope_level: ScopeLevel
    quantifiers: list[str]
    assumptions: list[str]
    root_claim_id: str
    status_date: str
    verifier_policy: VerifierPolicy = field(default_factory=VerifierPolicy)


@dataclass
class RouteRecord:
    route_id: str
    name: str
    mechanism: str
    basin: str
    status: str = "ACTIVE"
    rounds_without_gain: int = 0
    verified_gain: int = 0
    cost_units: float = 0.0


@dataclass
class ClaimNode:
    claim_id: str
    statement: str
    scope_level: ScopeLevel
    mechanism: str
    route_id: str
    dependencies: list[str] = field(default_factory=list)
    status: ClaimStatus = ClaimStatus.PROPOSED
    required_trust: TrustLevel = TrustLevel.EXACT
    evidence_ids: list[str] = field(default_factory=list)
    critical: bool = True
    notes: list[str] = field(default_factory=list)
    invalidated_by: str | None = None


@dataclass
class EvidenceArtifact:
    evidence_id: str
    kind: EvidenceKind
    trust_level: TrustLevel
    scope_level: ScopeLevel
    producer: str
    payload: dict[str, Any]
    sha256: str
    replay_command: str | None = None
    output_digest: str | None = None
    independent_of: list[str] = field(default_factory=list)
    accepted: bool = True


@dataclass
class ToolCallRecord:
    call_id: str
    tool_name: str
    input_digest: str
    status: ToolStatus
    summary: str
    output_digest: str
    duration_ms: int
    replay_command: str | None = None
    claim_ids: list[str] = field(default_factory=list)


@dataclass
class ReasoningCard:
    card_id: str
    sequence: int
    objective: str
    hypothesis: str
    action: str
    observation: str
    falsification: str
    decision: str
    public_summary: str
    claim_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    tool_call_ids: list[str] = field(default_factory=list)


@dataclass
class FailureEvent:
    failure_id: str
    claim_id: str
    classification: str
    root_cause: str
    minimal_reproduction: dict[str, Any]
    invalidated_claim_ids: list[str]
    regression_fixture: str


@dataclass
class GuardEvent:
    guard_id: str
    rule: str
    claim_id: str
    message: str
    blocked: bool = True


@dataclass
class ResearchRun:
    run_id: str
    contract: TheoremContract
    created_at: str
    updated_at: str
    claims: dict[str, ClaimNode] = field(default_factory=dict)
    routes: dict[str, RouteRecord] = field(default_factory=dict)
    evidence: dict[str, EvidenceArtifact] = field(default_factory=dict)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    reasoning_cards: list[ReasoningCard] = field(default_factory=list)
    failures: list[FailureEvent] = field(default_factory=list)
    guard_events: list[GuardEvent] = field(default_factory=list)
    release_state: str = "DRAFT"

    def to_dict(self) -> dict[str, Any]:
        return cast("dict[str, Any]", _encode(asdict(self)))

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ResearchRun":
        contract_raw = dict(raw["contract"])
        policy_raw = dict(contract_raw.pop("verifier_policy", {}))
        contract_scope = ScopeLevel(contract_raw.pop("scope_level"))
        policy = VerifierPolicy(
            minimum_root_trust=TrustLevel(policy_raw.get("minimum_root_trust", 3)),
            require_independent_root_evidence=policy_raw.get(
                "require_independent_root_evidence", True
            ),
            require_replay_command=policy_raw.get("require_replay_command", True),
            require_all_critical_claims=policy_raw.get("require_all_critical_claims", True),
        )
        contract = TheoremContract(
            **contract_raw,
            scope_level=contract_scope,
            verifier_policy=policy,
        )
        claims: dict[str, ClaimNode] = {}
        for key, value in raw.get("claims", {}).items():
            claim_raw = dict(value)
            claim_scope = ScopeLevel(claim_raw.pop("scope_level"))
            claim_status = ClaimStatus(claim_raw.pop("status"))
            required_trust = TrustLevel(claim_raw.pop("required_trust"))
            claims[key] = ClaimNode(
                **claim_raw,
                scope_level=claim_scope,
                status=claim_status,
                required_trust=required_trust,
            )
        routes = {key: RouteRecord(**value) for key, value in raw.get("routes", {}).items()}
        evidence: dict[str, EvidenceArtifact] = {}
        for key, value in raw.get("evidence", {}).items():
            evidence_raw = dict(value)
            kind = EvidenceKind(evidence_raw.pop("kind"))
            trust = TrustLevel(evidence_raw.pop("trust_level"))
            scope = ScopeLevel(evidence_raw.pop("scope_level"))
            evidence[key] = EvidenceArtifact(
                **evidence_raw,
                kind=kind,
                trust_level=trust,
                scope_level=scope,
            )
        tool_calls: list[ToolCallRecord] = []
        for item in raw.get("tool_calls", []):
            call_raw = dict(item)
            status = ToolStatus(call_raw.pop("status"))
            tool_calls.append(ToolCallRecord(**call_raw, status=status))
        cards = [ReasoningCard(**item) for item in raw.get("reasoning_cards", [])]
        failures = [FailureEvent(**item) for item in raw.get("failures", [])]
        guards = [GuardEvent(**item) for item in raw.get("guard_events", [])]
        return cls(
            run_id=raw["run_id"],
            contract=contract,
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
            claims=claims,
            routes=routes,
            evidence=evidence,
            tool_calls=tool_calls,
            reasoning_cards=cards,
            failures=failures,
            guard_events=guards,
            release_state=raw.get("release_state", "DRAFT"),
        )


def _encode(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    return value
