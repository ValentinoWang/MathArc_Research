"""Independent replay, verifier receipts, evidence conversion and invalidation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping

from ..schema import EvidenceKind, EvidenceRecord, EvidenceStatus, digest_json, utc_now
from .synthesis import ExplorationCandidate


class VerificationError(ValueError):
    pass


class ReplayProtocolError(VerificationError):
    """The verifier returned a value outside the replay protocol."""


ScopeBindingError = VerificationError


class VerificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"


def _is_sha256(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _receipt_binding_digest(*, candidate_identity_digest: str, replay_digest: str,
                            result_digest: str, verifier_id: str,
                            status: VerificationStatus, independent: bool) -> str:
    return digest_json({
        "candidate_identity_digest": candidate_identity_digest,
        "replay_digest": replay_digest,
        "result_digest": result_digest,
        "verifier_id": verifier_id,
        "status": status.value,
        "independent": independent,
    })


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
        if not str(verifier_id).strip() or not str(implementation_id).strip():
            raise VerificationError("verifier_id and implementation_id are required")
        if verifier_id.strip() == implementation_id.strip():
            raise VerificationError("same implementation cannot count as independent verification")
        if max_retries < 0:
            raise VerificationError("max_retries must be non-negative")
        env = dict(environment or {"mode": "clean", "network": False, "candidate_id": candidate.candidate_id})
        if env.get("clean_environment") is False or env.get("mode") not in (None, "clean"):
            raise VerificationError("independent replay requires a clean environment")
        if env.get("network", False) is not False:
            raise VerificationError("independent replay must not use a networked environment")
        if env.get("candidate_id", candidate.candidate_id) != candidate.candidate_id:
            raise VerificationError("replay environment candidate mismatch")
        digest = digest_json({"candidate": candidate.envelope.to_dict(),
                              "candidate_provenance_digest": candidate.provenance_digest,
                              "environment": env,
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
    candidate_identity_digest: str = ""
    receipt_binding_digest: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.status, VerificationStatus):
            try:
                aliases = {"TIMEOUT": VerificationStatus.TIMED_OUT.value,
                           "CANCELED": VerificationStatus.CANCELLED.value}
                object.__setattr__(self, "status", VerificationStatus(aliases.get(str(self.status), str(self.status))))
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

    @property
    def retryable(self) -> bool:
        """Whether another replay attempt is semantically permitted."""
        return self.failure_class in {"TIMEOUT", "REPLAY_EXECUTION_ERROR"}

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {"candidate_id": self.candidate_id, "replay_digest": self.replay_digest,
                 "status": self.status.value, "verifier_id": self.verifier_id,
                 "independent": self.independent, "result_digest": self.result_digest,
                 "failure_class": self.failure_class, "message": self.message,
                 "attempts": self.attempts, "created_at": self.created_at,
                 "candidate_identity_digest": self.candidate_identity_digest,
                 "receipt_binding_digest": self.receipt_binding_digest}
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
    if not str(claim_id).strip() or not candidate.claim_ids or claim_id not in candidate.claim_ids:
        raise ScopeBindingError("candidate is not associated with claim")
    if not isinstance(candidate.payload, Mapping):
        raise ScopeBindingError("candidate payload must declare claim scope")
    payload = candidate.payload
    for key, expected in (("proposition", proposition), ("quantifier", quantifier), ("scope", scope)):
        actual = payload.get(key)
        if actual is None or str(actual) != str(expected):
            raise ScopeBindingError(f"candidate {key} does not match bound claim")
    actual_objects = tuple(str(item) for item in payload.get("objects", objects))
    if tuple(str(item) for item in objects) != actual_objects:
        raise ScopeBindingError("candidate objects do not match bound claim")
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
    def normalize_result(result: Any) -> tuple[bool, str]:
        if isinstance(result, bool):
            return result, digest_json(result)
        if not isinstance(result, Mapping):
            raise ReplayProtocolError("replay returned an unsupported result type")
        present = [key for key in ("passed", "ok") if key in result]
        if not present or any(not isinstance(result[key], bool) for key in present):
            raise ReplayProtocolError("replay must return a boolean or a mapping with boolean passed/ok")
        if len(present) == 2 and result["passed"] != result["ok"]:
            raise ReplayProtocolError("replay passed and ok fields disagree")
        return bool(result[present[0]]), digest_json(result)

    while True:
        attempts += 1
        try:
            result = replay(candidate.payload)
            passed, result_digest = normalize_result(result)
            status = VerificationStatus.PASS if passed else VerificationStatus.FAIL
            receipt = VerifierReceipt(candidate.candidate_id, plan.replay_digest, status, verifier_id, True,
                                      result_digest, None if passed else "VERIFICATION_FAILED", "", attempts,
                                      candidate_identity_digest=candidate.envelope.identity_digest,
                                      receipt_binding_digest=_receipt_binding_digest(
                                          candidate_identity_digest=candidate.envelope.identity_digest,
                                          replay_digest=plan.replay_digest,
                                          result_digest=result_digest, verifier_id=verifier_id,
                                          status=status, independent=True))
            return plan, receipt
        except TimeoutError as exc:
            status, failure = VerificationStatus.TIMED_OUT, "TIMEOUT"
            error_message = str(exc)
        except (KeyboardInterrupt, InterruptedError) as exc:
            status, failure = VerificationStatus.CANCELLED, "CANCELLED"
            error_message = str(exc)
        except ReplayProtocolError as exc:
            status, failure = VerificationStatus.RETRYABLE_FAILURE, "REPLAY_PROTOCOL_ERROR"
            error_message = str(exc)
        except VerificationError as exc:
            status, failure = VerificationStatus.RETRYABLE_FAILURE, "REPLAY_PROTOCOL_ERROR"
            error_message = str(exc)
        except Exception as exc:  # verifier failure is recorded, not promoted
            status, failure = VerificationStatus.RETRYABLE_FAILURE, "REPLAY_EXECUTION_ERROR"
            error_message = str(exc)
        retryable = failure in {"TIMEOUT", "REPLAY_EXECUTION_ERROR"}
        if not retryable or attempts > max_retries:
            return plan, VerifierReceipt(candidate.candidate_id, plan.replay_digest, status, verifier_id, True,
                                         "", failure, error_message, attempts,
                                         candidate_identity_digest=candidate.envelope.identity_digest,
                                         receipt_binding_digest=_receipt_binding_digest(
                                             candidate_identity_digest=candidate.envelope.identity_digest,
                                             replay_digest=plan.replay_digest, result_digest="",
                                             verifier_id=verifier_id, status=status, independent=True))


def convert_receipt_to_evidence(candidate: ExplorationCandidate, receipt: VerifierReceipt,
                                *, artifact_uri: str = "runtime://candidate",
                                producer: str = "runtime-worker", independence_group: str | None = None) -> EvidenceRecord:
    if receipt.candidate_id != candidate.candidate_id:
        raise VerificationError("receipt candidate identity mismatch")
    if receipt.status is not VerificationStatus.PASS or not receipt.independent:
        raise VerificationError("only an independent PASS receipt can become evidence")
    if receipt.candidate_identity_digest != candidate.envelope.identity_digest:
        raise VerificationError("receipt candidate digest does not match candidate envelope")
    if not _is_sha256(candidate.envelope.payload_digest) or digest_json(candidate.payload) != candidate.envelope.payload_digest:
        raise VerificationError("candidate payload digest does not match candidate envelope")
    if not _is_sha256(receipt.replay_digest) or not _is_sha256(receipt.result_digest):
        raise VerificationError("receipt replay and result digests must be SHA-256 values")
    expected_binding = _receipt_binding_digest(
        candidate_identity_digest=receipt.candidate_identity_digest,
        replay_digest=receipt.replay_digest,
        result_digest=receipt.result_digest,
        verifier_id=receipt.verifier_id,
        status=receipt.status,
        independent=receipt.independent,
    )
    if receipt.receipt_binding_digest != expected_binding:
        raise VerificationError("receipt replay/candidate binding digest mismatch")
    return EvidenceRecord(
        evidence_id="ev-" + receipt.receipt_digest,
        claim_ids=tuple(candidate.claim_ids), kind=EvidenceKind.EXACT_COMPUTATION,
        status=EvidenceStatus.ACCEPTED, summary="Independently replayed runtime candidate",
        artifact_uri=artifact_uri, digest_sha256=receipt.result_digest or candidate.envelope.artifact_digest,
        producer=producer, verifier=receipt.verifier_id,
        independence_group=independence_group or receipt.verifier_id,
        replay_command=f"replay:{receipt.replay_digest}",
        statement_correspondence="Candidate payload corresponds to the bound claim scope.",
        limitations=(f"candidate_id={candidate.candidate_id}",
                     f"candidate_payload_digest={candidate.envelope.payload_digest}",
                     f"candidate_provenance_digest={candidate.provenance_digest}",
                     f"receipt_digest={receipt.receipt_digest}"),
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
        self._payload_digest: dict[str, str] = {}
        self._consumed_content: dict[str, str] = {}
        self._provenance: dict[str, str] = {}
        self._evidence_digest: dict[str, str] = {}

    def register(self, evidence: EvidenceRecord, candidate: ExplorationCandidate) -> None:
        if not _is_sha256(candidate.envelope.payload_digest):
            raise VerificationError("candidate envelope has no valid payload digest")
        if digest_json(candidate.payload) != candidate.envelope.payload_digest:
            raise VerificationError("candidate consumed content does not match payload digest")
        self._identity[evidence.evidence_id] = candidate.envelope.identity_digest
        self._payload_digest[evidence.evidence_id] = candidate.envelope.payload_digest
        self._consumed_content[evidence.evidence_id] = digest_json(candidate.payload)
        self._provenance[evidence.evidence_id] = candidate.provenance_digest
        self._evidence_digest[evidence.evidence_id] = digest_json(evidence.to_dict())

    def check(self, evidence: EvidenceRecord, candidate: ExplorationCandidate) -> bool:
        expected = self._identity.get(evidence.evidence_id)
        if expected is None:
            raise VerificationError("evidence has no registered candidate identity")
        expected_payload = self._payload_digest.get(evidence.evidence_id)
        expected_content = self._consumed_content.get(evidence.evidence_id)
        expected_provenance = self._provenance.get(evidence.evidence_id)
        evidence_changed = self._evidence_digest.get(evidence.evidence_id) != digest_json(evidence.to_dict())
        payload_changed = expected_payload != candidate.envelope.payload_digest
        content_changed = expected_content != digest_json(candidate.payload)
        provenance_changed = expected_provenance != candidate.provenance_digest
        if evidence_changed:
            invalidate_evidence(evidence, reason="consumed evidence mutated")
            return False
        if expected != candidate.envelope.identity_digest or payload_changed or content_changed or provenance_changed:
            changed = {"candidate_identity_digest": candidate.envelope.identity_digest,
                       "candidate_payload_digest": candidate.envelope.payload_digest,
                       "candidate_provenance_digest": candidate.provenance_digest}
            invalidate_evidence(evidence, reason="candidate consumed content changed", changed_fields=changed)
            return False
        return True


__all__ = ["VerificationError", "ReplayProtocolError", "VerificationStatus", "ReplayPlan", "VerifierReceipt",
           "ScopeBindingError", "ClaimBinding", "bind_candidate_scope", "independent_replay", "verify_candidate",
           "convert_receipt_to_evidence", "evidence_from_receipt", "invalidate_evidence", "invalidate_evidence_for_change", "EvidenceInvalidator"]
