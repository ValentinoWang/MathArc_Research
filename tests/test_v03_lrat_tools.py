from __future__ import annotations

import base64
import json
import unittest
from unittest.mock import patch

from matharc.v02.exact_tools import ExactToolArgumentError, default_exact_tool_registry
from matharc.v02.lrat_checker import LratCheckError, check_lrat_proof
from matharc.v02.lrat_tools import build_cnf_lrat_artifact, cnf_lrat_unsat
from matharc.v02.schema import EvidenceKind, ToolStatus, canonical_json, digest_json


class LratCheckerTests(unittest.TestCase):
    def test_accepts_explicit_rup_refutation(self) -> None:
        report = check_lrat_proof(
            num_variables=2,
            clauses=((1, 2), (-1,), (-2,)),
            proof_text="4 2 0 1 2 0\n5 0 3 4 0\n",
        )
        self.assertTrue(report["valid"])
        self.assertEqual(report["empty_clause_id"], 5)

    def test_rejects_tampered_hint_chain(self) -> None:
        with self.assertRaises(LratCheckError):
            check_lrat_proof(
                num_variables=2,
                clauses=((1, 2), (-1,), (-2,)),
                proof_text="4 2 0 1 3 0\n5 0 3 4 0\n",
            )

    def test_rejects_hint_after_conflict(self) -> None:
        with self.assertRaises(LratCheckError):
            check_lrat_proof(
                num_variables=2,
                clauses=((1, 2), (-1,), (-2,)),
                proof_text="4 2 0 1 2 999 0\n5 0 3 4 0\n",
            )

    def test_rejects_proof_without_empty_clause(self) -> None:
        with self.assertRaisesRegex(LratCheckError, "empty clause"):
            check_lrat_proof(
                num_variables=2,
                clauses=((1, 2), (-1,)),
                proof_text="3 2 0 1 2 0\n",
            )


class CnfLratToolTests(unittest.TestCase):
    def test_unsat_cnf_produces_embedded_independently_checked_artifact(self) -> None:
        arguments = {
            "num_variables": 2,
            "clauses": [[1, 2], [-1], [-2]],
        }
        result = cnf_lrat_unsat(claim_id="C-CNF", arguments=arguments)
        self.assertEqual(result.tool_call.status, ToolStatus.PASS)
        assert result.evidence is not None
        self.assertEqual(result.evidence.kind, EvidenceKind.EXACT_CERTIFICATE)
        self.assertNotEqual(result.evidence.producer, result.evidence.verifier)
        prefix, encoded = result.evidence.artifact_uri.split(",", 1)
        self.assertEqual(prefix, "data:application/vnd.matharc.cnf-lrat+json;base64")
        artifact = json.loads(base64.b64decode(encoded).decode("utf-8"))
        self.assertTrue(artifact["checker"]["valid"])
        self.assertEqual(digest_json(artifact), result.evidence.digest_sha256)
        self.assertEqual(canonical_json(artifact), canonical_json(build_cnf_lrat_artifact(arguments)))

    def test_satisfiable_cnf_cannot_create_unsat_evidence(self) -> None:
        result = cnf_lrat_unsat(
            claim_id="C-SAT",
            arguments={"num_variables": 2, "clauses": [[1, 2], [-1, 2]]},
        )
        self.assertEqual(result.tool_call.status, ToolStatus.FAIL)
        self.assertIsNone(result.evidence)

    def test_resource_limit_is_error_without_evidence(self) -> None:
        result = cnf_lrat_unsat(
            claim_id="C-LIMIT",
            arguments={
                "num_variables": 2,
                "clauses": [[1, 2], [-1], [-2]],
                "max_derived_clauses": 1,
            },
        )
        self.assertEqual(result.tool_call.status, ToolStatus.ERROR)
        self.assertIsNone(result.evidence)

    def test_resolution_pair_limit_is_error_without_evidence(self) -> None:
        result = cnf_lrat_unsat(
            claim_id="C-PAIR-LIMIT",
            arguments={
                "num_variables": 2,
                "clauses": [[1, 2], [-1], [-2]],
                "max_resolution_pairs": 1,
            },
        )
        self.assertEqual(result.tool_call.status, ToolStatus.ERROR)
        self.assertIsNone(result.evidence)

    def test_checker_disagreement_is_error_without_evidence(self) -> None:
        with patch(
            "matharc.v02.lrat_tools.check_lrat_proof",
            side_effect=LratCheckError("independent checker rejected proof"),
        ):
            result = cnf_lrat_unsat(
                claim_id="C-DISAGREE",
                arguments={"num_variables": 1, "clauses": [[1], [-1]]},
            )
        self.assertEqual(result.tool_call.status, ToolStatus.ERROR)
        self.assertIsNone(result.evidence)

    def test_malformed_cnf_is_rejected(self) -> None:
        with self.assertRaises(ExactToolArgumentError):
            cnf_lrat_unsat(
                claim_id="C-BAD",
                arguments={"num_variables": 1, "clauses": [[1, -1]]},
            )

    def test_cnf_clause_order_is_canonicalized(self) -> None:
        first = build_cnf_lrat_artifact(
            {"num_variables": 2, "clauses": [[1, 2], [-1], [-2]]}
        )
        second = build_cnf_lrat_artifact(
            {"num_variables": 2, "clauses": [[-2], [2, 1], [-1]]}
        )
        self.assertEqual(canonical_json(first), canonical_json(second))

    def test_template_is_registered_without_changing_z3_semantics(self) -> None:
        registry = default_exact_tool_registry()
        self.assertIn("cnf_lrat_unsat", registry.template_ids())
        self.assertIn("smt_universal_no_counterexample", registry.template_ids())


if __name__ == "__main__":
    unittest.main()
