from __future__ import annotations

import hashlib
import tempfile
import unittest

from matharc.v02.failure_channels import (
    FailureChannel,
    FailureChannelRecord,
)
from matharc.v02.failure_workspace import (
    WorkspaceFailureError,
    record_workspace_claim_counterexample,
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
from matharc.v02.trace import ResearchTrace
from matharc.v02.workspace import ResearchWorkspace


def _trace() -> ResearchTrace:
    trace = ResearchTrace(
        "V03-WORKSPACE-CEX",
        TheoremContract("K", "Decide C.", ("C",), "declared scope"),
    )
    trace.add_claim(ClaimRecord("C", "C", "declared scope"))
    trace.add_route(
        ResearchRoute(
            "R",
            "candidate route",
            "mechanism",
            ("mechanism-r",),
            "search the smallest counterexample",
            RouteStatus.ACTIVE,
            ("C",),
        )
    )
    return trace


def _evidence(content: bytes) -> EvidenceRecord:
    digest = hashlib.sha256(content).hexdigest()
    return EvidenceRecord(
        evidence_id="E-CEX",
        claim_ids=("C",),
        kind=EvidenceKind.COUNTEREXAMPLE,
        status=EvidenceStatus.ACCEPTED,
        summary="Exact counterexample witness.",
        artifact_uri="workspace://E-CEX",
        digest_sha256=digest,
        producer="counterexample-generator",
        verifier="independent-checker",
        independence_group="cex:independent",
        replay_command="python replay_counterexample.py E-CEX",
        statement_correspondence="The witness satisfies the hypotheses and negates C.",
    )


def _record() -> FailureChannelRecord:
    return FailureChannelRecord(
        event_id="CEX-WORKSPACE-1",
        channel=FailureChannel.CLAIM_COUNTEREXAMPLE,
        claim_id="C",
        claim_revision=0,
        route_id="R",
        description="The stored witness falsifies C.",
        evidence_ids=("E-CEX",),
        exact=True,
    )


class WorkspaceCounterexampleTests(unittest.TestCase):
    def test_trace_only_counterexample_without_artifact_is_rejected(self) -> None:
        trace = _trace()
        trace.add_evidence(_evidence(b"counterexample-bytes"))
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, trace, strict_artifacts=True)
            with self.assertRaisesRegex(WorkspaceFailureError, "lacks stored artifacts"):
                record_workspace_claim_counterexample(workspace, _record())
        self.assertEqual(trace.claims["C"].status, ClaimStatus.OPEN)

    def test_content_addressed_counterexample_can_refute_claim(self) -> None:
        trace = _trace()
        content = b"counterexample-bytes"
        with tempfile.TemporaryDirectory() as directory:
            workspace = ResearchWorkspace(directory, trace, strict_artifacts=True)
            workspace.add_evidence(
                _evidence(content),
                artifact_content=content,
                artifact_id="ART-CEX",
                actor="verifier",
            )
            result = record_workspace_claim_counterexample(
                workspace,
                _record(),
                actor="verifier",
            )
            self.assertEqual(workspace.events.events[-1].event_type, "CLAIM_COUNTEREXAMPLE_RECORDED")
        self.assertTrue(result.exact)
        self.assertEqual(trace.claims["C"].status, ClaimStatus.REFUTED)
        self.assertEqual(trace.routes["R"].status, RouteStatus.FALSIFIED)


if __name__ == "__main__":
    unittest.main()
