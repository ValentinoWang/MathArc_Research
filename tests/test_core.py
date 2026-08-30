import tempfile
import unittest
from pathlib import Path

from examples.frankl_scope_guard import build as build_frankl_guard
from matharc.demo import build_demo_run, write_demo
from matharc.engine import ResearchEngine
from matharc.metrics import compute_metrics
from matharc.models import ClaimStatus
from matharc.polynomial import PolynomialError, identity_certificate, parse_polynomial
from matharc.store import load_run
from matharc.validator import validate_run


class PolynomialTests(unittest.TestCase):
    def test_exact_identity(self) -> None:
        result = identity_certificate("n**2 + 2*n + 1", "(n+1)**2")
        self.assertTrue(result["valid"])
        self.assertEqual([0], result["difference_coefficients"])

    def test_false_identity(self) -> None:
        result = identity_certificate("(n+1)**2", "n**2+1")
        self.assertFalse(result["valid"])
        self.assertEqual([0, 2], result["difference_coefficients"])

    def test_parser_rejects_code_execution(self) -> None:
        with self.assertRaises(PolynomialError):
            parse_polynomial("__import__('os').system('echo unsafe')")


class DemoTests(unittest.TestCase):
    def test_demo_closes_with_independent_reconstruction(self) -> None:
        run = build_demo_run()
        self.assertEqual("MACHINE_VERIFIED", run.release_state)
        self.assertEqual(ClaimStatus.VERIFIED, run.claims["C-ROOT"].status)
        self.assertEqual(ClaimStatus.REFUTED, run.claims["C-BAD-LEMMA"].status)
        self.assertEqual(ClaimStatus.INVALIDATED, run.claims["C-BAD-ROUTE"].status)
        self.assertEqual([], ResearchEngine(run).certificate_debt())
        self.assertTrue(validate_run(run)["valid"])

    def test_artifact_roundtrip_and_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = write_demo(directory)
            for path in paths.values():
                self.assertTrue(Path(path).exists())
            loaded = load_run(paths["run"])
            self.assertEqual("MACHINE_VERIFIED", loaded.release_state)
            self.assertEqual(1, compute_metrics(loaded)["theorem_closure_binary"])
            self.assertIn("MathArc Research", Path(paths["dashboard"]).read_text())

    def test_metrics_are_bounded_and_not_proof_probability(self) -> None:
        metrics = compute_metrics(build_demo_run())
        self.assertEqual(1, metrics["theorem_closure_binary"])
        self.assertEqual([], metrics["certificate_debt"])
        self.assertGreaterEqual(metrics["portfolio"]["effective_mechanisms"], 3)
        for score in metrics["scores"].values():
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
        self.assertIn("not proof probability", metrics["metric_semantics"])


class ScopeAndFailureTests(unittest.TestCase):
    def test_fixed_parameter_does_not_close_global_frankl(self) -> None:
        run = build_frankl_guard()
        self.assertEqual(ClaimStatus.VERIFIED, run.claims["F-N5"].status)
        self.assertNotEqual(ClaimStatus.VERIFIED, run.claims["F-GLOBAL"].status)
        self.assertEqual("scope-or-trust-gap", run.guard_events[-1].rule)

    def test_refutation_invalidates_descendant(self) -> None:
        run = build_demo_run()
        self.assertEqual(ClaimStatus.REFUTED, run.claims["C-BAD-LEMMA"].status)
        self.assertEqual(ClaimStatus.INVALIDATED, run.claims["C-BAD-ROUTE"].status)
        self.assertEqual(["C-BAD-ROUTE"], run.failures[0].invalidated_claim_ids)


if __name__ == "__main__":
    unittest.main()
