from __future__ import annotations

import json
import tempfile
import unittest
from matharc.v02.trace import ResearchTrace, TraceValidationError
from pathlib import Path

from scripts.publication_audit_fixture import run_fixture, write_publication_fixture
from matharc.publication.claim_map import check_bidirectional_claims, parse_latex_claims, parse_latex_claims_text
from matharc.publication.gates import audit_publication
from matharc.publication.latex import bibliography_errors, collect_latex_sources
from matharc.publication.models import EvidenceIntegrity, HumanSignoff, HumanSignoffState, PublicationBundle, ScientificClosure, TechnicalPreflight
from matharc.v02.workspace_demo import write_workspace_demo


class PublicationGateTests(unittest.TestCase):
    def test_technical_preflight_fixture_passes_without_optional_dependencies(self) -> None:
        report = run_fixture()
        self.assertTrue(report.valid, report.to_dict())
        self.assertEqual("TECHNICAL_PREFLIGHT_PASS", report.readiness)
        self.assertEqual([], list(report.errors))

    def test_technical_preflight_output_preserves_non_authorizing_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            report = run_fixture(output)
            self.assertTrue(report.valid)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("publication-audit-technical-preflight", payload["fixture_kind"])
            self.assertFalse(payload["authorizes_real_publication"])
            self.assertEqual(report.to_dict(), payload["audit"])

    def test_technical_preflight_fixture_rejects_claim_map_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = write_publication_fixture(directory)
            paths.claim_map.write_text(
                json.dumps({"claims": {"C-TARGET": 1}}) + "\n", encoding="utf-8"
            )
            report = audit_publication(
                paths.workspace,
                paths.bundle,
                latex=paths.latex,
                claim_map=paths.claim_map,
                abstract=paths.abstract,
            )
            self.assertFalse(report.valid)
            self.assertIn("claim C-TARGET revision mismatch", " ".join(report.errors))

    def test_invalid_proved_trace_is_rejected_by_domain_loader(self) -> None:
        payload = {
            "schema_version": "2.0", "run_id": "evil",
            "contract": {"contract_id": "k", "problem": "p", "target_claim_ids": ["C"], "scope": "s"},
            "claims": [{"claim_id": "C", "statement": "false", "scope": "s", "status": "PROVED",
                        "dependencies": ["MISSING"], "evidence_ids": ["E"], "route_ids": []}],
            "routes": [],
            "evidence": [{"evidence_id": "E", "claim_ids": ["C"], "kind": "HEURISTIC", "status": "REJECTED",
                           "summary": "x", "artifact_uri": "x", "digest_sha256": "", "producer": "a",
                           "verifier": "b", "independence_group": "g"}],
            "tool_calls": [], "public_reasoning": [], "failures": [], "boundary_violations": [], "metadata": {},
        }
        with self.assertRaises(TraceValidationError):
            ResearchTrace.from_dict(payload)

    def test_latex_claim_mapping_is_bidirectional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            latex = Path(directory) / "main.tex"
            latex.write_text(r"\begin{theorem}\claimid{C}\claimrevision{2} x\end{theorem}\n", encoding="utf-8")
            self.assertEqual(parse_latex_claims(latex), {"C": 2})
            self.assertEqual(check_bidirectional_claims({"C": 2}, {"C": 2}), [])
            self.assertTrue(check_bidirectional_claims({"C": 3}, {"C": 2}))

    def test_missing_review_path_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_workspace_demo(root)
            bundle = PublicationBundle("paper", 1, {})
            result = audit_publication(root, bundle)
            self.assertFalse(result.valid)
            self.assertIn("LaTeX source", " ".join(result.errors))

    def test_claims_require_pairing_and_reject_duplicates(self) -> None:
        self.assertEqual(parse_latex_claims_text(r"\matharcclaim{A}{3}"), {"A": 3})
        with self.assertRaisesRegex(ValueError, "immediately followed"):
            parse_latex_claims_text(r"\claimid{A} text \claimid{B}\claimrevision{5}")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_latex_claims_text(r"\claimid{A}\claimrevision{1} \claimid{A}\claimrevision{2}")

    def test_bib_without_bbl_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.tex").write_text(r"\documentclass{article}\bibliography{refs}", encoding="utf-8")
            (root / "refs.bib").write_text("@article{x}", encoding="utf-8")
            self.assertTrue(any("no .bbl" in error for error in bibliography_errors(root)))

    def test_latex_inputs_are_recursive_and_cycles_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.tex").write_text(r"\input{sections/a}", encoding="utf-8")
            (root / "sections").mkdir()
            (root / "sections/a.tex").write_text("text", encoding="utf-8")
            self.assertEqual(len(collect_latex_sources(root / "main.tex")), 2)
            (root / "sections/a.tex").write_text(r"\input{../main}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cycle"):
                collect_latex_sources(root / "main.tex")

    def test_readiness_requires_independent_audit_and_signoff(self) -> None:
        bundle = PublicationBundle(
            "paper", 1, {}, scientific_closure=ScientificClosure.CLOSED,
            evidence_integrity=EvidenceIntegrity.REPLAYABLE,
            technical_preflight=TechnicalPreflight.PASS,
            human_signoff=HumanSignoffState.APPROVED,
            human_signoffs=(HumanSignoff("gate", "approve", "reviewer", "2026-01-01", "digest"),),
        )
        self.assertEqual(bundle.readiness, "DRAFT_READY")
        with self.assertRaisesRegex(ValueError, "reviewer"):
            HumanSignoff.from_dict({"gate": "g", "decision": "d", "reviewer": "", "reviewed_at": "t", "artifact_digest": "h", "notes": ""})
