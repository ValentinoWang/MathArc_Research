from __future__ import annotations

import math
from collections import Counter
from functools import lru_cache
from typing import Any, Iterable

from .falsification import FalsificationContractError, iter_route_evaluations
from .review import ReviewContractError
from .review_policy import assurance_snapshot_for_claim, claim_closure_trust_class, review_gate_applies
from .schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceStatus,
    RouteStatus,
    ToolStatus,
)
from .trace import ResearchTrace


def _ratio(numerator: float, denominator: float, *, empty: float = 1.0) -> float:
    if denominator <= 0:
        return empty
    return max(0.0, min(1.0, numerator / denominator))


def _geometric_mean(values: Iterable[float]) -> float:
    items = [max(0.0, min(1.0, float(item))) for item in values]
    if not items:
        return 0.0
    if any(item == 0.0 for item in items):
        return 0.0
    return math.exp(sum(math.log(item) for item in items) / len(items))


def _mechanism_diversity(trace: ResearchTrace) -> float:
    routes = [
        route
        for route in trace.routes.values()
        if route.status not in {RouteStatus.ABANDONED}
    ]
    if len(routes) <= 1:
        return 1.0 if routes else 0.0
    distances: list[float] = []
    for index, left in enumerate(routes):
        left_set = {value.lower().strip() for value in left.mechanism_signature}
        for right in routes[index + 1 :]:
            right_set = {value.lower().strip() for value in right.mechanism_signature}
            union = left_set | right_set
            similarity = len(left_set & right_set) / len(union) if union else 1.0
            distances.append(1.0 - similarity)
    return sum(distances) / len(distances)


def _critical_path_score(trace: ResearchTrace) -> tuple[float, list[dict[str, Any]]]:
    @lru_cache(maxsize=None)
    def heaviest_path(claim_id: str) -> tuple[float, tuple[str, ...]]:
        claim = trace.claims[claim_id]
        if not claim.dependencies:
            return claim.weight, (claim_id,)
        candidates = [heaviest_path(dependency) for dependency in claim.dependencies]
        dependency_weight, dependency_path = max(candidates, key=lambda item: item[0])
        return dependency_weight + claim.weight, (*dependency_path, claim_id)

    path_rows: list[dict[str, Any]] = []
    target_scores: list[float] = []
    for target_id in trace.contract.target_claim_ids:
        if target_id not in trace.claims:
            continue
        total_weight, path = heaviest_path(target_id)
        closed_weight = sum(
            trace.claims[claim_id].weight
            for claim_id in path
            if trace.claims[claim_id].status is ClaimStatus.PROVED
        )
        score = _ratio(closed_weight, total_weight, empty=0.0)
        target_scores.append(score)
        path_rows.append(
            {
                "target_claim_id": target_id,
                "path": list(path),
                "closed_weight": closed_weight,
                "total_weight": total_weight,
                "closure": score,
            }
        )
    return (min(target_scores) if target_scores else 0.0), path_rows


def _proof_capable_evidence(trace: ResearchTrace, claim: ClaimRecord) -> list[Any]:
    return [
        trace.evidence[evidence_id]
        for evidence_id in claim.evidence_ids
        if evidence_id in trace.evidence
        and trace.evidence[evidence_id].status is EvidenceStatus.ACCEPTED
        and trace.evidence[evidence_id].kind
        not in {
            EvidenceKind.NUMERICAL_EXPERIMENT,
            EvidenceKind.HEURISTIC,
            EvidenceKind.COUNTEREXAMPLE,
        }
    ]


def _release_state(trace: ResearchTrace, validation: dict[str, Any]) -> str:
    targets = [trace.claims.get(item) for item in trace.contract.target_claim_ids]
    if any(item is not None and item.status is ClaimStatus.REFUTED for item in targets):
        return "REFUTED_EXACT" if any(failure.exact for failure in trace.failures) else "REFUTED"
    if targets and all(item is not None and item.status is ClaimStatus.PROVED for item in targets):
        if validation["valid"] and not validation["warnings"]:
            return "PROVED_AND_AUDITED"
        return "PROVED_WITH_AUDIT_DEBT"
    if any(item is not None and item.status is ClaimStatus.CANDIDATE for item in targets):
        return "CANDIDATE_UNVERIFIED"
    if any(item is not None and item.status is ClaimStatus.BLOCKED for item in targets):
        return "BLOCKED_EXACT"
    return "OPEN_RESEARCH"


def compute_research_metrics(trace: ResearchTrace) -> dict[str, Any]:
    """Compute auditable research metrics.

    These metrics measure closure of an explicit dependency graph and quality of
    the attached evidence. They are not probabilities that an open theorem is
    true and are not estimates of time remaining.
    """

    validation = trace.validate()
    claims = list(trace.claims.values())
    total_weight = sum(claim.weight for claim in claims)
    proved_weight = sum(
        claim.weight for claim in claims if claim.status is ClaimStatus.PROVED
    )
    weighted_proof_closure = _ratio(proved_weight, total_weight, empty=0.0)

    critical_path_closure, critical_paths = _critical_path_score(trace)

    critical_claims = [claim for claim in claims if claim.critical]
    independence_numerator = 0.0
    independence_denominator = 0.0
    statement_numerator = 0.0
    statement_denominator = 0.0
    critical_audited_weight = 0.0
    critical_weight = sum(claim.weight for claim in critical_claims)
    proof_capable_ids: set[str] = set()
    review_assurance: dict[str, dict[str, Any]] = {}
    for claim in claims:
        evidence = _proof_capable_evidence(trace, claim)
        proof_capable_ids.update(item.evidence_id for item in evidence)
        groups = {item.independence_group for item in evidence if item.independence_group}
        required = 2 if claim.critical else 1
        independence_numerator += claim.weight * min(1.0, len(groups) / required)
        independence_denominator += claim.weight
        for item in evidence:
            statement_denominator += 1.0
            statement_numerator += bool(item.statement_correspondence.strip())
        if claim.critical and len(groups) >= 2 and all(item.replayable for item in evidence):
            critical_audited_weight += claim.weight

        # v0.3 R4: closure_trust_class and the per-obligation assurance
        # snapshot. Cheap and harmless for every claim; the obligation
        # snapshot itself is only populated when review_gate_applies (the
        # claim actually relies on HUMAN_AUDIT evidence) to avoid spending
        # a bundle rebuild on claims that never touch review.py.
        try:
            trust_class = claim_closure_trust_class(trace, claim.claim_id).value
            gate_applies = review_gate_applies(trace, claim.claim_id)
            obligations = (
                [item.to_dict() for item in assurance_snapshot_for_claim(trace, claim.claim_id)]
                if gate_applies
                else []
            )
        except ReviewContractError as exc:
            trust_class = "unknown"
            gate_applies = False
            obligations = [{"error": str(exc)}]
        review_assurance[claim.claim_id] = {
            "closure_trust_class": trust_class,
            "review_gate_applies": gate_applies,
            "obligations": obligations,
        }

    evidence_independence = _ratio(
        independence_numerator, independence_denominator, empty=0.0
    )
    statement_correspondence = _ratio(
        statement_numerator, statement_denominator, empty=0.0
    )
    independent_audit_coverage = _ratio(
        critical_audited_weight, critical_weight, empty=1.0
    )

    accepted_evidence = [
        item for item in trace.evidence.values() if item.status is EvidenceStatus.ACCEPTED
    ]
    counterexample_evidence = [
        item
        for item in accepted_evidence
        if item.kind is EvidenceKind.COUNTEREXAMPLE
    ]
    exact_or_formal_evidence = [
        item
        for item in accepted_evidence
        if item.kind
        in {
            EvidenceKind.FORMAL_PROOF,
            EvidenceKind.CHECKED_DERIVATION,
            EvidenceKind.EXACT_CERTIFICATE,
            EvidenceKind.EXACT_COMPUTATION,
        }
    ]
    passing_tools = [
        item for item in trace.tool_calls.values() if item.status is ToolStatus.PASS
    ]
    replayable_count = sum(item.replayable for item in accepted_evidence) + sum(
        item.replayable for item in passing_tools
    )
    replayable_total = len(accepted_evidence) + len(passing_tools)
    cold_replay_rate = _ratio(replayable_count, replayable_total, empty=0.0)

    tool_complete = sum(
        bool(
            item.purpose.strip()
            and item.input_digest_sha256
            and item.output_digest_sha256
            and item.replay_command.strip()
            and item.expected_discriminator.strip()
        )
        for item in trace.tool_calls.values()
    )
    tool_transparency = _ratio(tool_complete, len(trace.tool_calls), empty=1.0)

    route_failure_ids = {failure.route_id for failure in trace.failures}
    route_reasoning_ids = {
        route_id
        for step in trace.public_reasoning
        if step.falsification_test.strip() and step.observation.strip()
        for route_id in step.linked_route_ids
    }
    structured_route_ids: set[str] = set()
    try:
        structured_route_ids = {
            item.route_id for item in iter_route_evaluations(trace)
        }
        structured_route_evaluation_count = len(iter_route_evaluations(trace))
    except FalsificationContractError:
        structured_route_evaluation_count = 0
    falsified_or_tested = route_failure_ids | route_reasoning_ids | structured_route_ids
    falsification_coverage = _ratio(
        len(falsified_or_tested), len(trace.routes), empty=0.0
    )

    claims_with_reasoning = {
        claim_id for step in trace.public_reasoning for claim_id in step.linked_claim_ids
    }
    public_trace_coverage = _ratio(
        sum(trace.claims[item].weight for item in claims_with_reasoning if item in trace.claims),
        total_weight,
        empty=0.0,
    )

    useful_failures = sum(
        bool(item.diagnosis.strip() and item.repair.strip() and item.reusable_lesson.strip())
        for item in trace.failures
    )
    reused_failures = sum(item.reused_count > 0 for item in trace.failures)
    useful_failure_rate = _ratio(useful_failures, len(trace.failures), empty=1.0)
    failure_reuse_rate = _ratio(reused_failures, len(trace.failures), empty=0.0)

    boundary_integrity = 1.0 / (1.0 + len(trace.boundary_violations))
    route_diversity = _mechanism_diversity(trace)

    target_claims = [
        trace.claims[item]
        for item in trace.contract.target_claim_ids
        if item in trace.claims
    ]
    target_closure = _ratio(
        sum(item.weight for item in target_claims if item.status is ClaimStatus.PROVED),
        sum(item.weight for item in target_claims),
        empty=0.0,
    )

    readiness_components = {
        "critical_path_closure": critical_path_closure,
        "evidence_independence": evidence_independence,
        "independent_audit_coverage": independent_audit_coverage,
        "cold_replay_rate": cold_replay_rate,
        "falsification_coverage": falsification_coverage,
        "boundary_integrity": boundary_integrity,
        "tool_transparency": tool_transparency,
        "public_trace_coverage": public_trace_coverage,
    }
    research_readiness_index = _geometric_mean(readiness_components.values())
    release_state = _release_state(trace, validation)

    status_counts = Counter(claim.status.value for claim in claims)
    route_counts = Counter(route.status.value for route in trace.routes.values())
    open_critical = [
        claim.claim_id
        for claim in critical_claims
        if claim.status is not ClaimStatus.PROVED
    ]
    terminal_route_count = sum(
        route.status in {RouteStatus.BLOCKED, RouteStatus.FALSIFIED, RouteStatus.CLOSED}
        for route in trace.routes.values()
    )
    scope_events = trace.metadata.get("v03_scope_narrowing_events", [])
    scope_narrowing_count = len(scope_events) if isinstance(scope_events, list) else 0

    return {
        "schema_version": "2.0",
        "run_id": trace.run_id,
        "release_state": release_state,
        "metric_semantics": (
            "Dependency-graph and evidence-quality completion; not probability, "
            "fraction of mathematical instances, or time estimate."
        ),
        "weighted_proof_closure": weighted_proof_closure,
        "target_logical_closure": target_closure,
        "critical_path_closure": critical_path_closure,
        "evidence_independence": evidence_independence,
        "independent_audit_coverage": independent_audit_coverage,
        "statement_correspondence": statement_correspondence,
        "cold_replay_rate": cold_replay_rate,
        "tool_transparency": tool_transparency,
        "falsification_coverage": falsification_coverage,
        "public_trace_coverage": public_trace_coverage,
        "route_mechanism_diversity": route_diversity,
        "useful_failure_rate": useful_failure_rate,
        "failure_reuse_rate": failure_reuse_rate,
        "boundary_integrity": boundary_integrity,
        "research_readiness_index": research_readiness_index,
        "readiness_components": readiness_components,
        "claim_status_counts": dict(sorted(status_counts.items())),
        "route_status_counts": dict(sorted(route_counts.items())),
        "open_critical_obligations": open_critical,
        "critical_paths": critical_paths,
        "validation": validation,
        "marketing_claim_allowed": release_state == "PROVED_AND_AUDITED",
        "accounting": {
            "proved_claim_count": sum(
                claim.status is ClaimStatus.PROVED for claim in claims
            ),
            "terminal_route_count": terminal_route_count,
            "accepted_evidence_count": len(accepted_evidence),
            "proof_capable_evidence_count": len(proof_capable_ids),
            "counterexample_evidence_count": len(counterexample_evidence),
            "exact_or_formal_evidence_count": len(exact_or_formal_evidence),
            "structured_route_evaluation_count": structured_route_evaluation_count,
            "scope_narrowing_count": scope_narrowing_count,
        },
        "review_assurance": review_assurance,
        "review_assurance_policy_status": (
            "CODED_DEFAULT_PENDING_CHIEF_SCIENTIST_SIGN_OFF -- see review_policy.py"
        ),
        "claim_boundary": (
            "A high readiness score cannot promote an unproved target. Only the "
            "release_state and target_logical_closure govern theorem-completion claims."
        ),
        "definitions": {
            "weighted_proof_closure": "proved claim weight divided by declared claim weight",
            "critical_path_closure": "minimum proved-weight fraction on a heaviest dependency path to each target",
            "evidence_independence": "weighted satisfaction of independent-evidence requirements",
            "cold_replay_rate": "accepted evidence and passing tools with complete replay contracts",
            "falsification_coverage": "routes with an executed and recorded kill test, including typed v0.3 RouteEvaluationRecord entries",
            "boundary_integrity": "penalty for attempted promotion beyond evidence",
            "route_mechanism_diversity": "mean pairwise Jaccard distance of mechanism signatures",
            "research_readiness_index": "geometric mean of process-quality components; not theorem truth probability",
        },
    }
