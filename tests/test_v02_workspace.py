from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.artifact_store import ArtifactStore
from matharc.v02.event_log import EventLedger
from matharc.v02.object_registry import (
    MathematicalObject,
    ObjectKind,
    ObjectRegistry,
    ObjectStatus,
)
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
)
from matharc.v02.source_registry import SourceClaim, SourceClaimStatus, SourceKind
from matharc.v02.trace import PromotionError, ResearchTrace
from matharc.v02.workspace import ResearchWorkspace, WorkspaceAuditError


def sha(content: bytes | str) -> str:
    value = content if isinstance(content, bytes) else content.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def empty_trace() -> ResearchTrace:
    return ResearchTrace(
        "WORKSPACE-RUN",
        TheoremContract(
            "CONTRACT",
            "Prove the contracted claim C.",
            ("C",),
            "All natural numbers under the declared axioms.",
        ),
    )


def object_record() -> MathematicalObject:
    return MathematicalObject(
        object_id="OBJ-N",
        symbol="N",
        name="natural numbers",
        kind=ObjectKind.SET,
        definition="The inductively generated set with zero and successor.",
        type_signature="N : Set",
        construction_source="Peano axioms declared in the theorem contract.",
        current_role="Domain of the universal quantifier in C.",
        applicability_boundary="Only the declared natural-number model is used.",
        failure_if_removed="The quantified variable in C has no domain.",
        status=ObjectStatus.DEFINED,
    )


def source_record() -> SourceClaim:
    return SourceClaim(
        source_claim_id="SRC-INDUCTION",
        source_kind=SourceKind.BOOK,
        bibliographic_citation="Pinned foundations text, induction theorem.",
        canonical_uri="urn:matharc:test:induction",
        pinned_version="test-v1",
        locator="Theorem 1",
        claimed_result="Base and successor closure imply the property for every natural number.",
        applicability_conditions=("The property is defined on natural numbers.",),
        linked_claim_ids=("C",),
    )


def evidence_record(evidence_id: str, group: str, content: bytes) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim_ids=("C",),
        kind=EvidenceKind.EXACT_CERTIFICATE,
        status=EvidenceStatus.ACCEPTED,
        summary=f"Exact certificate {evidence_id}.",
        artifact_uri=f"workspace://{evidence_id}",
        digest_sha256=sha(content),
        producer=f"producer-{group}",
        verifier=f"verifier-{group}",
        independence_group=group,
        replay_command=f"python replay.py {evidence_id}",
        statement_correspondence="Exactly checks C under the declared induction premise.",
    )


class WorkspaceTests(unittest.TestCase):
    def build_proved_workspace(self, root: str | Path) -> ResearchWorkspace:
        workspace = ResearchWorkspace(root, empty_trace(), strict_artifacts=True)
        workspace.add_claim(
            ClaimRecord(
                "C",
                "For every natural number n, the contracted property holds.",
                "All n in N.",
                critical=True,
                boundary="Does not assert the property on integers outside N.",
            )
        )
        workspace.add_route(
            ResearchRoute(
                "R-INDUCTION",
                "induction",
                "prove base and successor closure",
                ("mathematical induction", "symbolic normalization"),
                "search for a failing base or successor instance",
                RouteStatus.ACTIVE,
                ("C",),
            )
        )
        workspace.add_object(object_record())
        workspace.verify_object("OBJ-N")
        workspace.link_claim_objects("C", ("OBJ-N",))
        workspace.add_source_claim(source_record())
        workspace.verify_source_claim(
            "SRC-INDUCTION",
            source_digest_sha256=sha("pinned source bytes"),
            verified_by="independent-literature-auditor",
            verification_method="read the pinned theorem and compare hypotheses",
            statement_correspondence="The source theorem supplies exactly the induction rule used by C.",
        )
        workspace.link_claim_sources("C", ("SRC-INDUCTION",))
        workspace.add_evidence(
            evidence_record("E-A", "group-a", b"certificate-a"),
            artifact_content=b"certificate-a",
        )
        workspace.add_evidence(
            evidence_record("E-B", "group-b", b"certificate-b"),
            artifact_content=b"certificate-b",
        )
        workspace.promote_claim("C")
        return workspace

    def test_full_workspace_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.build_proved_workspace(directory)
            report = workspace.audit()
            self.assertTrue(report.valid, report.to_dict())
            self.assertEqual(workspace.trace.claims["C"].status, ClaimStatus.PROVED)
            manifest = workspace.save()
            self.assertTrue(manifest.is_file())
            loaded = ResearchWorkspace.load(directory)
            self.assertEqual(loaded.state_digest(), workspace.state_digest())
            self.assertEqual(loaded.events.head_hash, workspace.events.head_hash)
            self.assertTrue(loaded.audit().valid)

    def test_direct_mutation_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, empty_trace())
            workspace.trace.metadata["unsealed"] = True
            report = workspace.audit()
            self.assertFalse(report.valid)
            self.assertTrue(
                any("last sealed event" in issue.message for issue in report.issues)
            )
            with self.assertRaisesRegex(WorkspaceAuditError, "unsealed direct mutation"):
                workspace.add_claim(ClaimRecord("C", "C", "scope"))

    def test_event_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, empty_trace())
            payload = workspace.events.to_dict()
            payload["events"][0]["payload"]["details"]["schema_version"] = "tampered"
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                EventLedger.from_dict(payload)

    def test_artifact_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            record = store.put_text(
                "A",
                "original",
                logical_role="certificate",
                producer="test",
            )
            store.path_for(record.artifact_id).write_text("tampered", encoding="utf-8")
            verification = store.verify()
            self.assertFalse(verification["valid"])
            self.assertIn("digest mismatch", verification["errors"][0])

    def test_evidence_digest_preflight_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, empty_trace())
            workspace.add_claim(ClaimRecord("C", "C", "scope"))
            before = workspace.state_digest()
            record = evidence_record("E", "g", b"expected")
            with self.assertRaisesRegex(ValueError, "prospective artifact"):
                workspace.add_evidence(record, artifact_content=b"different")
            self.assertEqual(workspace.state_digest(), before)
            self.assertEqual(workspace.committed_state_digest, before)
            self.assertNotIn("E", workspace.trace.evidence)
            self.assertEqual(len(workspace.artifacts.records), 0)

    def test_source_verification_preflight_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, empty_trace())
            workspace.add_claim(ClaimRecord("C", "C", "scope"))
            workspace.add_source_claim(source_record())
            before = workspace.state_digest()
            with self.assertRaisesRegex(ValueError, "non-SHA-256"):
                workspace.verify_source_claim(
                    "SRC-INDUCTION",
                    source_digest_sha256="bad",
                    verified_by="auditor",
                    verification_method="read source",
                    statement_correspondence="matches C",
                )
            self.assertEqual(workspace.state_digest(), before)
            self.assertEqual(workspace.committed_state_digest, before)
            self.assertEqual(
                workspace.sources.get("SRC-INDUCTION").status,
                SourceClaimStatus.PENDING,
            )

    def test_failed_promotion_is_sealed_as_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, empty_trace(), strict_artifacts=False)
            workspace.add_claim(ClaimRecord("C", "C", "scope"))
            before_events = len(workspace.events.events)
            with self.assertRaises(PromotionError):
                workspace.promote_claim("C")
            self.assertEqual(len(workspace.events.events), before_events + 1)
            self.assertEqual(
                workspace.events.events[-1].event_type,
                "CLAIM_PROMOTION_REJECTED",
            )
            self.assertEqual(workspace.state_digest(), workspace.committed_state_digest)
            self.assertEqual(workspace.trace.claims["C"].status, ClaimStatus.OPEN)

    def test_unverified_linked_source_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, empty_trace(), strict_artifacts=False)
            workspace.add_claim(ClaimRecord("C", "C", "scope"))
            workspace.add_source_claim(source_record())
            workspace.link_claim_sources("C", ("SRC-INDUCTION",))
            with self.assertRaisesRegex(WorkspaceAuditError, "unverified or inapplicable"):
                workspace.promote_claim("C")
            self.assertEqual(workspace.state_digest(), workspace.committed_state_digest)

    def test_object_deprecation_invalidates_verified_dependents(self) -> None:
        registry = ObjectRegistry()
        base = object_record()
        registry.add(base)
        registry.verify("OBJ-N")
        dependent = MathematicalObject(
            object_id="OBJ-P",
            symbol="P",
            name="property",
            kind=ObjectKind.MAP,
            definition="A predicate on N.",
            type_signature="P : N -> Prop",
            construction_source="Defined in the theorem contract.",
            current_role="Statement of C.",
            domain="N",
            codomain="Prop",
            dependencies=("OBJ-N",),
            applicability_boundary="Only values on N are defined.",
            failure_if_removed="C has no predicate.",
            status=ObjectStatus.DEFINED,
        )
        registry.add(dependent)
        registry.verify("OBJ-P")
        registry.deprecate("OBJ-N")
        self.assertEqual(registry.get("OBJ-N").status, ObjectStatus.DEPRECATED)
        self.assertEqual(registry.get("OBJ-P").status, ObjectStatus.DEFINED)


if __name__ == "__main__":
    unittest.main()
