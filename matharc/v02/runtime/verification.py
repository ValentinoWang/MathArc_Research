"""Independent replay, verifier receipts, evidence conversion and invalidation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping

from ..schema import EvidenceKind, EvidenceRecord, EvidenceStatus, digest_json, utc_now
from .synthesis import ExplorationCandidate


class VerificationError(ValueError):
    pass


ScopeBindingError = VerificationError


class VerificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"


@dataclass(frozen=True, slots=True)
class ReplayPlan:
    candidate_id: str
    replay_digest: str
    environment: Mapping[str, Any]
    verifier_id: str
    implementation_id: str
    clean_environment: bool = True
    max_retries: int = 0

    @classmethod
    def for_candidate(cls, candidate: ExplorationCandidate, *, verifier_id: str,
                      implementation_id: str, environment: Mapping[str, Any] | None = None,
                      max_retries: int = 0) -> "ReplayPlan":
        if verifier_id.strip() == implementation_id.strip():
            raise VerificationError("same implementation cannot count as independent verification")
        if max_retries < 0:
            raise VerificationError("max_retries must be non-negative")
        env = dict(environment or {"mode": "clean", "network": False, "candidate_id": candidate.candidate_id})
        if env.get("clean_environment") is False or env.get("mode") not in (None, "clean"):
            raise VerificationError("independent replay requires a clean environment")
        if env.get("candidate_id", candidate.candidate_id) != candidate.candidate_id:
            raise VerificationError("replay environment candidate mismatch")
        digest = digest_json({"candidate": candidate.envelope.to_dict(), "environment": env,
                              "verifier_id": verifier_id, "implementation_id": implementation_id})
        return cls(candidate.candidate_id, digest, env, verifier_id, implementation_id, True, max_retries)

    @property
    def idempotency_key(self) -> str:
        return f"{self.candidate_id}+{self.replay_digest}"

    def to_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "replay_digest": self.replay_digest,
                "environment": dict(self.environment), "verifier_id": self.verifier_id,
                "implementation_id": self.implementation_id, "clean_environment": self.clean_environment,
                "max_retries": self.max_retries}


@dataclass(frozen=True, slots=True)
class VerifierReceipt:
    candidate_id: str
    replay_digest: str
    status: VerificationStatus
    verifier_id: str
    independent: bool
    result_digest: str = ""
    failure_class: str | None = None
    message: str = ""
    attempts: int = 1
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.status, VerificationStatus):
            try:
                object.__setattr__(self, "status", VerificationStatus(str(self.status)))
            except ValueError as exc:
                raise VerificationError(f"unknown verification status: {self.status}") from exc
        if self.attempts < 1:
            raise VerificationError("attempts must be positive")

    @property
    def receipt_digest(self) -> str:
        return digest_json(self.to_dict(include_digest=False))

    @property
    def idempotency_key(self) -> str:
        return f"{self.candidate_id}+{self.receipt_digest}"

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {"candidate_id": self.candidate_id, "replay_digest": self.replay_digest,
                 "status": self.status.value, "verifier_id": self.verifier_id,
                 "independent": self.independent, "result_digest": self.result_digest,
                 "failure_class": self.failure_class, "message": self.message,
                 "attempts": self.attempts, "created_at": self.created_at}
        if include_digest: value["receipt_digest"] = self.receipt_digest
        return value


@dataclass(frozen=True, slots=True)
class ClaimBinding:
    claim_id: str
    proposition: str
    quantifier: str
    objects: tuple[str, ...]
    scope: str

    def to_dict(self) -> dict[str, Any]:
        return {"claim_id": self.claim_id, "proposition": self.proposition,
                "quantifier": self.quantifier, "objects": list(self.objects), "scope": self.scope}


def bind_candidate_scope(candidate: ExplorationCandidate, *, claim_id: str,
                         proposition: str, quantifier: str, objects: tuple[str, ...] = (),
                         scope: str) -> ClaimBinding:
    """Bind a candidate to the exact proposition/quantifier/object/scope it claims."""
    payload = candidate.payload if isinstance(candidate.payload, Mapping) else {}
    for key, expected in (("proposition", proposition), ("quantifier", quantifier), ("scope", scope)):
        actual = payload.get(key)
        if actual is not None and str(actual) != str(expected):
            raise ScopeBindingError(f"candidate {key} does not match bound claim")
    actual_objects = tuple(str(item) for item in payload.get("objects", objects))
    if tuple(str(item) for item in objects) != actual_objects:
        raise ScopeBindingError("candidate objects do not match bound claim")
    if candidate.claim_ids and claim_id not in candidate.claim_ids:
        raise ScopeBindingError("candidate is not associated with claim")
    return ClaimBinding(str(claim_id), str(proposition), str(quantifier), actual_objects, str(scope))


def independent_replay(candidate: ExplorationCandidate, *, verifier_id: str,
                       implementation_id: str, replay: Callable[[Any], Any],
                       environment: Mapping[str, Any] | None = None,
                       max_retries: int = 0) -> tuple[ReplayPlan, VerifierReceipt]:
    expected_payload_digest = candidate.envelope.payload_digest
    if expected_payload_digest and digest_json(candidate.payload) != expected_payload_digest:
        raise VerificationError("candidate payload digest does not match envelope")
    plan = ReplayPlan.for_candidate(candidate, verifier_id=verifier_id, implementation_id=implementation_id,
                                    environment=environment, max_retries=max_retries)
    attempts = 0
    error_message = ""
    while True:
        attempts += 1
        try:
            result = replay(candidate.payload)
            passed = bool(result) if isinstance(result, bool) else bool(result.get("passed", result.get("ok", False))) if isinstance(result, Mapping) else True
            status = VerificationStatus.PASS if passed else VerificationStatus.FAIL
            receipt = VerifierReceipt(candidate.candidate_id, plan.replay_digest, status, verifier_id, True,
                                      digest_json(result), None if passed else "VERIFICATION_FAILED", "", attempts)
            return plan, receipt
        except TimeoutError as exc:
            status, failure = VerificationStatus.TIMED_OUT, "TIMEOUT"
            error_message = str(exc)
        except (KeyboardInterrupt, InterruptedError) as exc:
            status, failure = VerificationStatus.CANCELLED, "CANCELLED"
            error_message = str(exc)
        except Exception as exc:  # verifier failure is recorded, not promoted
            status, failure = VerificationStatus.RETRYABLE_FAILURE, type(exc).__name__
            error_message = str(exc)
        if attempts > max_retries:
            return plan, VerifierReceipt(candidate.candidate_id, plan.replay_digest, status, verifier_id, True,
                                         "", failure, error_message, attempts)


def convert_receipt_to_evidence(candidate: ExplorationCandidate, receipt: VerifierReceipt,
                                *, artifact_uri: str = "runtime://candidate",
                                producer: str = "runtime-worker", independence_group: str | None = None) -> EvidenceRecord:
    if receipt.candidate_id != candidate.candidate_id:
        raise VerificationError("receipt candidate identity mismatch")
    if receipt.status is not VerificationStatus.PASS or not receipt.independent:
        raise VerificationError("only an independent PASS receipt can become evidence")
    return EvidenceRecord(
        evidence_id="ev-" + receipt.receipt_digest,
        claim_ids=tuple(candidate.claim_ids), kind=EvidenceKind.EXACT_COMPUTATION,
        status=EvidenceStatus.ACCEPTED, summary="Independently replayed runtime candidate",
        artifact_uri=artifact_uri, digest_sha256=receipt.result_digest or candidate.envelope.artifact_digest,
        producer=producer, verifier=receipt.verifier_id,
        independence_group=independence_group or receipt.verifier_id,
        replay_command=f"replay:{receipt.replay_digest}",
        statement_correspondence="Candidate payload corresponds to the bound claim scope.",
        limitations=(f"candidate_id={candidate.candidate_id}", f"receipt_digest={receipt.receipt_digest}"),
    )


verify_candidate = independent_replay
evidence_from_receipt = convert_receipt_to_evidence


def invalidate_evidence(evidence: EvidenceRecord, *, reason: str,
                        changed_fields: Mapping[str, Any] | None = None) -> EvidenceRecord:
    if not str(reason).strip():
        raise VerificationError("invalidation reason is required")
    evidence.status = EvidenceStatus.STALE
    details = reason if not changed_fields else f"{reason}; changed={','.join(sorted(changed_fields))}"
    evidence.limitations = tuple(dict.fromkeys((*evidence.limitations, details)))
    return evidence


invalidate_evidence_for_change = invalidate_evidence


class EvidenceInvalidator:
    """Tracks the candidate identity consumed by evidence and invalidates drift."""
    def __init__(self) -> None:
        self._identity: dict[str, str] = {}

    def register(self, evidence: EvidenceRecord, candidate: ExplorationCandidate) -> None:
        self._identity[evidence.evidence_id] = candidate.envelope.identity_digest

    def check(self, evidence: EvidenceRecord, candidate: ExplorationCandidate) -> bool:
        expected = self._identity.get(evidence.evidence_id)
        if expected is None:
            raise VerificationError("evidence has no registered candidate identity")
        if expected != candidate.envelope.identity_digest:
            invalidate_evidence(evidence, reason="candidate identity changed", changed_fields=candidate.envelope.to_dict())
            return False
        return True


__all__ = ["VerificationError", "VerificationStatus", "ReplayPlan", "VerifierReceipt",
           "ScopeBindingError", "ClaimBinding", "bind_candidate_scope", "independent_replay", "verify_candidate",
           "convert_receipt_to_evidence", "evidence_from_receipt", "invalidate_evidence", "invalidate_evidence_for_change", "EvidenceInvalidator"]
