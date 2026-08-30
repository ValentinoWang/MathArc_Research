from __future__ import annotations

import math
from collections import Counter
from typing import Any

from .engine import ResearchEngine
from .models import ClaimStatus, EvidenceKind, ResearchRun, TrustLevel


def compute_metrics(run: ResearchRun) -> dict[str, Any]:
    engine = ResearchEngine(run)
    claims = list(run.claims.values())
    critical = [item for item in claims if item.critical and item.status is not ClaimStatus.REFUTED]
    verified_critical = [item for item in critical if item.status is ClaimStatus.VERIFIED]
    closure = _percent(len(verified_critical), len(critical))

    maturity_values: list[float] = []
    for claim in claims:
        levels = [
            int(run.evidence[eid].trust_level)
            for eid in claim.evidence_ids
            if eid in run.evidence and run.evidence[eid].accepted
        ]
        maturity_values.append(max(levels, default=0) / int(TrustLevel.INDEPENDENT_REPLAY))
    evidence_maturity = 100 * (sum(maturity_values) / len(maturity_values) if maturity_values else 0)

    mechanism_counts = Counter(route.mechanism for route in run.routes.values())
    route_entropy, effective_mechanisms = _entropy(mechanism_counts)
    route_diversity = 100 * route_entropy

    accepted_evidence = [item for item in run.evidence.values() if item.accepted]
    replayable = [item for item in accepted_evidence if item.replay_command and item.output_digest]
    replayability = _percent(len(replayable), len(accepted_evidence))

    independent_claims = 0
    verified_claims = [item for item in claims if item.status is ClaimStatus.VERIFIED]
    for claim in verified_claims:
        if any(
            run.evidence[eid].kind is EvidenceKind.INDEPENDENT_RECONSTRUCTION
            for eid in claim.evidence_ids
            if eid in run.evidence
        ):
            independent_claims += 1
    independence = _percent(independent_claims, len(verified_claims))

    attempted = [item for item in claims if item.status is not ClaimStatus.PROPOSED]
    falsified = [item for item in claims if item.status is ClaimStatus.REFUTED]
    falsification_yield = _percent(len(falsified), len(attempted))

    failure_memory_complete = [
        item
        for item in run.failures
        if item.minimal_reproduction and item.regression_fixture and item.root_cause
    ]
    failure_memory = _percent(len(failure_memory_complete), len(run.failures))

    referenced_calls = {call_id for card in run.reasoning_cards for call_id in card.tool_call_ids}
    tool_trace = _percent(len(referenced_calls), len(run.tool_calls))

    guard_failures = [event for event in run.guard_events if not event.blocked]
    scope_safety = 100.0 if not guard_failures else 0.0

    debt = engine.certificate_debt()
    theorem_closure = 100.0 if run.release_state == "MACHINE_VERIFIED" else 0.0
    reliability = (
        0.18 * closure
        + 0.14 * evidence_maturity
        + 0.10 * route_diversity
        + 0.12 * replayability
        + 0.12 * independence
        + 0.12 * scope_safety
        + 0.08 * failure_memory
        + 0.06 * tool_trace
        + 0.08 * theorem_closure
    )

    return {
        "metric_semantics": "research-program measurements; not proof probability",
        "release_state": run.release_state,
        "theorem_closure_binary": 1 if theorem_closure == 100 else 0,
        "execution": {
            "claims_total": len(claims),
            "claims_verified": len(verified_claims),
            "tool_calls": len(run.tool_calls),
            "reasoning_cards": len(run.reasoning_cards),
            "failures_captured": len(run.failures),
            "guard_blocks": len(run.guard_events),
        },
        "scores": {
            "critical_obligation_closure": round(closure, 2),
            "evidence_maturity": round(evidence_maturity, 2),
            "route_diversity": round(route_diversity, 2),
            "replayability": round(replayability, 2),
            "independent_reconstruction": round(independence, 2),
            "falsification_yield": round(falsification_yield, 2),
            "failure_memory_completeness": round(failure_memory, 2),
            "tool_trace_coverage": round(tool_trace, 2),
            "scope_safety": round(scope_safety, 2),
            "theorem_closure": round(theorem_closure, 2),
            "research_reliability_index": round(reliability, 2),
        },
        "portfolio": {
            "physical_routes": len(run.routes),
            "effective_mechanisms": round(effective_mechanisms, 3),
            "normalized_route_entropy": round(route_entropy, 3),
            "mechanism_counts": dict(mechanism_counts),
        },
        "certificate_debt": debt,
    }


def _percent(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 100.0


def _entropy(counts: Counter[str]) -> tuple[float, float]:
    total = sum(counts.values())
    if total <= 1 or len(counts) <= 1:
        return (0.0 if total else 1.0, float(total))
    probabilities = [value / total for value in counts.values()]
    raw = -sum(value * math.log(value) for value in probabilities)
    normalized = raw / math.log(len(counts))
    return normalized, math.exp(raw)
