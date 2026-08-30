from __future__ import annotations

import unittest

from matharc.v02.orchestrator import (
    MAX_NEW_CLAIMS_PER_PROPOSAL,
    MAX_NEW_ROUTES_PER_PROPOSAL,
    ResearchOrchestrator,
)
from matharc.v02.schema import ClaimStatus, RouteStatus, TheoremContract
from matharc.v02.trace import ResearchTrace


def base_reasoning() -> dict[str, object]:
    return {
        "objective": "decompose",
        "premises": [],
        "proposed_move": "split into sub-claims",
        "observation": "structure identified",
        "falsification": "check smallest instance",
        "decision": "propose sub-structure",
    }


def trace_with_root_claim() -> ResearchTrace:
    trace = ResearchTrace("CREATE-TEST", TheoremContract("K", "prove C", ("C",), "test scope"))
    from matharc.v02.schema import ClaimRecord

    trace.add_claim(ClaimRecord("C", "root statement", "test scope"))
    return trace


class GovernedClaimCreationTests(unittest.TestCase):
    def test_worker_can_create_a_new_claim_as_proposed(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={
                "public_reasoning": base_reasoning(),
                "new_claims": [
                    {"claim_id": "C-SUB", "statement": "a sub-lemma", "scope": "narrower scope"}
                ],
            },
        )
        self.assertIn("C-SUB", trace.claims)
        self.assertEqual(trace.claims["C-SUB"].status, ClaimStatus.PROPOSED)
        self.assertEqual(trace.claims["C-SUB"].owner, "agent:strategist")
        self.assertEqual(orchestrator.creation_log[-1]["created_claim_ids"], ("C-SUB",))

    def test_created_claim_can_depend_on_an_existing_claim(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={
                "public_reasoning": base_reasoning(),
                "new_claims": [
                    {
                        "claim_id": "C-SUB",
                        "statement": "a sub-lemma",
                        "scope": "narrower scope",
                        "dependencies": ["C"],
                    }
                ],
            },
        )
        self.assertEqual(trace.claims["C-SUB"].dependencies, ("C",))

    def test_a_worker_can_never_set_a_status_other_than_proposed(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="prover",
            payload={
                "public_reasoning": base_reasoning(),
                # A malicious/careless worker attempts to inject a status --
                # the schema forced onto real workers has no such field, but
                # the orchestrator must not honor one even if present.
                "new_claims": [
                    {
                        "claim_id": "C-SNEAKY",
                        "statement": "x",
                        "scope": "y",
                        "status": "PROVED",
                    }
                ],
            },
        )
        self.assertEqual(trace.claims["C-SNEAKY"].status, ClaimStatus.PROPOSED)

    def test_undeclared_dependency_is_rejected_without_crashing_the_batch(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={
                "public_reasoning": base_reasoning(),
                "new_claims": [
                    {
                        "claim_id": "C-BAD",
                        "statement": "x",
                        "scope": "y",
                        "dependencies": ["C-DOES-NOT-EXIST"],
                    },
                    {"claim_id": "C-GOOD", "statement": "x", "scope": "y"},
                ],
            },
        )
        self.assertNotIn("C-BAD", trace.claims)
        self.assertIn("C-GOOD", trace.claims)
        rejected = orchestrator.creation_log[-1]["rejected"]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["kind"], "claim")

    def test_duplicate_claim_id_is_rejected(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={
                "public_reasoning": base_reasoning(),
                "new_claims": [{"claim_id": "C", "statement": "x", "scope": "y"}],
            },
        )
        self.assertEqual(trace.claims["C"].statement, "root statement")
        self.assertEqual(len(orchestrator.creation_log[-1]["rejected"]), 1)

    def test_malformed_claim_spec_is_rejected_not_raised(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        # No exception should propagate even though "statement" is missing.
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={
                "public_reasoning": base_reasoning(),
                "new_claims": [{"claim_id": "C-MISSING", "scope": "y"}],
            },
        )
        self.assertNotIn("C-MISSING", trace.claims)

    def test_per_proposal_cap_is_enforced(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        many_claims = [
            {"claim_id": f"C-{index}", "statement": "x", "scope": "y"}
            for index in range(MAX_NEW_CLAIMS_PER_PROPOSAL + 3)
        ]
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={"public_reasoning": base_reasoning(), "new_claims": many_claims},
        )
        created = [claim_id for claim_id in trace.claims if claim_id.startswith("C-") and claim_id != "C"]
        self.assertLessEqual(len(created), MAX_NEW_CLAIMS_PER_PROPOSAL)
        reasons = [item["reason"] for item in orchestrator.creation_log[-1]["rejected"]]
        self.assertTrue(any("cap exceeded" in reason for reason in reasons))


class GovernedRouteCreationTests(unittest.TestCase):
    def test_worker_can_create_a_new_route_as_proposed(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={
                "public_reasoning": base_reasoning(),
                "new_routes": [
                    {
                        "route_id": "R-NEW",
                        "name": "a new mechanism",
                        "hypothesis": "try a distinct invariant",
                        "mechanism_signature": ["new invariant"],
                        "kill_test": "search the smallest counterexample",
                        "claim_ids": ["C"],
                    }
                ],
            },
        )
        self.assertIn("R-NEW", trace.routes)
        self.assertEqual(trace.routes["R-NEW"].status, RouteStatus.PROPOSED)
        self.assertIn("R-NEW", trace.claims["C"].route_ids)

    def test_route_referencing_unknown_claim_is_rejected(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={
                "public_reasoning": base_reasoning(),
                "new_routes": [
                    {
                        "route_id": "R-BAD",
                        "name": "n",
                        "hypothesis": "h",
                        "mechanism_signature": ["m"],
                        "kill_test": "k",
                        "claim_ids": ["C-DOES-NOT-EXIST"],
                    }
                ],
            },
        )
        self.assertNotIn("R-BAD", trace.routes)

    def test_route_cap_is_enforced(self) -> None:
        trace = trace_with_root_claim()
        orchestrator = ResearchOrchestrator(trace)
        many_routes = [
            {
                "route_id": f"R-{index}",
                "name": "n",
                "hypothesis": "h",
                "mechanism_signature": [f"mechanism-{index}"],
                "kill_test": "k",
            }
            for index in range(MAX_NEW_ROUTES_PER_PROPOSAL + 2)
        ]
        orchestrator.accept_agent_proposal(
            role="strategist",
            payload={"public_reasoning": base_reasoning(), "new_routes": many_routes},
        )
        self.assertLessEqual(len(trace.routes), MAX_NEW_ROUTES_PER_PROPOSAL)


if __name__ == "__main__":
    unittest.main()
