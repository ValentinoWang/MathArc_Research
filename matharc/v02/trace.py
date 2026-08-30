from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    FailureRecord,
    PublicReasoningStep,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolCallRecord,
    ToolStatus,
    canonical_json,
    digest_json,
    utc_now,
)


class TraceValidationError(ValueError):
    """Raised when a research trace is structurally or mathematically unsafe."""


class PromotionError(TraceValidationError):
    """Raised when a claim is promoted beyond its evidence boundary."""


@dataclass(slots=True)
class ResearchTrace:
    run_id: str
    contract: TheoremContract
    claims: dict[str, ClaimRecord] = field(default_factory=dict)
    routes: dict[str, ResearchRoute] = field(default_factory=dict)
    evidence: dict[str, EvidenceRecord] = field(default_factory=dict)
    tool_calls: dict[str, ToolCallRecord] = field(default_factory=dict)
    public_reasoning: list[PublicReasoningStep] = field(default_factory=list)
    failures: list[FailureRecord] = field(default_factory=list)
    boundary_violations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = "2.0"

    def _touch(self) -> None:
        self.updated_at = utc_now()

    def add_claim(self, claim: ClaimRecord) -> None:
        if claim.claim_id in self.claims:
            raise TraceValidationError(f"duplicate claim id: {claim.claim_id}")
        if claim.weight <= 0:
            raise TraceValidationError(f"claim weight must be positive: {claim.claim_id}")
        missing = [item for item in claim.dependencies if item not in self.claims]
        if missing:
            raise TraceValidationError(
                f"claim {claim.claim_id} has undeclared dependencies: {missing}"
            )
        self.claims[claim.claim_id] = claim
        cycle = self._find_cycle()
        if cycle:
            del self.claims[claim.claim_id]
            raise TraceValidationError(f"claim dependency cycle: {' -> '.join(cycle)}")
        self._touch()

    def revise_claim(
        self,
        claim_id: str,
        *,
        statement: str | None = None,
        scope: str | None = None,
        boundary: str | None = None,
    ) -> ClaimRecord:
        claim = self._claim(claim_id)
        if claim.status is ClaimStatus.PROVED:
            raise TraceValidationError(
                "proved claims are immutable; retract and create a new revision instead"
            )
        if statement is not None:
            claim.statement = statement
        if scope is not None:
            claim.scope = scope
        if boundary is not None:
            claim.boundary = boundary
        claim.revision += 1
        claim.updated_at = utc_now()
        self._touch()
        return claim

    def add_route(self, route: ResearchRoute) -> None:
        if route.route_id in self.routes:
            raise TraceValidationError(f"duplicate route id: {route.route_id}")
        if not route.mechanism_signature:
            raise TraceValidationError("a route requires a non-empty mechanism signature")
        if not route.kill_test.strip():
            raise TraceValidationError("a route requires a cheap falsification or kill test")
        missing_claims = [item for item in route.claim_ids if item not in self.claims]
        if missing_claims:
            raise TraceValidationError(
                f"route {route.route_id} references unknown claims: {missing_claims}"
            )
        if route.parent_route_id is not None and route.parent_route_id not in self.routes:
            raise TraceValidationError(
                f"route {route.route_id} has unknown parent {route.parent_route_id}"
            )
        normalized = self._mechanism_signature(route.mechanism_signature)
        for existing in self.routes.values():
            if existing.status is RouteStatus.ABANDONED:
                continue
            if normalized == self._mechanism_signature(existing.mechanism_signature):
                raise TraceValidationError(
                    f"route {route.route_id} duplicates mechanism of {existing.route_id}; "
                    "renaming a route is not route diversity"
                )
        self.routes[route.route_id] = route
        for claim_id in route.claim_ids:
            claim = self.claims[claim_id]
            claim.route_ids = tuple(dict.fromkeys((*claim.route_ids, route.route_id)))
            claim.updated_at = utc_now()
        self._touch()

    def activate_route(self, route_id: str) -> None:
        route = self._route(route_id)
        if route.status in {RouteStatus.FALSIFIED, RouteStatus.CLOSED, RouteStatus.ABANDONED}:
            raise TraceValidationError(f"terminal route cannot be activated: {route_id}")
        route.status = RouteStatus.ACTIVE
        route.updated_at = utc_now()
        self._touch()

    def add_evidence(self, record: EvidenceRecord) -> None:
        if record.evidence_id in self.evidence:
            raise TraceValidationError(f"duplicate evidence id: {record.evidence_id}")
        missing = [item for item in record.claim_ids if item not in self.claims]
        if missing:
            raise TraceValidationError(
                f"evidence {record.evidence_id} references unknown claims: {missing}"
            )
        if record.status is EvidenceStatus.ACCEPTED:
            if len(record.digest_sha256) != 64:
                raise TraceValidationError(
                    f"accepted evidence {record.evidence_id} needs a SHA-256 digest"
                )
            if not record.statement_correspondence.strip():
                raise TraceValidationError(
                    f"accepted evidence {record.evidence_id} needs statement correspondence"
                )
        self.evidence[record.evidence_id] = record
        for claim_id in record.claim_ids:
            claim = self.claims[claim_id]
            claim.evidence_ids = tuple(
                dict.fromkeys((*claim.evidence_ids, record.evidence_id))
            )
            claim.updated_at = utc_now()
        self._touch()

    def add_tool_call(self, record: ToolCallRecord) -> None:
        if record.call_id in self.tool_calls:
            raise TraceValidationError(f"duplicate tool call id: {record.call_id}")
        missing = [item for item in record.linked_claim_ids if item not in self.claims]
        if missing:
            raise TraceValidationError(
                f"tool call {record.call_id} references unknown claims: {missing}"
            )
        if record.status is ToolStatus.PASS and not record.output_digest_sha256:
            raise TraceValidationError(
                f"passing tool call {record.call_id} requires an output digest"
            )
        self.tool_calls[record.call_id] = record
        self._touch()

    def add_public_reasoning(self, step: PublicReasoningStep) -> None:
        if any(existing.step_id == step.step_id for existing in self.public_reasoning):
            raise TraceValidationError(f"duplicate public reasoning step: {step.step_id}")
        self._require_refs(step.linked_claim_ids, self.claims, "claim", step.step_id)
        self._require_refs(step.linked_route_ids, self.routes, "route", step.step_id)
        self._require_refs(
            step.linked_tool_call_ids, self.tool_calls, "tool call", step.step_id
        )
        self.public_reasoning.append(step)
        self._touch()

    def mark_candidate(self, claim_id: str) -> None:
        claim = self._claim(claim_id)
        if claim.status in {ClaimStatus.REFUTED, ClaimStatus.RETRACTED}:
            raise PromotionError(f"terminal claim cannot become a candidate: {claim_id}")
        claim.status = ClaimStatus.CANDIDATE
        claim.updated_at = utc_now()
        self._touch()

    def promote_claim(
        self,
        claim_id: str,
        *,
        minimum_independent_groups: int | None = None,
    ) -> None:
        claim = self._claim(claim_id)
        required = (
            minimum_independent_groups
            if minimum_independent_groups is not None
            else (2 if claim.critical else 1)
        )
        issues = self._promotion_issues(claim, required)
        if issues:
            violation = {
                "claim_id": claim_id,
                "attempted_status": ClaimStatus.PROVED.value,
                "issues": issues,
                "timestamp": utc_now(),
            }
            self.boundary_violations.append(violation)
            self._touch()
            raise PromotionError("; ".join(issues))
        claim.status = ClaimStatus.PROVED
        claim.updated_at = utc_now()
        self._touch()

    def retract_claim(self, claim_id: str, reason: str) -> tuple[str, ...]:
        claim = self._claim(claim_id)
        claim.status = ClaimStatus.RETRACTED
        claim.updated_at = utc_now()
        descendants = self.descendants(claim_id)
        invalidated: list[str] = []
        for descendant_id in descendants:
            descendant = self.claims[descendant_id]
            if descendant.status in {
                ClaimStatus.PROVED,
                ClaimStatus.CANDIDATE,
                ClaimStatus.OPEN,
            }:
                descendant.status = ClaimStatus.BLOCKED
                descendant.updated_at = utc_now()
                invalidated.append(descendant_id)
        self.boundary_violations.append(
            {
                "claim_id": claim_id,
                "attempted_status": "RETRACTION",
                "issues": [reason],
                "invalidated_claim_ids": invalidated,
                "timestamp": utc_now(),
            }
        )
        self._touch()
        return tuple(invalidated)

    def record_failure(self, record: FailureRecord) -> FailureRecord:
        if any(item.failure_id == record.failure_id for item in self.failures):
            raise TraceValidationError(f"duplicate failure id: {record.failure_id}")
        claim = self._claim(record.claim_id)
        route = self._route(record.route_id)
        self._require_refs(record.evidence_ids, self.evidence, "evidence", record.failure_id)

        claim.status = ClaimStatus.REFUTED if record.exact else ClaimStatus.BLOCKED
        claim.updated_at = utc_now()
        route.status = RouteStatus.FALSIFIED if record.exact else RouteStatus.BLOCKED
        route.updated_at = utc_now()

        invalidated: list[str] = []
        for descendant_id in self.descendants(record.claim_id):
            descendant = self.claims[descendant_id]
            if descendant.status not in {ClaimStatus.REFUTED, ClaimStatus.RETRACTED}:
                descendant.status = ClaimStatus.BLOCKED
                descendant.updated_at = utc_now()
                invalidated.append(descendant_id)
        record.invalidated_claim_ids = tuple(
            dict.fromkeys((*record.invalidated_claim_ids, *invalidated))
        )
        self.failures.append(record)
        self._touch()
        return record

    def descendants(self, claim_id: str) -> tuple[str, ...]:
        self._claim(claim_id)
        reverse: dict[str, list[str]] = {item: [] for item in self.claims}
        for candidate in self.claims.values():
            for dependency in candidate.dependencies:
                reverse[dependency].append(candidate.claim_id)
        seen: set[str] = set()
        stack = list(reverse[claim_id])
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(reverse[current])
        return tuple(sorted(seen))

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []

        if self.schema_version != "2.0":
            errors.append(f"unsupported schema version: {self.schema_version}")
        if not self.run_id.strip():
            errors.append("run_id is empty")
        for target in self.contract.target_claim_ids:
            if target not in self.claims:
                errors.append(f"contract target is missing: {target}")
        cycle = self._find_cycle()
        if cycle:
            errors.append(f"claim dependency cycle: {' -> '.join(cycle)}")

        for claim in self.claims.values():
            for dependency in claim.dependencies:
                if dependency not in self.claims:
                    errors.append(
                        f"claim {claim.claim_id} has missing dependency {dependency}"
                    )
            for evidence_id in claim.evidence_ids:
                if evidence_id not in self.evidence:
                    errors.append(
                        f"claim {claim.claim_id} has missing evidence {evidence_id}"
                    )
            for route_id in claim.route_ids:
                if route_id not in self.routes:
                    errors.append(f"claim {claim.claim_id} has missing route {route_id}")
            if claim.status is ClaimStatus.PROVED:
                required = 2 if claim.critical else 1
                errors.extend(self._promotion_issues(claim, required))

        for route in self.routes.values():
            if not route.kill_test.strip():
                errors.append(f"route {route.route_id} has no kill test")
            for claim_id in route.claim_ids:
                if claim_id not in self.claims:
                    errors.append(f"route {route.route_id} has missing claim {claim_id}")

        for evidence in self.evidence.values():
            if evidence.status is EvidenceStatus.ACCEPTED and not evidence.replayable:
                warnings.append(
                    f"accepted evidence {evidence.evidence_id} is not cold-replayable"
                )
            if evidence.producer == evidence.verifier:
                warnings.append(
                    f"evidence {evidence.evidence_id} is self-verified by {evidence.producer}"
                )

        for tool_call in self.tool_calls.values():
            if tool_call.status is ToolStatus.PASS and not tool_call.replayable:
                warnings.append(f"tool call {tool_call.call_id} is not cold-replayable")

        step_ids: set[str] = set()
        for step in self.public_reasoning:
            if step.step_id in step_ids:
                errors.append(f"duplicate public reasoning step {step.step_id}")
            step_ids.add(step.step_id)
            for claim_id in step.linked_claim_ids:
                if claim_id not in self.claims:
                    errors.append(f"reasoning step {step.step_id} has missing claim {claim_id}")

        serialized = canonical_json(self.to_dict())
        forbidden_tokens = (
            '"chain_of_thought"',
            '"private_chain_of_thought"',
            '"scratchpad"',
            '"hidden_reasoning"',
        )
        if any(token in serialized for token in forbidden_tokens):
            errors.append("trace contains a forbidden private-reasoning field")

        return {
            "valid": not errors,
            "run_id": self.run_id,
            "schema_version": self.schema_version,
            "errors": errors,
            "warnings": warnings,
            "counts": {
                "claims": len(self.claims),
                "routes": len(self.routes),
                "evidence": len(self.evidence),
                "tool_calls": len(self.tool_calls),
                "public_reasoning_steps": len(self.public_reasoning),
                "failures": len(self.failures),
                "boundary_violations": len(self.boundary_violations),
            },
            "trace_digest_sha256": self.content_digest(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "contract": self.contract.to_dict(),
            "claims": [self.claims[key].to_dict() for key in sorted(self.claims)],
            "routes": [self.routes[key].to_dict() for key in sorted(self.routes)],
            "evidence": [self.evidence[key].to_dict() for key in sorted(self.evidence)],
            "tool_calls": [
                self.tool_calls[key].to_dict() for key in sorted(self.tool_calls)
            ],
            "public_reasoning": [item.to_dict() for item in self.public_reasoning],
            "failures": [item.to_dict() for item in self.failures],
            "boundary_violations": self.boundary_violations,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResearchTrace":
        allowed = {
            "schema_version",
            "run_id",
            "contract",
            "claims",
            "routes",
            "evidence",
            "tool_calls",
            "public_reasoning",
            "failures",
            "boundary_violations",
            "metadata",
            "created_at",
            "updated_at",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise TraceValidationError(f"unknown trace fields: {sorted(unknown)}")
        trace = cls(
            run_id=str(payload["run_id"]),
            contract=TheoremContract.from_dict(payload["contract"]),
            metadata=dict(payload.get("metadata") or {}),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
            schema_version=str(payload.get("schema_version", "2.0")),
        )
        trace.claims = {
            item.claim_id: item
            for item in (ClaimRecord.from_dict(value) for value in payload.get("claims", []))
        }
        trace.routes = {
            item.route_id: item
            for item in (ResearchRoute.from_dict(value) for value in payload.get("routes", []))
        }
        trace.evidence = {
            item.evidence_id: item
            for item in (EvidenceRecord.from_dict(value) for value in payload.get("evidence", []))
        }
        trace.tool_calls = {
            item.call_id: item
            for item in (ToolCallRecord.from_dict(value) for value in payload.get("tool_calls", []))
        }
        trace.public_reasoning = [
            PublicReasoningStep.from_dict(value)
            for value in payload.get("public_reasoning", [])
        ]
        trace.failures = [
            FailureRecord.from_dict(value) for value in payload.get("failures", [])
        ]
        trace.boundary_violations = [
            dict(value) for value in payload.get("boundary_violations", [])
        ]
        validation = trace.validate()
        if not validation["valid"]:
            raise TraceValidationError("; ".join(validation["errors"]))
        return trace

    def content_digest(self) -> str:
        return digest_json(self.to_dict())

    def _promotion_issues(self, claim: ClaimRecord, required_groups: int) -> list[str]:
        issues: list[str] = []
        if claim.status in {ClaimStatus.REFUTED, ClaimStatus.RETRACTED}:
            issues.append(f"claim {claim.claim_id} is terminal ({claim.status.value})")
        missing_dependencies = [
            dependency
            for dependency in claim.dependencies
            if self.claims.get(dependency) is None
            or self.claims[dependency].status is not ClaimStatus.PROVED
        ]
        if missing_dependencies:
            issues.append(
                f"claim {claim.claim_id} has unproved dependencies {missing_dependencies}"
            )

        accepted = [
            self.evidence[evidence_id]
            for evidence_id in claim.evidence_ids
            if evidence_id in self.evidence
            and self.evidence[evidence_id].status is EvidenceStatus.ACCEPTED
        ]

        # v0.3 R0: HUMAN_AUDIT evidence derived from an expert ReviewRecord
        # must stop counting toward promotion the moment that review is no
        # longer ACTIVE (revoked) or the claim's statement has since moved
        # to a new revision the review never saw. This mirrors F2's opt-in,
        # lazily-checked pattern below: a claim with no review-derived
        # evidence is completely unaffected.
        try:
            from .review import ReviewContractError, stale_review_evidence_ids

            stale_review_ids = set(stale_review_evidence_ids(self, claim.claim_id))
        except ReviewContractError as exc:
            issues.append(f"claim {claim.claim_id} has invalid review metadata: {exc}")
            stale_review_ids = set()
        if stale_review_ids:
            issues.append(
                f"claim {claim.claim_id} has stale review-derived evidence excluded "
                f"from promotion: {sorted(stale_review_ids)}"
            )
            accepted = [item for item in accepted if item.evidence_id not in stale_review_ids]

        # Counterexamples are negative evidence. They are stored on the same
        # claim for provenance, but must never help that claim pass a positive
        # promotion gate.
        proof_capable = [
            item
            for item in accepted
            if item.kind
            not in {
                EvidenceKind.NUMERICAL_EXPERIMENT,
                EvidenceKind.HEURISTIC,
                EvidenceKind.COUNTEREXAMPLE,
            }
        ]
        if not proof_capable:
            issues.append(
                f"claim {claim.claim_id} has no accepted proof-capable evidence"
            )
        groups = {
            item.independence_group
            for item in proof_capable
            if item.independence_group.strip()
        }
        if len(groups) < required_groups:
            issues.append(
                f"claim {claim.claim_id} has {len(groups)} independent evidence groups; "
                f"requires {required_groups}"
            )
        if any(not item.statement_correspondence.strip() for item in proof_capable):
            issues.append(
                f"claim {claim.claim_id} has evidence without statement correspondence"
            )
        if claim.critical and any(not item.replayable for item in proof_capable):
            issues.append(
                f"critical claim {claim.claim_id} has non-replayable accepted evidence"
            )

        # v0.3 F2: once a route opts into the structured KillTestSpec protocol,
        # the unique promotion authority must fail closed until that active
        # route has a current PASS_BOUNDED RouteEvaluationRecord. Legacy v0.2
        # routes without a structured spec are intentionally ignored by the
        # helper, preserving replay compatibility for frozen traces.
        try:
            from .falsification import (
                FalsificationContractError,
                promotion_route_blockers,
            )

            route_blockers = promotion_route_blockers(self, claim.claim_id)
        except FalsificationContractError as exc:
            issues.append(
                f"claim {claim.claim_id} has invalid structured kill-test metadata: {exc}"
            )
        else:
            if route_blockers:
                issues.append(
                    f"claim {claim.claim_id} has active structured routes without a current "
                    f"PASS_BOUNDED evaluation: {list(route_blockers)}"
                )

        # v0.3 R4: a claim that closes partly or wholly on HUMAN_AUDIT
        # evidence must have every reviewer-facing obligation actually
        # meet its required_assurance (R2), not just have *some* evidence
        # attached. Opt-in: review_policy.review_gate_applies is False --
        # and this import produces no side effect -- for any claim that
        # never touches HUMAN_AUDIT evidence at all.
        try:
            from .review import ReviewContractError
            from .review_policy import assurance_blockers

            policy_blockers = assurance_blockers(self, claim.claim_id)
        except ReviewContractError as exc:
            issues.append(
                f"claim {claim.claim_id} has invalid review-assurance state: {exc}"
            )
        else:
            if policy_blockers:
                issues.extend(policy_blockers)
        return issues

    def _find_cycle(self) -> tuple[str, ...]:
        state: dict[str, int] = {}
        stack: list[str] = []

        def visit(claim_id: str) -> tuple[str, ...]:
            state[claim_id] = 1
            stack.append(claim_id)
            claim = self.claims[claim_id]
            for dependency in claim.dependencies:
                if dependency not in self.claims:
                    continue
                if state.get(dependency, 0) == 0:
                    cycle = visit(dependency)
                    if cycle:
                        return cycle
                elif state.get(dependency) == 1:
                    index = stack.index(dependency)
                    return tuple((*stack[index:], dependency))
            stack.pop()
            state[claim_id] = 2
            return ()

        for claim_id in sorted(self.claims):
            if state.get(claim_id, 0) == 0:
                cycle = visit(claim_id)
                if cycle:
                    return cycle
        return ()

    @staticmethod
    def _mechanism_signature(values: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted({" ".join(value.lower().split()) for value in values if value.strip()}))

    @staticmethod
    def _require_refs(
        values: Iterable[str],
        registry: Mapping[str, Any],
        label: str,
        owner: str,
    ) -> None:
        missing = [item for item in values if item not in registry]
        if missing:
            raise TraceValidationError(f"{owner} references unknown {label}s: {missing}")

    def _claim(self, claim_id: str) -> ClaimRecord:
        try:
            return self.claims[claim_id]
        except KeyError as exc:
            raise TraceValidationError(f"unknown claim id: {claim_id}") from exc

    def _route(self, route_id: str) -> ResearchRoute:
        try:
            return self.routes[route_id]
        except KeyError as exc:
            raise TraceValidationError(f"unknown route id: {route_id}") from exc


def save_trace(trace: ResearchTrace, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    validation = trace.validate()
    if not validation["valid"]:
        raise TraceValidationError("; ".join(validation["errors"]))
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(trace.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, target)
    return target


def load_trace(path: str | Path) -> ResearchTrace:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TraceValidationError("trace root must be a JSON object")
    return ResearchTrace.from_dict(payload)
