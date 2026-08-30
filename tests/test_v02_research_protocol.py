from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

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


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def contract(target: str = "C") -> TheoremContract:
    return TheoremContract(
        contract_id="K",
        problem="test problem",
        target_claim_ids=(target,),
        scope="test scope",
    )


def accepted_evidence(
    evidence_id: str,
    claim_id: str,
    group: str,
    *,
    kind: EvidenceKind = EvidenceKind.CHECKED_DERIVATION,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim_ids=(claim_id,),
        kind=kind,
        status=EvidenceStatus.ACCEPTED,
        summary="checked",
        artifact_uri=f"artifact://{evidence_id}",
        digest_sha256=sha(evidence_id),
        producer=f"producer-{group}",
        verifier=f"verifier-{group}",
        independence_group=group,
        replay_command=("python replay.py" if kind in {EvidenceKind.EXACT_CERTIFICATE, EvidenceKind.EXACT_COMPUTATION, EvidenceKind.FORMAL_PROOF} else ""),
        statement_correspondence=f"exactly checks {claim_id}",
    )


class ResearchProtocolTests(unittest.TestCase):
    def test_deterministic_demo_is_valid_and_target_is_proved(self) -> None:
        trace = build_research_demo()
        validation = trace.validate()
        metrics = compute_research_metrics(trace)
        self.assertTrue(validation["valid"], validation)
        self.assertEqual(trace.claims["C-TARGET"].status, ClaimStatus.PROVED)
        self.assertEqual(trace.claims["C-FINITE-LEAP"].status, ClaimStatus.REFUTED)
        self.assertEqual(metrics["release_state"], "PROVED_AND_AUDITED")
        self.assertEqual(metrics["target_logical_closure"], 1.0)
        self.assertFalse(metrics["validation"]["warnings"])

    def test_private_chain_of_thought_field_is_rejected(self) -> None:
        payload = {
            "step_id": "S",
            "role": "prover",
            "objective": "x",
            "premises": [],
            "proposed_move": "x",
            "observation": "x",
            "falsification_test": "x",
            "decision": "x",
            "chain_of_thought": "private tokens",
        }
        with self.assertRaisesRegex(ValueError, "private token-by-token"):
            PublicReasoningStep.from_dict(payload)

    def test_agent_proposal_has_no_proof_authority(self) -> None:
        trace = ResearchTrace("R", contract())
        trace.add_claim(ClaimRecord("C", "statement", "scope"))
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="prover",
            payload={
                "public_reasoning": {
                    "objective": "try",
                    "premises": [],
                    "proposed_move": "derive",
                    "observation": "looks plausible",
                    "falsification": "seek counterexample",
                    "decision": "candidate only",
                },
                "claim_updates": [
                    {
                        "claim_id": "C",
                        "action": "propose",
                        "statement": "statement",
                        "scope": "scope",
                        "evidence_needed": ["exact proof"],
                    }
                ],
            },
        )
        self.assertEqual(trace.claims["C"].status, ClaimStatus.CANDIDATE)
        self.assertNotEqual(trace.claims["C"].status, ClaimStatus.PROVED)

    def test_unproved_dependency_blocks_promotion(self) -> None:
        trace = ResearchTrace("R", contract("B"))
        trace.add_claim(ClaimRecord("A", "A", "scope"))
        trace.add_claim(ClaimRecord("B", "B", "scope", dependencies=("A",)))
        trace.add_evidence(accepted_evidence("E-B", "B", "g"))
        with self.assertRaisesRegex(PromotionError, "unproved dependencies"):
            trace.promote_claim("B")
        self.assertEqual(len(trace.boundary_violations), 1)

    def test_critical_claim_requires_two_independent_groups(self) -> None:
        trace = ResearchTrace("R", contract())
        trace.add_claim(ClaimRecord("C", "C", "scope", critical=True))
        trace.add_evidence(accepted_evidence("E1", "C", "same"))
        trace.add_evidence(accepted_evidence("E2", "C", "same"))
        with self.assertRaisesRegex(PromotionError, "requires 2"):
            trace.promote_claim("C")
        trace.add_evidence(accepted_evidence("E3", "C", "independent"))
        trace.promote_claim("C")
        self.assertEqual(trace.claims["C"].status, ClaimStatus.PROVED)

    def test_numerical_experiment_cannot_prove_universal_claim(self) -> None:
        trace = ResearchTrace("R", contract())
        trace.add_claim(ClaimRecord("C", "for all n", "all natural numbers"))
        trace.add_evidence(
            accepted_evidence(
                "E",
                "C",
                "enumerator",
                kind=EvidenceKind.NUMERICAL_EXPERIMENT,
            )
        )
        with self.assertRaisesRegex(PromotionError, "no accepted proof-capable evidence"):
            trace.promote_claim("C")

    def test_exact_failure_invalidates_descendants(self) -> None:
        trace = ResearchTrace("R", contract("C"))
        trace.add_claim(ClaimRecord("A", "A", "scope"))
        trace.add_claim(ClaimRecord("B", "B", "scope", dependencies=("A",)))
        trace.add_claim(ClaimRecord("C", "C", "scope", dependencies=("B",)))
        trace.add_route(
            ResearchRoute(
                "ROUTE",
                "route",
                "hypothesis",
                ("mechanism-a",),
                "test A",
                RouteStatus.ACTIVE,
                ("A",),
            )
        )
        trace.record_failure(
            FailureRecord(
                "F",
                "A",
                "ROUTE",
                FailureClass.FALSE_STATEMENT,
                "counterexample",
                "A is false",
                "minimal witness",
                "replace A",
                "test the smallest case first",
                exact=True,
            )
        )
        self.assertEqual(trace.claims["A"].status, ClaimStatus.REFUTED)
        self.assertEqual(trace.claims["B"].status, ClaimStatus.BLOCKED)
        self.assertEqual(trace.claims["C"].status, ClaimStatus.BLOCKED)
        self.assertEqual(set(trace.failures[0].invalidated_claim_ids), {"B", "C"})

    def test_route_renaming_is_not_counted_as_diversity(self) -> None:
        trace = ResearchTrace("R", contract())
        trace.add_claim(ClaimRecord("C", "C", "scope"))
        trace.add_route(
            ResearchRoute("R1", "first", "h", ("normal form", "induction"), "kill", claim_ids=("C",))
        )
        with self.assertRaisesRegex(TraceValidationError, "renaming"):
            trace.add_route(
                ResearchRoute("R2", "renamed", "h2", ("induction", "normal form"), "kill2", claim_ids=("C",))
            )

    def test_failure_memory_retrieves_and_counts_reuse(self) -> None:
        trace = build_research_demo()
        memory = FailureMemory()
        self.assertEqual(memory.ingest_trace(trace), 1)
        matches = memory.query("infer a universal theorem from finitely many checked values")
        self.assertTrue(matches)
        memory.mark_reused(matches[0].lesson_id)
        metrics = memory.metrics()
        self.assertEqual(metrics["lesson_count"], 1)
        self.assertEqual(metrics["lesson_reuse_rate"], 1.0)

    def test_round_planner_selects_a_load_bearing_open_claim(self) -> None:
        trace = ResearchTrace("R", contract("T"))
        trace.add_claim(ClaimRecord("L", "lemma", "scope", weight=1.0, critical=True))
        trace.add_claim(ClaimRecord("T", "target", "scope", dependencies=("L",), weight=3.0, critical=True))
        trace.add_route(
            ResearchRoute("RL", "lemma route", "h", ("obstruction",), "small counterexample", RouteStatus.ACTIVE, ("L",))
        )
        plan = ResearchOrchestrator(trace).plan_round()
        self.assertEqual(plan.focus_claim_id, "L")
        self.assertTrue(plan.acceptance_gate)
        self.assertIn("verifier-gated", plan.public_summary)

    def test_save_load_round_trip_preserves_digest(self) -> None:
        trace = build_research_demo()
        with tempfile.TemporaryDirectory() as directory:
            path = save_trace(trace, Path(directory) / "trace.json")
            loaded = load_trace(path)
        self.assertEqual(trace.content_digest(), loaded.content_digest())

    def test_dashboard_and_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = write_research_demo(directory)
            for path in paths.values():
                self.assertTrue(path.is_file(), path)
            html = paths["dashboard"].read_text(encoding="utf-8")
            self.assertIn("证明依赖图", html)
            self.assertIn("公开研究轨迹", html)
            comparison = json.loads(paths["comparison"].read_text(encoding="utf-8"))
            self.assertFalse(comparison["superiority_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
