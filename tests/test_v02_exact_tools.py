from __future__ import annotations

import unittest

from matharc.v02.exact_tools import (
    ExactToolArgumentError,
    UnknownExactToolError,
    default_exact_tool_registry,
)
from matharc.v02.schema import EvidenceKind, EvidenceStatus, ToolStatus


class ExactToolRegistryTests(unittest.TestCase):
    def test_unknown_template_is_rejected(self) -> None:
        registry = default_exact_tool_registry()
        with self.assertRaises(UnknownExactToolError):
            registry.execute("not-a-real-tool", claim_id="C", arguments={})

    def test_polynomial_identity_pass(self) -> None:
        registry = default_exact_tool_registry()
        result = registry.execute(
            "polynomial_identity",
            claim_id="C",
            arguments={"lhs": "(n+1)*(n+1)", "rhs": "n*n + 2*n + 1"},
        )
        self.assertEqual(result.tool_call.status, ToolStatus.PASS)
        self.assertIsNotNone(result.evidence)
        assert result.evidence is not None
        self.assertEqual(result.evidence.kind, EvidenceKind.EXACT_CERTIFICATE)
        self.assertEqual(result.evidence.status, EvidenceStatus.ACCEPTED)
        self.assertTrue(result.tool_call.replayable)
        self.assertTrue(result.evidence.replayable)

    def test_polynomial_identity_fail_produces_no_evidence(self) -> None:
        registry = default_exact_tool_registry()
        result = registry.execute(
            "polynomial_identity",
            claim_id="C",
            arguments={"lhs": "n*n", "rhs": "n*n + 1"},
        )
        self.assertEqual(result.tool_call.status, ToolStatus.FAIL)
        self.assertIsNone(result.evidence)

    def test_polynomial_identity_missing_argument_raises(self) -> None:
        registry = default_exact_tool_registry()
        with self.assertRaises(ExactToolArgumentError):
            registry.execute("polynomial_identity", claim_id="C", arguments={"lhs": "n"})

    def test_induction_certificate_pass_for_odd_sum(self) -> None:
        registry = default_exact_tool_registry()
        certificate = {
            "variable": "n",
            "base": {"at": 0, "lhs": "0", "rhs": "0*0"},
            "step": {"lhs": "(n*n) + (2*(n+1) - 1)", "rhs": "(n+1)*(n+1)"},
        }
        result = registry.execute(
            "induction_certificate",
            claim_id="C-STEP",
            arguments={"certificate": certificate},
        )
        self.assertEqual(result.tool_call.status, ToolStatus.PASS)
        self.assertIsNotNone(result.evidence)

    def test_induction_certificate_fail_when_step_is_wrong(self) -> None:
        registry = default_exact_tool_registry()
        certificate = {
            "variable": "n",
            "base": {"at": 0, "lhs": "0", "rhs": "0*0"},
            "step": {"lhs": "n*n", "rhs": "n*n + 1"},
        }
        result = registry.execute(
            "induction_certificate",
            claim_id="C-STEP",
            arguments={"certificate": certificate},
        )
        self.assertEqual(result.tool_call.status, ToolStatus.FAIL)
        self.assertIsNone(result.evidence)

    def test_induction_certificate_malformed_raises(self) -> None:
        registry = default_exact_tool_registry()
        with self.assertRaises(ExactToolArgumentError):
            registry.execute(
                "induction_certificate",
                claim_id="C",
                arguments={"certificate": {"base": {}}},
            )

    def test_two_calls_to_the_same_template_share_an_independence_group(self) -> None:
        # Same underlying implementation run twice is NOT independent evidence
        # -- this is intentional: it documents why a critical claim cannot
        # reach PROVED from this single exact-tool family alone.
        registry = default_exact_tool_registry()
        first = registry.execute(
            "polynomial_identity", claim_id="C", arguments={"lhs": "n", "rhs": "n"}
        )
        second = registry.execute(
            "polynomial_identity", claim_id="C", arguments={"lhs": "n+1", "rhs": "1+n"}
        )
        assert first.evidence is not None and second.evidence is not None
        self.assertEqual(first.evidence.independence_group, second.evidence.independence_group)


if __name__ == "__main__":
    unittest.main()
