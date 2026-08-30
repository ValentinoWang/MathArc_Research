from __future__ import annotations

import tempfile
import unittest
from matharc.v02.trace import ResearchTrace, TraceValidationError
from pathlib import Path

from matharc.publication.claim_map import check_bidirectional_claims, parse_latex_claims
from matharc.publication.gates import audit_publication
from matharc.publication.models import PublicationBundle
from matharc.v02.workspace_demo import write_workspace_demo


class PublicationGateTests(unittest.TestCase):
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
