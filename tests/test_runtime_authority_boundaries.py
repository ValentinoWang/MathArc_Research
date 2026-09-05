from __future__ import annotations

import hashlib
import unittest

from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    TheoremContract,
)
from matharc.v02.trace import PromotionError, ResearchTrace, TraceValidationError, runtime_health


def _evidence(*, claim_ids: tuple[str, ...] = ("C",), **overrides: object) -> EvidenceRecord:
    payload: dict[str, object] = {
        "evidence_id": "E",
        "claim_ids": claim_ids,
        "kind": EvidenceKind.CHECKED_DERIVATION,
        "status": EvidenceStatus.ACCEPTED,
        "summary": "independently checked derivation",
        "artifact_uri": "memory://evidence/E",
        "digest_sha256": hashlib.sha256(b"evidence").hexdigest(),
        "producer": "source-checker",
        "verifier": "independent-evaluator",
        "independence_group": "checker-A",
        "statement_correspondence": "Exactly checks claim C.",
    }
    payload.update(overrides)
    return EvidenceRecord(**payload)


class RuntimeAuthorityBoundaryTests(unittest.TestCase):
    def test_health_snapshot_cannot_mark_a_claim_proved(self) -> None:
        trace = ResearchTrace("trace-1", TheoremContract("K", "p", (), "s"))
        health = runtime_health(trace, runtime_run_id="runtime-1")
        self.assertNotIn("PROVED", health)
        self.assertEqual(trace.claims, {})

    def test_runtime_status_api_rejects_proved(self) -> None:
        trace = ResearchTrace("trace-1", TheoremContract("K", "p", (), "s"))
        with self.assertRaises(TraceValidationError):
            trace.record_runtime_status("PROVED")

    def test_malformed_accepted_evidence_cannot_enter_proof_closure(self) -> None:
        trace = ResearchTrace("trace-2", TheoremContract("K", "p", ("C",), "s"))
        trace.add_claim(ClaimRecord("C", "claim C", "s"))
        with self.assertRaisesRegex(TraceValidationError, "valid SHA-256"):
            trace.add_evidence(_evidence(digest_sha256="forged"))
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)
        self.assertEqual(trace.claims["C"].evidence_ids, ())

    def test_evidence_reference_and_evaluator_binding_are_checked_at_promotion(self) -> None:
        trace = ResearchTrace("trace-3", TheoremContract("K", "p", ("C",), "s"))
        trace.add_claim(ClaimRecord("C", "claim C", "s"))
        trace.add_evidence(_evidence())
        # Simulate a post-ingestion tamper that removes the claim binding.
        trace.evidence["E"].claim_ids = ()
        with self.assertRaisesRegex(PromotionError, "not bound to claim C"):
            trace.promote_claim("C")
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)

    def test_incomplete_source_or_evaluator_cannot_be_accepted(self) -> None:
        for field in ("producer", "verifier", "independence_group", "statement_correspondence"):
            with self.subTest(field=field):
                trace = ResearchTrace("trace-4", TheoremContract("K", "p", ("C",), "s"))
                trace.add_claim(ClaimRecord("C", "claim C", "s"))
                with self.assertRaises(TraceValidationError):
                    trace.add_evidence(_evidence(**{field: ""}))


if __name__ == "__main__":
    unittest.main()
