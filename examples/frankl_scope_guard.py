"""Demonstrate that fixed-parameter evidence cannot close global Frankl."""

from datetime import datetime, timezone

from matharc.engine import GuardViolation, ResearchEngine
from matharc.hashing import digest_json
from matharc.models import (
    ClaimNode,
    EvidenceArtifact,
    EvidenceKind,
    ResearchRun,
    RouteRecord,
    ScopeLevel,
    TheoremContract,
    TrustLevel,
)


def build() -> ResearchRun:
    now = datetime.now(timezone.utc).isoformat()
    run = ResearchRun(
        run_id="FRANKL-SCOPE-GUARD-DEMO",
        contract=TheoremContract(
            theorem_id="FRANKL-GLOBAL",
            title="Frankl's union-closed sets conjecture",
            statement="Every nontrivial finite union-closed family has an element in at least half its sets.",
            scope_level=ScopeLevel.GLOBAL,
            quantifiers=["every finite union-closed family"],
            assumptions=[],
            root_claim_id="F-GLOBAL",
            status_date=now[:10],
        ),
        created_at=now,
        updated_at=now,
    )
    engine = ResearchEngine(run)
    engine.add_route(RouteRecord("R-N5", "fixed ground set", "complete-enumeration", "finite"))
    engine.add_route(RouteRecord("R-GLOBAL", "global bridge", "quantifier-lift", "deductive"))
    engine.add_claim(
        ClaimNode(
            "F-N5",
            "Frankl holds for families on a ground set of size exactly five.",
            ScopeLevel.FINITE_RANGE,
            "complete-enumeration",
            "R-N5",
        )
    )
    engine.add_claim(
        ClaimNode(
            "F-GLOBAL",
            run.contract.statement,
            ScopeLevel.GLOBAL,
            "quantifier-lift",
            "R-GLOBAL",
            dependencies=["F-N5"],
        )
    )
    payload = {"parameter": 5, "complete": True, "certificate_count": 14480}
    evidence = EvidenceArtifact(
        evidence_id="E-N5",
        kind=EvidenceKind.EXACT_CERTIFICATE,
        trust_level=TrustLevel.EXACT,
        scope_level=ScopeLevel.FINITE_RANGE,
        producer="fixed-n-enumerator",
        payload=payload,
        sha256=digest_json(payload),
        replay_command="python verifier.py --n 5",
        output_digest=digest_json(payload),
    )
    engine.add_evidence(evidence)
    engine.attach_evidence("F-N5", "E-N5")
    engine.verify_claim("F-N5")
    engine.attach_evidence("F-GLOBAL", "E-N5")
    try:
        engine.verify_claim("F-GLOBAL")
    except GuardViolation:
        pass
    else:
        raise AssertionError("global Frankl promotion should have been blocked")
    return run


if __name__ == "__main__":
    guarded = build()
    print(guarded.guard_events[-1])
