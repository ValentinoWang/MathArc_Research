from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any, Iterable

from .hashing import digest_json
from .models import (
    ClaimNode,
    ClaimStatus,
    EvidenceArtifact,
    EvidenceKind,
    FailureEvent,
    GuardEvent,
    ReasoningCard,
    ResearchRun,
    RouteRecord,
    ToolCallRecord,
    TrustLevel,
)


class GuardViolation(RuntimeError):
    """Raised when a claim promotion exceeds its evidence or dependency contract."""


class ResearchEngine:
    def __init__(self, run: ResearchRun):
        self.run = run

    def add_route(self, route: RouteRecord) -> None:
        if route.route_id in self.run.routes:
            raise ValueError(f"duplicate route: {route.route_id}")
        self.run.routes[route.route_id] = route
        self._touch()

    def add_claim(self, claim: ClaimNode) -> None:
        if claim.claim_id in self.run.claims:
            raise ValueError(f"duplicate claim: {claim.claim_id}")
        if claim.route_id not in self.run.routes:
            raise ValueError(f"unknown route: {claim.route_id}")
        missing = [dep for dep in claim.dependencies if dep not in self.run.claims]
        if missing:
            raise ValueError(f"missing dependencies for {claim.claim_id}: {missing}")
        self.run.claims[claim.claim_id] = claim
        if self._has_cycle():
            del self.run.claims[claim.claim_id]
            raise ValueError(f"claim dependency cycle introduced by {claim.claim_id}")
        self._touch()

    def add_evidence(self, evidence: EvidenceArtifact) -> None:
        if evidence.evidence_id in self.run.evidence:
            raise ValueError(f"duplicate evidence: {evidence.evidence_id}")
        expected = digest_json(evidence.payload)
        if evidence.sha256 != expected:
            raise ValueError(
                f"evidence digest mismatch for {evidence.evidence_id}: {evidence.sha256} != {expected}"
            )
        self.run.evidence[evidence.evidence_id] = evidence
        self._touch()

    def attach_evidence(self, claim_id: str, evidence_id: str) -> None:
        claim = self._claim(claim_id)
        if evidence_id not in self.run.evidence:
            raise ValueError(f"unknown evidence: {evidence_id}")
        if evidence_id not in claim.evidence_ids:
            claim.evidence_ids.append(evidence_id)
        self._touch()

    def add_tool_call(self, call: ToolCallRecord) -> None:
        if any(existing.call_id == call.call_id for existing in self.run.tool_calls):
            raise ValueError(f"duplicate tool call: {call.call_id}")
        self.run.tool_calls.append(call)
        self._touch()

    def add_reasoning_card(self, card: ReasoningCard) -> None:
        if any(existing.card_id == card.card_id for existing in self.run.reasoning_cards):
            raise ValueError(f"duplicate reasoning card: {card.card_id}")
        if card.sequence <= 0:
            raise ValueError("reasoning-card sequence must be positive")
        self.run.reasoning_cards.append(card)
        self.run.reasoning_cards.sort(key=lambda item: item.sequence)
        self._touch()

    def set_active(self, claim_id: str) -> None:
        claim = self._claim(claim_id)
        if claim.status not in {ClaimStatus.PROPOSED, ClaimStatus.BLOCKED}:
            raise GuardViolation(f"cannot activate {claim_id} from {claim.status.value}")
        claim.status = ClaimStatus.ACTIVE
        self._touch()

    def set_tested(self, claim_id: str) -> None:
        claim = self._claim(claim_id)
        if claim.status in {ClaimStatus.REFUTED, ClaimStatus.INVALIDATED}:
            raise GuardViolation(f"cannot test dead claim {claim_id}")
        claim.status = ClaimStatus.TESTED
        self._touch()

    def verify_claim(self, claim_id: str) -> None:
        claim = self._claim(claim_id)
        if claim.status in {ClaimStatus.REFUTED, ClaimStatus.INVALIDATED}:
            self._guard("dead-claim-promotion", claim_id, "refuted/invalidated claim cannot verify")
        for dependency in claim.dependencies:
            dep = self._claim(dependency)
            if dep.status is not ClaimStatus.VERIFIED:
                self._guard(
                    "dependency-not-verified",
                    claim_id,
                    f"dependency {dependency} is {dep.status.value}",
                )
        artifacts = [self.run.evidence[item] for item in claim.evidence_ids]
        accepted = [item for item in artifacts if item.accepted]
        if not accepted:
            self._guard("missing-evidence", claim_id, "claim has no accepted evidence")
        eligible = [
            item
            for item in accepted
            if item.scope_level >= claim.scope_level and item.trust_level >= claim.required_trust
        ]
        if not eligible:
            maximum_scope = max((int(item.scope_level) for item in accepted), default=-1)
            maximum_trust = max((int(item.trust_level) for item in accepted), default=-1)
            self._guard(
                "scope-or-trust-gap",
                claim_id,
                f"required scope={claim.scope_level.name}, trust={claim.required_trust.name}; "
                f"available max scope={maximum_scope}, trust={maximum_trust}",
            )
        policy = self.run.contract.verifier_policy
        if claim_id == self.run.contract.root_claim_id:
            if max(item.trust_level for item in eligible) < policy.minimum_root_trust:
                self._guard("root-trust-gap", claim_id, "root trust policy not met")
            if policy.require_replay_command and not any(item.replay_command for item in eligible):
                self._guard("root-not-replayable", claim_id, "root evidence lacks replay command")
            if policy.require_independent_root_evidence and not self._independence_met(accepted):
                self._guard(
                    "independent-reconstruction-missing",
                    claim_id,
                    "root needs accepted independent reconstruction evidence",
                )
        claim.status = ClaimStatus.VERIFIED
        if claim.route_id in self.run.routes:
            self.run.routes[claim.route_id].verified_gain += 1
        self._refresh_release_state()
        self._touch()

    def refute_claim(
        self,
        claim_id: str,
        *,
        classification: str,
        root_cause: str,
        minimal_reproduction: dict[str, Any],
        regression_fixture: str,
    ) -> FailureEvent:
        claim = self._claim(claim_id)
        claim.status = ClaimStatus.REFUTED
        descendants = self._descendants(claim_id)
        for descendant_id in descendants:
            descendant = self._claim(descendant_id)
            if descendant.status is not ClaimStatus.REFUTED:
                descendant.status = ClaimStatus.INVALIDATED
                descendant.invalidated_by = claim_id
        failure = FailureEvent(
            failure_id=f"F-{len(self.run.failures) + 1:04d}",
            claim_id=claim_id,
            classification=classification,
            root_cause=root_cause,
            minimal_reproduction=minimal_reproduction,
            invalidated_claim_ids=descendants,
            regression_fixture=regression_fixture,
        )
        self.run.failures.append(failure)
        self._refresh_release_state()
        self._touch()
        return failure

    def block_claim(self, claim_id: str, reason: str) -> None:
        claim = self._claim(claim_id)
        claim.status = ClaimStatus.BLOCKED
        claim.notes.append(reason)
        self._refresh_release_state()
        self._touch()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.run.contract.root_claim_id not in self.run.claims:
            errors.append("root claim is missing")
        if self._has_cycle():
            errors.append("claim graph contains a cycle")
        tool_ids = {item.call_id for item in self.run.tool_calls}
        evidence_ids = set(self.run.evidence)
        claim_ids = set(self.run.claims)
        for card in self.run.reasoning_cards:
            if any(item not in tool_ids for item in card.tool_call_ids):
                errors.append(f"reasoning card {card.card_id} references unknown tool call")
            if any(item not in evidence_ids for item in card.evidence_ids):
                errors.append(f"reasoning card {card.card_id} references unknown evidence")
            if any(item not in claim_ids for item in card.claim_ids):
                errors.append(f"reasoning card {card.card_id} references unknown claim")
        for claim in self.run.claims.values():
            if any(dep not in claim_ids for dep in claim.dependencies):
                errors.append(f"claim {claim.claim_id} has unknown dependency")
            if any(eid not in evidence_ids for eid in claim.evidence_ids):
                errors.append(f"claim {claim.claim_id} has unknown evidence")
            if claim.status is ClaimStatus.VERIFIED:
                for dep in claim.dependencies:
                    if self.run.claims[dep].status is not ClaimStatus.VERIFIED:
                        errors.append(f"verified claim {claim.claim_id} has unverified dependency {dep}")
        if self.run.release_state == "MACHINE_VERIFIED":
            root = self.run.claims.get(self.run.contract.root_claim_id)
            if root is None or root.status is not ClaimStatus.VERIFIED:
                errors.append("release state is MACHINE_VERIFIED but root is not verified")
        return errors

    def certificate_debt(self) -> list[str]:
        debt: list[str] = []
        for claim in self.run.claims.values():
            if not claim.critical or claim.status is ClaimStatus.REFUTED:
                continue
            artifacts = [self.run.evidence[item] for item in claim.evidence_ids]
            exact = any(
                item.accepted
                and item.scope_level >= claim.scope_level
                and item.trust_level >= claim.required_trust
                for item in artifacts
            )
            if claim.status is not ClaimStatus.VERIFIED or not exact:
                debt.append(claim.claim_id)
        return debt

    def _independence_met(self, artifacts: Iterable[EvidenceArtifact]) -> bool:
        independent = [
            item
            for item in artifacts
            if item.accepted
            and item.kind is EvidenceKind.INDEPENDENT_RECONSTRUCTION
            and item.scope_level >= self.run.contract.scope_level
            and item.trust_level >= TrustLevel.EXACT
        ]
        return bool(independent)

    def _guard(self, rule: str, claim_id: str, message: str) -> None:
        event = GuardEvent(
            guard_id=f"G-{len(self.run.guard_events) + 1:04d}",
            rule=rule,
            claim_id=claim_id,
            message=message,
        )
        self.run.guard_events.append(event)
        self._touch()
        raise GuardViolation(f"{rule}: {claim_id}: {message}")

    def _refresh_release_state(self) -> None:
        root = self.run.claims.get(self.run.contract.root_claim_id)
        if root is None:
            self.run.release_state = "DRAFT"
            return
        if root.status is ClaimStatus.VERIFIED and not self.certificate_debt():
            self.run.release_state = "MACHINE_VERIFIED"
        elif root.status in {ClaimStatus.REFUTED, ClaimStatus.INVALIDATED}:
            self.run.release_state = "REFUTED_OR_INVALIDATED"
        elif any(item.status is ClaimStatus.BLOCKED for item in self.run.claims.values()):
            self.run.release_state = "BLOCKED"
        else:
            self.run.release_state = "INCONCLUSIVE"

    def _claim(self, claim_id: str) -> ClaimNode:
        try:
            return self.run.claims[claim_id]
        except KeyError as exc:
            raise ValueError(f"unknown claim: {claim_id}") from exc

    def _descendants(self, claim_id: str) -> list[str]:
        children: dict[str, list[str]] = {key: [] for key in self.run.claims}
        for node in self.run.claims.values():
            for dep in node.dependencies:
                children.setdefault(dep, []).append(node.claim_id)
        result: list[str] = []
        queue: deque[str] = deque(children.get(claim_id, []))
        seen: set[str] = set()
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            result.append(current)
            queue.extend(children.get(current, []))
        return result

    def _has_cycle(self) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in visiting:
                return True
            if node_id in visited:
                return False
            visiting.add(node_id)
            for dep in self.run.claims[node_id].dependencies:
                if dep in self.run.claims and visit(dep):
                    return True
            visiting.remove(node_id)
            visited.add(node_id)
            return False

        return any(visit(node_id) for node_id in self.run.claims if node_id not in visited)

    def _touch(self) -> None:
        self.run.updated_at = datetime.now(timezone.utc).isoformat()
