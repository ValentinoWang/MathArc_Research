from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matharc
from matharc.v02 import __version__ as v02_version
from matharc.v02.benchmark import BenchmarkResult, compare_agents
from matharc.v02.demo import build_research_demo, write_research_demo
from matharc.v02.failure_memory import FailureMemory
from matharc.v02.metrics import compute_research_metrics
from matharc.v02.orchestrator import ResearchOrchestrator
from matharc.v02.schema import (
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
)
from matharc.v02.trace import PromotionError, ResearchTrace, TraceValidationError, load_trace, save_trace

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(slots=True)
class Gate:
    gate_id: str
    description: str
    check: Callable[[], dict[str, object]]


def minimal_contract(target: str = "C") -> TheoremContract:
    return TheoremContract("K", "test", (target,), "test scope")


def evidence(evidence_id: str, claim_id: str, group: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim_ids=(claim_id,),
        kind=EvidenceKind.CHECKED_DERIVATION,
        status=EvidenceStatus.ACCEPTED,
        summary="checked",
        artifact_uri=f"artifact://{evidence_id}",
        digest_sha256=sha(evidence_id),
        producer=f"producer-{group}",
        verifier=f"verifier-{group}",
        independence_group=group,
        statement_correspondence=f"checks {claim_id}",
    )


def benchmark_result(system: str, index: int, score: float) -> BenchmarkResult:
    return BenchmarkResult(
        system_name=system,
        suite_id="SMOKE",
        suite_version="1",
        case_id=f"case-{index}",
        seed=index,
        metrics={"audited_closure": score},
        release_state="PROVED_AND_AUDITED" if score == 1 else "BLOCKED_EXACT",
        false_promotion=False,
        replay_pass=True,
        budget_units=100,
        runtime_seconds=1,
        artifact_digest_sha256=sha(f"{system}-{index}"),
    )


def gate_version() -> dict[str, object]:
    assert v02_version == "0.2.0"
    assert hasattr(matharc, "ResearchEngine")
    return {"v02_version": v02_version, "v01_api_present": True}


def gate_demo_valid() -> dict[str, object]:
    trace = build_research_demo()
    validation = trace.validate()
    assert validation["valid"], validation
    assert not validation["warnings"], validation
    return validation


def gate_target_and_failed_route() -> dict[str, object]:
    trace = build_research_demo()
    assert trace.claims["C-TARGET"].status is ClaimStatus.PROVED
    assert trace.claims["C-FINITE-LEAP"].status is ClaimStatus.REFUTED
    assert trace.routes["R-FINITE-PREFIX"].status is RouteStatus.FALSIFIED
    return {
        "target": trace.claims["C-TARGET"].status.value,
        "failed_claim": trace.claims["C-FINITE-LEAP"].status.value,
        "failed_route": trace.routes["R-FINITE-PREFIX"].status.value,
    }


def gate_dependency_guard() -> dict[str, object]:
    trace = ResearchTrace("R", minimal_contract("B"))
    trace.add_claim(ClaimRecord("A", "A", "scope"))
    trace.add_claim(ClaimRecord("B", "B", "scope", dependencies=("A",)))
    trace.add_evidence(evidence("EB", "B", "g"))
    try:
        trace.promote_claim("B")
    except PromotionError as exc:
        assert "unproved dependencies" in str(exc)
    else:
        raise AssertionError("promotion unexpectedly passed")
    return {"boundary_violations": len(trace.boundary_violations)}


def gate_independent_evidence() -> dict[str, object]:
    trace = ResearchTrace("R", minimal_contract())
    trace.add_claim(ClaimRecord("C", "C", "scope", critical=True))
    trace.add_evidence(evidence("E1", "C", "same"))
    trace.add_evidence(evidence("E2", "C", "same"))
    try:
        trace.promote_claim("C")
    except PromotionError:
        pass
    else:
        raise AssertionError("same-group evidence unexpectedly passed")
    trace.add_evidence(evidence("E3", "C", "independent"))
    trace.promote_claim("C")
    return {"status": trace.claims["C"].status.value, "groups": 2}


def gate_failure_cascade() -> dict[str, object]:
    trace = ResearchTrace("R", minimal_contract("C"))
    trace.add_claim(ClaimRecord("A", "A", "scope"))
    trace.add_claim(ClaimRecord("B", "B", "scope", dependencies=("A",)))
    trace.add_claim(ClaimRecord("C", "C", "scope", dependencies=("B",)))
    trace.add_route(ResearchRoute("R1", "route", "h", ("m",), "kill", RouteStatus.ACTIVE, ("A",)))
    record = trace.record_failure(
        FailureRecord(
            "F1",
            "A",
            "R1",
            FailureClass.FALSE_STATEMENT,
            "witness",
            "A is false",
            "minimal witness",
            "replace A",
            "test the smallest case",
            exact=True,
        )
    )
    assert set(record.invalidated_claim_ids) == {"B", "C"}
    assert trace.claims["C"].status is ClaimStatus.BLOCKED
    return {"invalidated": list(record.invalidated_claim_ids)}


def gate_public_reasoning_policy() -> dict[str, object]:
    payload = {
        "step_id": "S",
        "role": "prover",
        "objective": "x",
        "premises": [],
        "proposed_move": "x",
        "observation": "x",
        "falsification_test": "x",
        "decision": "x",
        "chain_of_thought": "not allowed",
    }
    try:
        PublicReasoningStep.from_dict(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("private chain-of-thought field was accepted")
    trace = build_research_demo()
    assert trace.public_reasoning
    return {"public_steps": len(trace.public_reasoning), "private_fields_accepted": False}


def gate_agent_proposal_only() -> dict[str, object]:
    trace = ResearchTrace("R", minimal_contract())
    trace.add_claim(ClaimRecord("C", "C", "scope"))
    ResearchOrchestrator(trace).accept_agent_proposal(
        role="prover",
        payload={
            "public_reasoning": {
                "objective": "try",
                "premises": [],
                "proposed_move": "derive",
                "observation": "candidate",
                "falsification": "search counterexample",
                "decision": "propose",
            },
            "claim_updates": [{"claim_id": "C", "action": "propose"}],
        },
    )
    assert trace.claims["C"].status is ClaimStatus.CANDIDATE
    return {"status": trace.claims["C"].status.value, "proof_authority": False}


def gate_failure_memory() -> dict[str, object]:
    memory = FailureMemory()
    memory.ingest_trace(build_research_demo())
    matches = memory.query("universal conclusion from a finite checked prefix")
    assert matches
    memory.mark_reused(matches[0].lesson_id)
    metrics = memory.metrics()
    assert metrics["lesson_reuse_rate"] == 1.0
    return metrics


def gate_metrics_semantics() -> dict[str, object]:
    metrics = compute_research_metrics(build_research_demo())
    assert metrics["release_state"] == "PROVED_AND_AUDITED"
    assert metrics["target_logical_closure"] == 1.0
    assert "not probability" in metrics["metric_semantics"]
    assert metrics["marketing_claim_allowed"]
    return {
        "release_state": metrics["release_state"],
        "readiness": metrics["research_readiness_index"],
        "semantics": metrics["metric_semantics"],
    }


def gate_benchmark_guard() -> dict[str, object]:
    candidate = [benchmark_result("candidate", index, 1.0) for index in range(4)]
    baseline = [benchmark_result("baseline", index, 0.5) for index in range(4)]
    comparison = compare_agents(
        candidate,
        baseline,
        metric_directions={"audited_closure": "maximize"},
        primary_metrics=("audited_closure",),
        minimum_pairs=30,
        bootstrap_samples=100,
    )
    assert not comparison.superiority_claim_allowed
    assert comparison.qualification_state == "INSUFFICIENT_EVIDENCE"
    return comparison.to_dict()


def gate_dashboard() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        paths = write_research_demo(directory)
        dashboard = paths["dashboard"].read_text(encoding="utf-8")
        assert "证明依赖图" in dashboard
        assert "公开研究轨迹" in dashboard
        assert "工具调用账本" in dashboard
        size = paths["dashboard"].stat().st_size
    return {"dashboard_bytes": size, "required_panels": 3}


def gate_cold_replay() -> dict[str, object]:
    checks = ("finite-leap", "base", "step-a", "step-b", "induction-certificate")
    outputs = []
    for check in checks:
        completed = subprocess.run(
            [sys.executable, "examples/research_trace_v02.py", "--check", check],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["pass"] is True
        outputs.append(check)
    return {"replayed": outputs}


def gate_serialization() -> dict[str, object]:
    trace = build_research_demo()
    with tempfile.TemporaryDirectory() as directory:
        path = save_trace(trace, Path(directory) / "trace.json")
        loaded = load_trace(path)
    assert loaded.content_digest() == trace.content_digest()
    return {"digest_sha256": trace.content_digest()}


def gate_route_distinctness() -> dict[str, object]:
    trace = ResearchTrace("R", minimal_contract())
    trace.add_claim(ClaimRecord("C", "C", "scope"))
    trace.add_route(ResearchRoute("R1", "one", "h", ("induction", "normal form"), "kill", claim_ids=("C",)))
    try:
        trace.add_route(ResearchRoute("R2", "renamed", "h", ("normal form", "induction"), "kill2", claim_ids=("C",)))
    except TraceValidationError:
        pass
    else:
        raise AssertionError("renamed duplicate route was accepted")
    return {"declared_routes": len(trace.routes), "duplicate_rejected": True}


def main() -> None:
    gates = [
        Gate("G01", "v0.2 version and v0.1 API compatibility", gate_version),
        Gate("G02", "deterministic demo validates with no warning", gate_demo_valid),
        Gate("G03", "target proof and exact failed route coexist", gate_target_and_failed_route),
        Gate("G04", "unproved dependencies block promotion", gate_dependency_guard),
        Gate("G05", "critical claims require independent evidence", gate_independent_evidence),
        Gate("G06", "exact failure propagates through the claim DAG", gate_failure_cascade),
        Gate("G07", "public reasoning schema rejects private chain-of-thought", gate_public_reasoning_policy),
        Gate("G08", "agent output remains proposal-only", gate_agent_proposal_only),
        Gate("G09", "failure memory retrieves and records reuse", gate_failure_memory),
        Gate("G10", "metrics preserve theorem-completion semantics", gate_metrics_semantics),
        Gate("G11", "benchmark layer blocks underpowered superiority claims", gate_benchmark_guard),
        Gate("G12", "dashboard renders all observability panels", gate_dashboard),
        Gate("G13", "all exact demo artifacts cold-replay", gate_cold_replay),
        Gate("G14", "trace serialization is digest-stable", gate_serialization),
        Gate("G15", "route renaming is rejected as diversity", gate_route_distinctness),
    ]
    # Keep the public acceptance contract at fourteen semantic gates by folding
    # route distinctness into the final serialization/integrity gate.
    route_gate = gates.pop()
    original = gates[-1]

    def combined_final_gate() -> dict[str, object]:
        return {"serialization": original.check(), "route_distinctness": route_gate.check()}

    gates[-1] = Gate("G14", "serialization integrity and route distinctness", combined_final_gate)

    records: list[dict[str, object]] = []
    for gate in gates:
        try:
            details = gate.check()
            records.append(
                {
                    "gate_id": gate.gate_id,
                    "description": gate.description,
                    "status": "PASS",
                    "details": details,
                }
            )
        except Exception as exc:  # pragma: no cover - exercised only on acceptance failure
            records.append(
                {
                    "gate_id": gate.gate_id,
                    "description": gate.description,
                    "status": "FAIL",
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
            )

    passed = sum(record["status"] == "PASS" for record in records)
    result = {
        "schema_version": "1.0",
        "release": "MathArc Research v0.2",
        "passed": passed,
        "total": len(records),
        "valid": passed == len(records),
        "gates": records,
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    output = ARTIFACTS / "v0.2-acceptance.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
