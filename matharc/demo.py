from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .dashboard import render_dashboard
from .engine import ResearchEngine
from .hashing import digest_json
from .metrics import compute_metrics
from .models import (
    ClaimNode,
    EvidenceArtifact,
    EvidenceKind,
    ReasoningCard,
    ResearchRun,
    RouteRecord,
    ScopeLevel,
    TheoremContract,
    TrustLevel,
    VerifierPolicy,
)
from .store import save_run
from .tools import FiniteOddSumTool, InductionCertificateTool, PolynomialIdentityTool


def build_demo_run() -> ResearchRun:
    now = datetime.now(timezone.utc).isoformat()
    contract = TheoremContract(
        theorem_id="ODD-SUM-INDUCTION-001",
        title="Sum of the first n odd numbers",
        statement="For every natural number n, sum_{k=1}^n (2k-1) = n^2.",
        scope_level=ScopeLevel.GLOBAL,
        quantifiers=["for every n in the natural numbers"],
        assumptions=["ordinary induction on natural numbers", "exact integer arithmetic"],
        root_claim_id="C-ROOT",
        status_date=now[:10],
        verifier_policy=VerifierPolicy(
            minimum_root_trust=TrustLevel.EXACT,
            require_independent_root_evidence=True,
            require_replay_command=True,
            require_all_critical_claims=True,
        ),
    )
    run = ResearchRun(
        run_id="DEMO-ODD-SUM-001",
        contract=contract,
        created_at=now,
        updated_at=now,
    )
    engine = ResearchEngine(run)

    engine.add_route(RouteRecord("R-FINITE", "finite reconnaissance", "finite-enumeration", "computational"))
    engine.add_route(RouteRecord("R-BAD", "naive recurrence", "shortcut-recurrence", "algebraic"))
    engine.add_route(RouteRecord("R-IND", "exact induction", "induction-certificate", "deductive"))
    engine.add_route(RouteRecord("R-RECON", "independent reconstruction", "coefficient-normalization", "symbolic"))

    engine.add_claim(
        ClaimNode(
            "C-FINITE",
            "The identity holds for 0 <= n <= 100.",
            ScopeLevel.FINITE_RANGE,
            "finite-enumeration",
            "R-FINITE",
            required_trust=TrustLevel.TESTED,
            critical=False,
        )
    )
    engine.add_claim(
        ClaimNode(
            "C-BAD-LEMMA",
            "For every n, (n+1)^2 = n^2 + 1.",
            ScopeLevel.GLOBAL,
            "shortcut-recurrence",
            "R-BAD",
            critical=False,
        )
    )
    engine.add_claim(
        ClaimNode(
            "C-BAD-ROUTE",
            "The target theorem follows from the shortcut recurrence.",
            ScopeLevel.GLOBAL,
            "shortcut-recurrence",
            "R-BAD",
            dependencies=["C-BAD-LEMMA"],
            critical=False,
        )
    )
    engine.add_claim(
        ClaimNode(
            "C-BASE",
            "The identity holds at n=0.",
            ScopeLevel.INSTANCE,
            "induction-certificate",
            "R-IND",
            required_trust=TrustLevel.EXACT,
        )
    )
    engine.add_claim(
        ClaimNode(
            "C-STEP",
            "Assuming S(n)=n^2, adding the next odd number gives S(n+1)=(n+1)^2.",
            ScopeLevel.PARAMETRIC_FAMILY,
            "induction-certificate",
            "R-IND",
            dependencies=["C-BASE"],
            required_trust=TrustLevel.EXACT,
        )
    )
    engine.add_claim(
        ClaimNode(
            "C-INDUCTION",
            "Base and step establish the identity for all natural n.",
            ScopeLevel.GLOBAL,
            "induction-certificate",
            "R-IND",
            dependencies=["C-BASE", "C-STEP"],
            required_trust=TrustLevel.EXACT,
        )
    )
    engine.add_claim(
        ClaimNode(
            "C-ROOT",
            contract.statement,
            ScopeLevel.GLOBAL,
            "proof-composition",
            "R-IND",
            dependencies=["C-INDUCTION"],
            required_trust=TrustLevel.EXACT,
        )
    )

    finite = FiniteOddSumTool().run("T-FINITE-001", 100)
    finite.call.claim_ids = ["C-FINITE"]
    engine.add_tool_call(finite.call)
    finite_evidence = _evidence(
        "E-FINITE",
        EvidenceKind.COMPUTATION,
        TrustLevel.TESTED,
        ScopeLevel.FINITE_RANGE,
        "finite-odd-sum-checker",
        finite.output,
        finite.call.replay_command,
        finite.call.output_digest,
    )
    engine.add_evidence(finite_evidence)
    engine.attach_evidence("C-FINITE", "E-FINITE")
    engine.verify_claim("C-FINITE")

    bad = PolynomialIdentityTool().run("T-BAD-001", "(n+1)**2", "n**2+1")
    bad.call.claim_ids = ["C-BAD-LEMMA", "C-BAD-ROUTE"]
    engine.add_tool_call(bad.call)
    bad_evidence = _evidence(
        "E-BAD",
        EvidenceKind.COUNTEREXAMPLE,
        TrustLevel.EXACT,
        ScopeLevel.GLOBAL,
        "polynomial-identity-exact",
        bad.output,
        bad.call.replay_command,
        bad.call.output_digest,
    )
    engine.add_evidence(bad_evidence)
    engine.attach_evidence("C-BAD-LEMMA", "E-BAD")
    engine.refute_claim(
        "C-BAD-LEMMA",
        classification="FALSE_ALGEBRAIC_BRIDGE",
        root_cause="The proposed recurrence drops the 2n term.",
        minimal_reproduction={"n": 1, "lhs": 4, "rhs": 2},
        regression_fixture="tests/fixtures/false_recurrence.json",
    )

    certificate = {
        "variable": "n",
        "domain": "natural numbers",
        "base": {"at": 0, "lhs": "0", "rhs": "n**2"},
        "step": {"lhs": "n**2 + 2*(n+1)-1", "rhs": "(n+1)**2"},
    }
    induction = InductionCertificateTool().run("T-IND-001", certificate)
    induction.call.claim_ids = ["C-BASE", "C-STEP", "C-INDUCTION", "C-ROOT"]
    engine.add_tool_call(induction.call)
    base_payload = {"certificate": certificate["base"], "check": induction.output["base"]}
    engine.add_evidence(
        _evidence(
            "E-BASE",
            EvidenceKind.EXACT_CERTIFICATE,
            TrustLevel.EXACT,
            ScopeLevel.INSTANCE,
            "induction-certificate-checker",
            base_payload,
            induction.call.replay_command,
            digest_json(base_payload),
        )
    )
    step_payload = {"certificate": certificate["step"], "check": induction.output["step"]}
    engine.add_evidence(
        _evidence(
            "E-STEP",
            EvidenceKind.EXACT_CERTIFICATE,
            TrustLevel.EXACT,
            ScopeLevel.PARAMETRIC_FAMILY,
            "induction-certificate-checker",
            step_payload,
            induction.call.replay_command,
            digest_json(step_payload),
        )
    )
    engine.add_evidence(
        _evidence(
            "E-INDUCTION",
            EvidenceKind.EXACT_CERTIFICATE,
            TrustLevel.EXACT,
            ScopeLevel.GLOBAL,
            "induction-certificate-checker",
            induction.output,
            induction.call.replay_command,
            induction.call.output_digest,
        )
    )
    engine.attach_evidence("C-BASE", "E-BASE")
    engine.verify_claim("C-BASE")
    engine.attach_evidence("C-STEP", "E-STEP")
    engine.verify_claim("C-STEP")
    engine.attach_evidence("C-INDUCTION", "E-INDUCTION")
    engine.verify_claim("C-INDUCTION")
    engine.attach_evidence("C-ROOT", "E-INDUCTION")

    reconstruction = PolynomialIdentityTool().run(
        "T-RECON-001", "n**2 + 2*n + 1", "(n+1)**2"
    )
    reconstruction.call.claim_ids = ["C-ROOT"]
    engine.add_tool_call(reconstruction.call)
    engine.add_evidence(
        _evidence(
            "E-RECON",
            EvidenceKind.INDEPENDENT_RECONSTRUCTION,
            TrustLevel.INDEPENDENT_REPLAY,
            ScopeLevel.GLOBAL,
            "independent-coefficient-normalizer",
            reconstruction.output,
            reconstruction.call.replay_command,
            reconstruction.call.output_digest,
            independent_of=["induction-certificate-checker"],
        )
    )
    engine.attach_evidence("C-ROOT", "E-RECON")
    engine.verify_claim("C-ROOT")

    cards = [
        ReasoningCard(
            "RC-001", 1,
            "Freeze the theorem and its quantifier scope.",
            "The target is universal over natural numbers, so finite checks cannot close it.",
            "Create a GLOBAL theorem contract and a separate FINITE_RANGE reconnaissance claim.",
            "The scope lattice makes the promotion boundary explicit.",
            "Attaching finite evidence directly to the root would trigger the scope guard.",
            "Keep finite search as reconnaissance only.",
            "Universal theorem frozen; finite evidence is deliberately non-conclusive.",
            ["C-FINITE", "C-ROOT"], [], []
        ),
        ReasoningCard(
            "RC-002", 2,
            "Search cheap instances for a defect or pattern.",
            "A failure below n=100 would immediately refute the theorem.",
            "Run the exact finite checker on n=0..100.",
            "No failure is found on 101 cases.",
            "The tool explicitly labels the result finite-range and non-proving.",
            "Continue to a universal bridge rather than promote the result.",
            "Finite evidence raises confidence in the route but creates no quantifier lift.",
            ["C-FINITE"], ["E-FINITE"], ["T-FINITE-001"]
        ),
        ReasoningCard(
            "RC-003", 3,
            "Attack a tempting shortcut recurrence.",
            "Perhaps the square increases by one at each step.",
            "Normalize both polynomials and compare coefficients exactly.",
            "The difference is 2n; n=1 is a minimal counterexample.",
            "The counterexample refutes the lemma and invalidates its dependent route.",
            "Archive the failure as a regression fixture; do not repair the route by wording.",
            "A false bridge was killed early and its downstream claim was invalidated automatically.",
            ["C-BAD-LEMMA", "C-BAD-ROUTE"], ["E-BAD"], ["T-BAD-001"]
        ),
        ReasoningCard(
            "RC-004", 4,
            "Construct an exact universal bridge.",
            "Induction reduces the theorem to a base case and a polynomial step.",
            "Check the base and normalize n^2+2(n+1)-1 against (n+1)^2.",
            "Both obligations are exact identities.",
            "The certificate contains the quantifier lift and accepted induction principle.",
            "Verify the base, step, and induction claims in dependency order.",
            "The universal proof is certificate-backed, subject to independent reconstruction.",
            ["C-BASE", "C-STEP", "C-INDUCTION"], ["E-BASE", "E-STEP", "E-INDUCTION"], ["T-IND-001"]
        ),
        ReasoningCard(
            "RC-005", 5,
            "Reconstruct the load-bearing algebra independently.",
            "A second implementation should recover the identity without the induction checker output.",
            "Run a separate coefficient normalizer on n^2+2n+1 and (n+1)^2.",
            "The independent coefficient vectors agree exactly.",
            "The evidence declares implementation independence and is replayable.",
            "Attach the reconstruction to the root and pass the release gate.",
            "The theorem reaches MACHINE_VERIFIED with zero certificate debt.",
            ["C-ROOT"], ["E-RECON"], ["T-RECON-001"]
        ),
    ]
    for card in cards:
        engine.add_reasoning_card(card)
    return run


def write_demo(out_dir: str | Path) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    run = build_demo_run()
    run_path = save_run(run, out / "run.json")
    metrics = compute_metrics(run)
    metrics_path = out / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    trace_path = out / "reasoning-trace.jsonl"
    trace_path.write_text(
        "".join(json.dumps(card.__dict__, ensure_ascii=False, sort_keys=True) + "\n" for card in run.reasoning_cards),
        encoding="utf-8",
    )
    calls_path = out / "tool-events.ndjson"
    calls_path.write_text(
        "".join(
            json.dumps({**call.__dict__, "status": call.status.value}, ensure_ascii=False, sort_keys=True) + "\n"
            for call in run.tool_calls
        ),
        encoding="utf-8",
    )
    dashboard_path = out / "dashboard.html"
    dashboard_path.write_text(render_dashboard(run, metrics), encoding="utf-8")
    return {
        "run": run_path,
        "metrics": metrics_path,
        "trace": trace_path,
        "tool_events": calls_path,
        "dashboard": dashboard_path,
    }


def _evidence(
    evidence_id: str,
    kind: EvidenceKind,
    trust: TrustLevel,
    scope: ScopeLevel,
    producer: str,
    payload: dict,
    replay_command: str | None,
    output_digest: str | None,
    independent_of: list[str] | None = None,
) -> EvidenceArtifact:
    return EvidenceArtifact(
        evidence_id=evidence_id,
        kind=kind,
        trust_level=trust,
        scope_level=scope,
        producer=producer,
        payload=payload,
        sha256=digest_json(payload),
        replay_command=replay_command,
        output_digest=output_digest,
        independent_of=independent_of or [],
    )
