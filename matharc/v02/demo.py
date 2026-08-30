from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .benchmark import BenchmarkResult, compare_agents
from .failure_memory import FailureMemory
from .metrics import compute_research_metrics
from .schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    FailureClass,
    FailureRecord,
    PublicReasoningStep,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolCallRecord,
    ToolStatus,
)
from .trace import ResearchTrace, save_trace
from .visualization import render_research_dashboard


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_research_demo() -> ResearchTrace:
    contract = TheoremContract(
        contract_id="CONTRACT-ODD-SUM-001",
        problem="Prove that the sum of the first n positive odd integers equals n squared.",
        target_claim_ids=("C-TARGET",),
        scope="For every integer n >= 0.",
        assumptions=("Peano arithmetic for natural numbers",),
        success_criteria=(
            "base and induction-step obligations are independently checked",
            "the target is promoted only through the claim DAG",
        ),
        non_claims=("finite testing alone proves the universal statement",),
    )
    trace = ResearchTrace(run_id="MATHARC-V02-DEMO-ODD-SUM", contract=contract)
    trace.add_claim(
        ClaimRecord(
            claim_id="C-FINITE-LEAP",
            statement="Agreement for n <= 100 is sufficient to prove agreement for every n.",
            scope="Universal extrapolation from a finite prefix.",
            weight=0.4,
            boundary="This is a candidate proof rule, not the target theorem.",
        )
    )
    trace.add_claim(
        ClaimRecord(
            claim_id="C-BASE",
            statement="The identity holds at n = 0.",
            scope="Single base case.",
            weight=1.0,
        )
    )
    trace.add_claim(
        ClaimRecord(
            claim_id="C-STEP",
            statement="If the identity holds at n, then it holds at n + 1.",
            scope="Every natural number n.",
            dependencies=("C-BASE",),
            weight=2.0,
            critical=True,
        )
    )
    trace.add_claim(
        ClaimRecord(
            claim_id="C-TARGET",
            statement="For every n >= 0, 1 + 3 + ... + (2n - 1) = n^2.",
            scope="All natural numbers.",
            dependencies=("C-BASE", "C-STEP"),
            weight=4.0,
            critical=True,
            boundary="No finite-prefix computation is accepted as universal proof.",
        )
    )

    trace.add_route(
        ResearchRoute(
            route_id="R-FINITE-PREFIX",
            name="Finite-prefix extrapolation",
            hypothesis="A large verified prefix may reveal and certify the formula.",
            mechanism_signature=("finite enumeration", "pattern extrapolation"),
            kill_test="Construct two integer-valued expressions agreeing through n=100 but differing at n=101.",
            status=RouteStatus.ACTIVE,
            claim_ids=("C-FINITE-LEAP",),
            expected_discriminator="A concrete n=101 disagreement refutes the proof rule.",
        )
    )
    trace.add_route(
        ResearchRoute(
            route_id="R-INDUCTION",
            name="Induction with symbolic difference certificate",
            hypothesis="The formula follows from a checked base case and a polynomial induction step.",
            mechanism_signature=("mathematical induction", "symbolic polynomial normalization"),
            kill_test="Normalize (n^2 + 2n + 1) - (n+1)^2 and require exact zero.",
            status=RouteStatus.ACTIVE,
            claim_ids=("C-BASE", "C-STEP", "C-TARGET"),
            expected_discriminator="Nonzero normalized polynomial blocks the route.",
        )
    )

    trace.add_tool_call(
        ToolCallRecord(
            call_id="T-FINITE-KILL",
            tool="python-exact-integer-checker",
            purpose="Falsify finite-prefix-to-universal inference.",
            status=ToolStatus.PASS,
            input_digest_sha256=_sha("p=n^2;q=n^2+product(n-k,k=0..100)"),
            output_digest_sha256=_sha("agree-0-100;differ-101"),
            linked_claim_ids=("C-FINITE-LEAP",),
            independence_group="finite-counterexample-generator",
            replay_command="python examples/research_trace_v02.py --check finite-leap",
            started_at="2026-08-25T00:00:00+00:00",
            ended_at="2026-08-25T00:00:01+00:00",
            exit_code=0,
            environment_digest_sha256=_sha("python-3.12-stdlib"),
            expected_discriminator="the two expressions differ at n=101",
        )
    )
    trace.add_evidence(
        EvidenceRecord(
            evidence_id="E-FINITE-COUNTEREXAMPLE",
            claim_ids=("C-FINITE-LEAP",),
            kind=EvidenceKind.COUNTEREXAMPLE,
            status=EvidenceStatus.ACCEPTED,
            summary="Two integer-valued expressions agree on 0..100 and differ at 101.",
            artifact_uri="artifacts/v02-demo/finite-leap.json",
            digest_sha256=_sha("agree-0-100;differ-101"),
            producer="finite-counterexample-generator",
            verifier="direct-substitution-audit",
            independence_group="finite-counterexample-generator",
            replay_command="python examples/research_trace_v02.py --check finite-leap",
            statement_correspondence="Directly negates the sufficiency claim C-FINITE-LEAP.",
        )
    )
    trace.add_public_reasoning(
        PublicReasoningStep(
            step_id="STEP-001",
            role="falsifier",
            objective="Test whether finite agreement can carry the universal quantifier.",
            premises=("The proposed route checks only n <= 100.",),
            proposed_move="Construct a polynomial perturbation vanishing on the checked prefix.",
            observation="The perturbation vanishes on 0..100 but not at 101.",
            falsification_test="Evaluate the pair at every checked n and at n=101.",
            decision="Reject finite-prefix extrapolation as a proof rule.",
            linked_claim_ids=("C-FINITE-LEAP",),
            linked_route_ids=("R-FINITE-PREFIX",),
            linked_tool_call_ids=("T-FINITE-KILL",),
            confidence=1.0,
        )
    )
    trace.record_failure(
        FailureRecord(
            failure_id="F-FINITE-TO-GLOBAL",
            claim_id="C-FINITE-LEAP",
            route_id="R-FINITE-PREFIX",
            failure_class=FailureClass.FINITE_TO_GLOBAL,
            trigger="The route attempted to replace a universal quantifier by finite testing.",
            diagnosis="Finite agreement does not control untested natural numbers.",
            minimal_witness="q(n)=n^2+product_{k=0}^{100}(n-k) agrees with p(n)=n^2 on 0..100 and differs at 101.",
            repair="Replace extrapolation by an induction step valid for arbitrary n.",
            reusable_lesson="Before promoting a computational pattern, isolate and discharge the missing universal quantifier.",
            evidence_ids=("E-FINITE-COUNTEREXAMPLE",),
            exact=True,
        )
    )

    trace.add_tool_call(
        ToolCallRecord(
            call_id="T-BASE",
            tool="integer-equality-checker",
            purpose="Check the induction base exactly.",
            status=ToolStatus.PASS,
            input_digest_sha256=_sha("sum-empty=0;0^2=0"),
            output_digest_sha256=_sha("0=0"),
            linked_claim_ids=("C-BASE",),
            independence_group="base-case-checker",
            replay_command="python examples/research_trace_v02.py --check base",
            started_at="2026-08-25T00:01:00+00:00",
            ended_at="2026-08-25T00:01:00+00:00",
            exit_code=0,
            environment_digest_sha256=_sha("python-3.12-stdlib"),
            expected_discriminator="both sides equal zero",
        )
    )
    trace.add_evidence(
        EvidenceRecord(
            evidence_id="E-BASE",
            claim_ids=("C-BASE",),
            kind=EvidenceKind.EXACT_COMPUTATION,
            status=EvidenceStatus.ACCEPTED,
            summary="Both sides are zero at n=0.",
            artifact_uri="artifacts/v02-demo/base.json",
            digest_sha256=_sha("0=0"),
            producer="integer-equality-checker",
            verifier="base-case-replay",
            independence_group="base-case-checker",
            replay_command="python examples/research_trace_v02.py --check base",
            statement_correspondence="Exactly checks C-BASE at its only quantified input.",
        )
    )
    trace.promote_claim("C-BASE")

    trace.add_tool_call(
        ToolCallRecord(
            call_id="T-STEP-SYMBOLIC",
            tool="polynomial-normalizer-a",
            purpose="Normalize the induction-step residual.",
            status=ToolStatus.PASS,
            input_digest_sha256=_sha("n^2+(2n+1)-(n+1)^2"),
            output_digest_sha256=_sha("0-polynomial"),
            linked_claim_ids=("C-STEP",),
            independence_group="symbolic-normalizer-a",
            replay_command="python examples/research_trace_v02.py --check step-a",
            started_at="2026-08-25T00:02:00+00:00",
            ended_at="2026-08-25T00:02:01+00:00",
            exit_code=0,
            environment_digest_sha256=_sha("python-3.12-stdlib-normalizer-a"),
            expected_discriminator="the residual normal form is zero",
        )
    )
    trace.add_tool_call(
        ToolCallRecord(
            call_id="T-STEP-INDEPENDENT",
            tool="coefficient-audit-b",
            purpose="Independently expand and compare coefficients.",
            status=ToolStatus.PASS,
            input_digest_sha256=_sha("left=n^2+2n+1;right=(n+1)^2"),
            output_digest_sha256=_sha("coefficients:[1,2,1]"),
            linked_claim_ids=("C-STEP",),
            independence_group="coefficient-audit-b",
            replay_command="python examples/research_trace_v02.py --check step-b",
            started_at="2026-08-25T00:02:02+00:00",
            ended_at="2026-08-25T00:02:03+00:00",
            exit_code=0,
            environment_digest_sha256=_sha("python-3.12-stdlib-coefficient-audit"),
            expected_discriminator="coefficient vectors agree exactly",
        )
    )
    for evidence_id, group, digest, command, summary in (
        (
            "E-STEP-A",
            "symbolic-normalizer-a",
            _sha("0-polynomial"),
            "python examples/research_trace_v02.py --check step-a",
            "The induction residual normalizes to the zero polynomial.",
        ),
        (
            "E-STEP-B",
            "coefficient-audit-b",
            _sha("coefficients:[1,2,1]"),
            "python examples/research_trace_v02.py --check step-b",
            "An independent implementation matches all polynomial coefficients.",
        ),
    ):
        trace.add_evidence(
            EvidenceRecord(
                evidence_id=evidence_id,
                claim_ids=("C-STEP",),
                kind=EvidenceKind.EXACT_CERTIFICATE,
                status=EvidenceStatus.ACCEPTED,
                summary=summary,
                artifact_uri=f"artifacts/v02-demo/{evidence_id.lower()}.json",
                digest_sha256=digest,
                producer=group,
                verifier=f"{group}-cold-replay",
                independence_group=group,
                replay_command=command,
                statement_correspondence="Checks the polynomial identity required by C-STEP for arbitrary symbolic n.",
                assumptions_checked=("induction hypothesis supplies n^2 for the first n odd integers",),
            )
        )
    trace.add_public_reasoning(
        PublicReasoningStep(
            step_id="STEP-002",
            role="prover",
            objective="Close the arbitrary-n induction step.",
            premises=("C-BASE is proved.", "The next odd term is 2n+1."),
            proposed_move="Reduce the step to a polynomial identity and check it twice.",
            observation="Both independent normalizers return the zero residual.",
            falsification_test="Any nonzero coefficient blocks induction.",
            decision="Promote C-STEP through the verifier gate.",
            linked_claim_ids=("C-STEP",),
            linked_route_ids=("R-INDUCTION",),
            linked_tool_call_ids=("T-STEP-SYMBOLIC", "T-STEP-INDEPENDENT"),
            confidence=1.0,
        )
    )
    trace.promote_claim("C-STEP")

    for evidence_id, kind, group, command, digest, summary in (
        (
            "E-TARGET-INDUCTION",
            EvidenceKind.FORMAL_PROOF,
            "induction-kernel",
            "python examples/research_trace_v02.py --check induction-certificate",
            _sha("base+step=>forall-n"),
            "A proof kernel applies induction to the accepted base and step nodes.",
        ),
        (
            "E-TARGET-AUDIT",
            EvidenceKind.CHECKED_DERIVATION,
            "manual-dependency-audit",
            "",
            _sha("dependency-audit:C-BASE,C-STEP=>C-TARGET"),
            "An independent dependency audit matches the theorem statement and quantifiers.",
        ),
    ):
        trace.add_evidence(
            EvidenceRecord(
                evidence_id=evidence_id,
                claim_ids=("C-TARGET",),
                kind=kind,
                status=EvidenceStatus.ACCEPTED,
                summary=summary,
                artifact_uri=f"artifacts/v02-demo/{evidence_id.lower()}.json",
                digest_sha256=digest,
                producer=group,
                verifier=f"{group}-verifier",
                independence_group=group,
                replay_command=command,
                statement_correspondence="C-TARGET is exactly the induction closure of C-BASE and C-STEP over all n >= 0.",
                assumptions_checked=("natural-number induction", "universal n in C-STEP"),
            )
        )
    trace.add_public_reasoning(
        PublicReasoningStep(
            step_id="STEP-003",
            role="synthesizer",
            objective="Close the target without exceeding the verified scope.",
            premises=("C-BASE is PROVED.", "C-STEP is PROVED for arbitrary n."),
            proposed_move="Apply induction and independently audit statement correspondence.",
            observation="Both target evidence groups match the same universal statement.",
            falsification_test="Reject if either dependency, quantifier, or statement correspondence differs.",
            decision="Promote C-TARGET; retain C-FINITE-LEAP as an exact failed route.",
            linked_claim_ids=("C-BASE", "C-STEP", "C-TARGET"),
            linked_route_ids=("R-INDUCTION",),
            confidence=1.0,
        )
    )
    trace.promote_claim("C-TARGET")
    trace.routes["R-INDUCTION"].status = RouteStatus.CLOSED
    trace.metadata.update(
        {
            "demo": True,
            "public_reasoning_policy": (
                "Expose concise premises, moves, observations, falsifiers, and decisions; "
                "do not store private token-by-token chain-of-thought."
            ),
        }
    )
    return trace


def _demo_comparison() -> dict[str, Any]:
    candidate: list[BenchmarkResult] = []
    baseline: list[BenchmarkResult] = []
    for seed in range(4):
        candidate.append(
            BenchmarkResult(
                system_name="MathArc Research v0.2",
                suite_id="MATHARC-SMOKE",
                suite_version="0.1",
                case_id=f"case-{seed}",
                seed=seed,
                metrics={"audited_closure": 1.0, "false_promotion_rate": 0.0},
                release_state="PROVED_AND_AUDITED",
                false_promotion=False,
                replay_pass=True,
                budget_units=100.0,
                runtime_seconds=1.0,
                artifact_digest_sha256=_sha(f"candidate-{seed}"),
            )
        )
        baseline.append(
            BenchmarkResult(
                system_name="Illustrative baseline",
                suite_id="MATHARC-SMOKE",
                suite_version="0.1",
                case_id=f"case-{seed}",
                seed=seed,
                metrics={"audited_closure": 0.75, "false_promotion_rate": 0.05},
                release_state="CANDIDATE_UNVERIFIED",
                false_promotion=False,
                replay_pass=True,
                budget_units=100.0,
                runtime_seconds=1.0,
                artifact_digest_sha256=_sha(f"baseline-{seed}"),
            )
        )
    return compare_agents(
        candidate,
        baseline,
        metric_directions={
            "audited_closure": "maximize",
            "false_promotion_rate": "minimize",
        },
        primary_metrics=("audited_closure", "false_promotion_rate"),
        minimum_pairs=30,
        bootstrap_samples=500,
    ).to_dict()


def write_research_demo(out_dir: str | Path) -> dict[str, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    trace = build_research_demo()
    metrics = compute_research_metrics(trace)
    comparison = _demo_comparison()
    memory = FailureMemory()
    memory.ingest_trace(trace)

    paths = {
        "trace": save_trace(trace, target / "research-trace.json"),
        "metrics": target / "research-metrics.json",
        "comparison": target / "benchmark-comparison.json",
        "failure_memory": target / "failure-memory.json",
        "dashboard": target / "research-dashboard.html",
    }
    paths["metrics"].write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths["comparison"].write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    memory.save(paths["failure_memory"])
    render_research_dashboard(trace, paths["dashboard"], comparison=comparison)
    return paths
