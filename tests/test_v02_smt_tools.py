from __future__ import annotations

import importlib.util
import unittest
from unittest.mock import patch

from matharc.v02.campaign import ResearchCampaign
from matharc.v02.exact_tools import (
    ExactToolArgumentError,
    ExactToolUnavailableError,
    default_exact_tool_registry,
)
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolStatus,
)
from matharc.v02.smt_tools import (
    eval_formula,
    smt_existential_witness,
    smt_universal_no_counterexample,
)
from matharc.v02.trace import ResearchTrace
from matharc.v02.workers import StaticProposalWorker

Z3_AVAILABLE = importlib.util.find_spec("z3") is not None


def var(name: str) -> dict[str, object]:
    return {"var": name}


def const(value: int) -> dict[str, object]:
    return {"const": value}


def op(name: str, *args: object) -> dict[str, object]:
    return {"op": name, "args": list(args)}


class IndependentEvaluatorTests(unittest.TestCase):
    """The pure-Python checker must work with or without z3 installed."""

    def test_arithmetic_and_comparisons(self) -> None:
        formula = op("eq", op("add", var("x"), const(3)), const(10))
        self.assertTrue(eval_formula(formula, {"x": 7}))
        self.assertFalse(eval_formula(formula, {"x": 8}))

    def test_boolean_connectives(self) -> None:
        formula = op(
            "implies",
            op("le", const(0), var("x")),
            op("or", op("gt", var("x"), const(-1)), op("eq", var("x"), const(-5))),
        )
        self.assertTrue(eval_formula(formula, {"x": 4}))
        self.assertTrue(eval_formula(formula, {"x": -9}))

    def test_mul_sub_neg(self) -> None:
        formula = op(
            "eq",
            op("sub", op("mul", var("x"), var("x")), op("neg", var("x"))),
            const(12),
        )
        self.assertTrue(eval_formula(formula, {"x": 3}))

    def test_term_where_formula_expected_raises(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            eval_formula(op("add", var("x"), const(1)), {"x": 1})


class ArgumentValidationTests(unittest.TestCase):
    def run_universal(self, arguments: dict[str, object]) -> None:
        smt_universal_no_counterexample(claim_id="C", arguments=arguments)

    def test_missing_variables_rejected(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            self.run_universal({"formula": op("le", var("x"), const(1))})

    def test_undeclared_variable_rejected(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            self.run_universal(
                {"variables": [{"name": "x"}], "formula": op("le", var("y"), const(1))}
            )

    def test_empty_bound_interval_rejected(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            self.run_universal(
                {
                    "variables": [{"name": "x", "lower": 5, "upper": 3}],
                    "formula": op("le", var("x"), const(1)),
                }
            )

    def test_integer_term_as_formula_rejected(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            self.run_universal(
                {"variables": [{"name": "x"}], "formula": op("add", var("x"), const(1))}
            )

    def test_unsupported_op_rejected(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            self.run_universal(
                {"variables": [{"name": "x"}], "formula": op("xor", var("x"), const(1))}
            )

    def test_bad_timeout_rejected(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            self.run_universal(
                {
                    "variables": [{"name": "x", "lower": 0, "upper": 1}],
                    "formula": op("le", var("x"), const(1)),
                    "timeout_ms": 0,
                }
            )


@unittest.skipUnless(Z3_AVAILABLE, "z3-solver is not installed (optional 'formal' extra)")
class SmtUniversalTests(unittest.TestCase):
    def test_bounded_universal_holds_produces_solver_trusted_evidence(self) -> None:
        # For all x in [0, 100]: 2x + 3 <= 203.
        result = smt_universal_no_counterexample(
            claim_id="C",
            arguments={
                "variables": [{"name": "x", "lower": 0, "upper": 100}],
                "formula": op(
                    "le", op("add", op("mul", const(2), var("x")), const(3)), const(203)
                ),
            },
        )
        self.assertEqual(result.tool_call.status, ToolStatus.PASS)
        self.assertIsNotNone(result.evidence)
        assert result.evidence is not None
        self.assertEqual(result.evidence.kind, EvidenceKind.EXACT_COMPUTATION)
        # The unsat verdict is deliberately self-verified: producer == verifier.
        self.assertEqual(result.evidence.producer, result.evidence.verifier)
        self.assertTrue(
            any("solver-internal" in item for item in result.evidence.limitations)
        )
        self.assertTrue(result.tool_call.replayable)

    def test_bounded_universal_fails_with_verified_countermodel_and_no_evidence(self) -> None:
        # For all x in [0, 10]: x <= 5 -- false, countermodel in [6, 10].
        result = smt_universal_no_counterexample(
            claim_id="C",
            arguments={
                "variables": [{"name": "x", "lower": 0, "upper": 10}],
                "formula": op("le", var("x"), const(5)),
            },
        )
        self.assertEqual(result.tool_call.status, ToolStatus.FAIL)
        # A counterexample never enters the supporting-evidence channel.
        self.assertIsNone(result.evidence)

    def test_unknown_is_a_hard_error_with_no_evidence(self) -> None:
        with patch(
            "matharc.v02.smt_tools._run_solver", return_value=("unknown", None)
        ):
            result = smt_universal_no_counterexample(
                claim_id="C",
                arguments={
                    "variables": [{"name": "x", "lower": 0, "upper": 10}],
                    "formula": op("le", var("x"), const(5)),
                },
            )
        self.assertEqual(result.tool_call.status, ToolStatus.ERROR)
        self.assertIsNone(result.evidence)

    def test_checker_disagreement_is_an_error_not_a_result(self) -> None:
        # Force z3 to "return" a model the independent evaluator rejects.
        with patch(
            "matharc.v02.smt_tools._run_solver", return_value=("sat", {"x": 3})
        ):
            result = smt_universal_no_counterexample(
                claim_id="C",
                arguments={
                    "variables": [{"name": "x", "lower": 0, "upper": 10}],
                    "formula": op("le", var("x"), const(5)),
                },
            )
        # x=3 satisfies the formula, so it is NOT a counterexample -- the
        # independent evaluator must veto it and the status must be ERROR.
        self.assertEqual(result.tool_call.status, ToolStatus.ERROR)
        self.assertIsNone(result.evidence)


@unittest.skipUnless(Z3_AVAILABLE, "z3-solver is not installed (optional 'formal' extra)")
class SmtExistentialTests(unittest.TestCase):
    def test_witness_is_independently_verified_and_becomes_exact_certificate(self) -> None:
        result = smt_existential_witness(
            claim_id="C",
            arguments={
                "variables": [{"name": "x", "lower": 0, "upper": 10}],
                "formula": op("eq", var("x"), const(7)),
            },
        )
        self.assertEqual(result.tool_call.status, ToolStatus.PASS)
        assert result.evidence is not None
        self.assertEqual(result.evidence.kind, EvidenceKind.EXACT_CERTIFICATE)
        self.assertNotEqual(result.evidence.producer, result.evidence.verifier)
        self.assertIn("7", result.evidence.summary)

    def test_unsat_existential_is_fail_with_no_evidence(self) -> None:
        result = smt_existential_witness(
            claim_id="C",
            arguments={
                "variables": [{"name": "x", "lower": 0, "upper": 3}],
                "formula": op("eq", var("x"), const(5)),
            },
        )
        self.assertEqual(result.tool_call.status, ToolStatus.FAIL)
        self.assertIsNone(result.evidence)

    def test_nonlinear_witness_within_bounds(self) -> None:
        # x*x = 49 with x in [0, 100]: nonlinear but easy; witness must verify.
        result = smt_existential_witness(
            claim_id="C",
            arguments={
                "variables": [{"name": "x", "lower": 0, "upper": 100}],
                "formula": op("eq", op("mul", var("x"), var("x")), const(49)),
            },
        )
        self.assertEqual(result.tool_call.status, ToolStatus.PASS)
        assert result.evidence is not None


class RegistryAndCampaignIntegrationTests(unittest.TestCase):
    def test_smt_templates_are_registered_by_default(self) -> None:
        registry = default_exact_tool_registry()
        self.assertIn("smt_universal_no_counterexample", registry.template_ids())
        self.assertIn("smt_existential_witness", registry.template_ids())

    def test_missing_z3_reports_unavailable_instead_of_crashing(self) -> None:
        registry = default_exact_tool_registry()
        with patch(
            "matharc.v02.smt_tools._run_solver",
            side_effect=ExactToolUnavailableError("z3-solver is not installed"),
        ):
            with self.assertRaises(ExactToolUnavailableError):
                registry.execute(
                    "smt_universal_no_counterexample",
                    claim_id="C",
                    arguments={
                        "variables": [{"name": "x", "lower": 0, "upper": 1}],
                        "formula": op("le", var("x"), const(1)),
                    },
                )

    @unittest.skipUnless(Z3_AVAILABLE, "z3-solver is not installed (optional 'formal' extra)")
    def test_campaign_promotes_a_bounded_claim_through_the_smt_template(self) -> None:
        contract = TheoremContract(
            contract_id="CONTRACT-SMT-TEST",
            problem="For every x in [0, 100], 2x + 3 <= 203.",
            target_claim_ids=("C-BOUNDED",),
            scope="x in [0, 100] only.",
        )
        trace = ResearchTrace(run_id="SMT-CAMPAIGN-TEST", contract=contract)
        trace.add_claim(
            ClaimRecord(
                "C-BOUNDED",
                "For every x in [0, 100], 2x + 3 <= 203.",
                "x in [0, 100] only.",
                weight=1.0,
            )
        )
        trace.add_route(
            ResearchRoute(
                route_id="R-SMT",
                name="Bounded SMT check",
                hypothesis="The linear bound holds across the whole interval.",
                mechanism_signature=("bounded smt check",),
                kill_test="Ask z3 for a countermodel of the negation within bounds.",
                status=RouteStatus.ACTIVE,
                claim_ids=("C-BOUNDED",),
            )
        )
        proposal = {
            "status": "progress",
            "public_reasoning": {
                "objective": "close the bounded claim",
                "premises": [],
                "proposed_move": "run the bounded SMT check",
                "observation": "the formula is linear and bounded",
                "falsification": "the solver searches for a countermodel",
                "decision": "attach exact evidence",
            },
            "tool_requests": [
                {
                    "tool": "smt_universal_no_counterexample",
                    "purpose": "bounded universal check",
                    "arguments": {
                        "variables": [{"name": "x", "lower": 0, "upper": 100}],
                        "formula": op(
                            "le",
                            op("add", op("mul", const(2), var("x")), const(3)),
                            const(203),
                        ),
                    },
                }
            ],
            "claim_boundary": "the worker never self-promotes",
        }
        worker = StaticProposalWorker("prover", proposal)
        campaign = ResearchCampaign(trace, [worker], max_rounds=2, max_rounds_without_gain=1)
        report = campaign.run()
        self.assertEqual(trace.claims["C-BOUNDED"].status, ClaimStatus.PROVED)
        executed = report.rounds[0]["workers"][0]["executed_tools"]
        self.assertEqual(executed[0]["status"], "EVIDENCE_ACCEPTED")
        self.assertTrue(executed[0]["promoted"])


if __name__ == "__main__":
    unittest.main()
