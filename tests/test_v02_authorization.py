from __future__ import annotations

import hashlib
import tempfile
import unittest

from matharc.v02.authorization import (
    ActorContext,
    AuthorizationError,
    Capability,
    RolePolicy,
    SecuredResearchWorkspace,
)
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    TheoremContract,
)
from matharc.v02.trace import ResearchTrace
from matharc.v02.workspace import ResearchWorkspace


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def actor(role: str) -> ActorContext:
    return ActorContext(f"actor-{role}", role, "session-1")


def evidence(evidence_id: str, group: str, content: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim_ids=("C",),
        kind=EvidenceKind.EXACT_CERTIFICATE,
        status=EvidenceStatus.ACCEPTED,
        summary="checked",
        artifact_uri=f"workspace://{evidence_id}",
        digest_sha256=sha(content),
        producer=f"producer-{group}",
        verifier=f"verifier-{group}",
        independence_group=group,
        replay_command=f"python replay.py {evidence_id}",
        statement_correspondence="exactly checks C",
    )


class AuthorizationTests(unittest.TestCase):
    def workspace(self, directory: str) -> SecuredResearchWorkspace:
        trace = ResearchTrace(
            "AUTH-RUN",
            TheoremContract("K", "prove C", ("C",), "scope"),
        )
        return SecuredResearchWorkspace(
            ResearchWorkspace(directory, trace, strict_artifacts=True)
        )

    def test_prover_cannot_create_or_promote_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            secured = self.workspace(directory)
            with self.assertRaisesRegex(AuthorizationError, "ADD_CLAIM"):
                secured.add_claim(actor("prover"), ClaimRecord("C", "C", "scope"))
            with self.assertRaisesRegex(AuthorizationError, "PROMOTE_CLAIM"):
                secured.promote_claim(actor("prover"), "C")
            self.assertFalse(secured.trace.claims)

    def test_director_declares_and_verifier_supplies_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            secured = self.workspace(directory)
            secured.add_claim(
                actor("research-director"),
                ClaimRecord(
                    "C",
                    "C",
                    "scope",
                    critical=True,
                    boundary="only the contracted scope",
                ),
            )
            with self.assertRaisesRegex(AuthorizationError, "ADD_EVIDENCE"):
                secured.add_evidence(
                    actor("prover"), evidence("E0", "g0", "zero"), artifact_content="zero"
                )
            secured.add_evidence(
                actor("verifier"),
                evidence("E1", "g1", "one"),
                artifact_content="one",
            )
            secured.add_evidence(
                actor("verifier"),
                evidence("E2", "g2", "two"),
                artifact_content="two",
            )
            self.assertEqual(secured.trace.claims["C"].status, ClaimStatus.OPEN)
            with self.assertRaisesRegex(AuthorizationError, "PROMOTE_CLAIM"):
                secured.promote_claim(actor("verifier"), "C")
            secured.promote_claim(actor("promotion-gate"), "C")
            self.assertEqual(secured.trace.claims["C"].status, ClaimStatus.PROVED)
            self.assertIn("promotion-gate", secured.workspace.events.events[-1].actor)

    def test_unknown_role_is_rejected(self) -> None:
        policy = RolePolicy.default()
        with self.assertRaisesRegex(AuthorizationError, "unknown role"):
            policy.require(actor("unknown"), Capability.ADD_PUBLIC_REASONING)

    def test_policy_has_no_prover_promotion_grant(self) -> None:
        policy = RolePolicy.default()
        self.assertFalse(policy.allows(actor("prover"), Capability.PROMOTE_CLAIM))
        self.assertTrue(
            policy.allows(actor("promotion-gate"), Capability.PROMOTE_CLAIM)
        )
        self.assertFalse(
            policy.allows(actor("falsifier"), Capability.RECORD_EXACT_FAILURE)
        )
        self.assertTrue(
            policy.allows(actor("verifier"), Capability.RECORD_EXACT_FAILURE)
        )


if __name__ == "__main__":
    unittest.main()
