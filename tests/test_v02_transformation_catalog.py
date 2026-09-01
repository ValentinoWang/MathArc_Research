from __future__ import annotations

import unittest

from matharc.v02.orchestrator import ResearchOrchestrator
from matharc.v02.schema import (
    ClaimRecord,
    FailureClass,
    FailureRecord,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
)
from matharc.v02.trace import ResearchTrace, TraceValidationError
from matharc.v02.transformation_catalog import (
    TransformationCatalog,
    TransformationCatalogError,
    TransformationSpec,
)


def failed_trace() -> ResearchTrace:
    trace = ResearchTrace(
        "TRANSFORMATION-TEST",
        TheoremContract(
            "TRANSFORMATION-CONTRACT",
            "Prove C.",
            ("C",),
            "The declared test scope.",
        ),
    )
    trace.add_claim(ClaimRecord("C", "C", "test scope"))
    trace.add_route(
        ResearchRoute(
            "R-FAILED",
            "original route",
            "The original hypothesis.",
            ("original mechanism",),
            "find a counterexample to the original route",
            RouteStatus.ACTIVE,
            ("C",),
        )
    )
    trace.record_failure(
        FailureRecord(
            failure_id="F-1",
            claim_id="C",
            route_id="R-FAILED",
            failure_class=FailureClass.SCOPE_OVERREACH,
            trigger="the claimed domain is too broad",
            diagnosis="the witness only supports a narrower scope",
            minimal_witness="n = 1",
            repair="restrict the domain",
            reusable_lesson="check the boundary before globalizing",
        )
    )
    return trace


def scope_catalog() -> TransformationCatalog:
    return TransformationCatalog(
        [
            TransformationSpec(
                transformation_id="T-NARROW",
                applicable_failure_classes=(FailureClass.SCOPE_OVERREACH,),
                directive={"action": "narrow_scope", "instruction": "restrict the domain"},
                structural_requirements=("state the new boundary",),
                provenance=("test-history://scope-overreach-1",),
            )
        ]
    )


class TransformationCatalogTests(unittest.TestCase):
    def test_catalog_requires_known_failure_classes_and_provenance(self) -> None:
        with self.assertRaisesRegex(TransformationCatalogError, "unknown failure class"):
            TransformationSpec(
                "T-UNKNOWN",
                ("NOT_A_FAILURE",),
                {"action": "x"},
                provenance=("history://real",),
            )
        with self.assertRaisesRegex(TransformationCatalogError, "provenance"):
            TransformationSpec(
                "T-NO-PROVENANCE",
                (FailureClass.SCOPE_OVERREACH,),
                {"action": "x"},
                provenance=(),
            )
        with self.assertRaisesRegex(TransformationCatalogError, "FailureRecord"):
            scope_catalog().applicable_to(object())  # type: ignore[arg-type]

    def test_catalog_round_trip_is_strict_and_preserves_one_small_entry(self) -> None:
        catalog = scope_catalog()
        restored = TransformationCatalog.from_dict(catalog.to_dict())
        self.assertEqual(restored.to_dict(), catalog.to_dict())
        self.assertEqual(len(restored), 1)
        with self.assertRaisesRegex(TransformationCatalogError, "unknown transformation fields"):
            TransformationCatalog.from_dict(
                {
                    "transformations": [
                        {
                            **catalog.entries[0].to_dict(),
                            "invented": True,
                        }
                    ]
                }
            )

    def test_planner_emits_directive_only_for_an_applicable_failure(self) -> None:
        trace = failed_trace()
        plan = ResearchOrchestrator(
            trace,
            transformation_catalog=scope_catalog(),
        ).plan_round()
        self.assertEqual(len(plan.transformation_directives), 1)
        directive = plan.transformation_directives[0]
        self.assertEqual(directive["failure_id"], "F-1")
        self.assertEqual(directive["transformation_id"], "T-NARROW")
        self.assertEqual(directive["failed_route_id"], "R-FAILED")

        no_match_catalog = TransformationCatalog(
            [
                TransformationSpec(
                    "T-FALSE",
                    (FailureClass.FALSE_STATEMENT,),
                    {"action": "unrelated"},
                    provenance=("test-history://false-statement-1",),
                )
            ]
        )
        no_match_plan = ResearchOrchestrator(
            failed_trace(),
            transformation_catalog=no_match_catalog,
        ).plan_round()
        self.assertEqual(no_match_plan.transformation_directives, ())

    def test_derived_route_binds_both_ids_and_survives_audit_round_trip(self) -> None:
        trace = failed_trace()
        orchestrator = ResearchOrchestrator(
            trace,
            transformation_catalog=scope_catalog(),
        )
        orchestrator.accept_agent_proposal(
            role="planner",
            payload={
                "public_reasoning": {
                    "objective": "repair the failed route",
                    "premises": ["F-1"],
                    "proposed_move": "restrict the domain",
                    "observation": "the catalog supplies a matching operator",
                    "falsification": "check the new boundary",
                    "decision": "open a derived route",
                },
                "new_routes": [
                    {
                        "route_id": "R-DERIVED",
                        "name": "narrowed route",
                        "hypothesis": "the narrower domain is supported",
                        "mechanism_signature": ("restricted domain",),
                        "kill_test": "test the first excluded boundary value",
                        "claim_ids": ["C"],
                        "derived_from_failure": "F-1",
                        "transformation_id": "T-NARROW",
                    }
                ],
            },
        )
        derived = trace.routes["R-DERIVED"]
        self.assertEqual(derived.derived_from_failure, "F-1")
        self.assertEqual(derived.transformation_id, "T-NARROW")
        self.assertEqual(derived.parent_route_id, "R-FAILED")
        self.assertTrue(trace.audit_transformation_linkage()["valid"])
        restored = ResearchTrace.from_dict(trace.to_dict())
        self.assertEqual(restored.routes["R-DERIVED"].to_dict(), derived.to_dict())
        self.assertTrue(restored.audit_transformation_linkage()["valid"])

    def test_same_mechanism_or_unknown_linkage_is_rejected_individually(self) -> None:
        trace = failed_trace()
        orchestrator = ResearchOrchestrator(trace, transformation_catalog=scope_catalog())
        base_payload = {
            "public_reasoning": {
                "objective": "try a derived route",
                "premises": [],
                "proposed_move": "change the mechanism",
                "observation": "candidate route",
                "falsification": "run its kill test",
                "decision": "keep it proposed",
            },
            "new_routes": [
                {
                    "route_id": "R-SAME",
                    "name": "renamed original",
                    "hypothesis": "same hypothesis",
                    "mechanism_signature": ("original mechanism",),
                    "kill_test": "same kill test",
                    "claim_ids": ["C"],
                    "derived_from_failure": "F-1",
                    "transformation_id": "T-NARROW",
                },
                {
                    "route_id": "R-UNKNOWN",
                    "name": "unknown operator",
                    "hypothesis": "unknown",
                    "mechanism_signature": ("new mechanism",),
                    "kill_test": "test unknown",
                    "claim_ids": ["C"],
                    "derived_from_failure": "F-1",
                    "transformation_id": "T-MISSING",
                },
            ],
        }
        orchestrator.accept_agent_proposal(role="planner", payload=base_payload)
        self.assertNotIn("R-SAME", trace.routes)
        self.assertNotIn("R-UNKNOWN", trace.routes)
        rejected = orchestrator.creation_log[-1]["rejected"]
        self.assertEqual(len(rejected), 2)
        self.assertTrue(all("route" in item["kind"] for item in rejected))


if __name__ == "__main__":
    unittest.main()
