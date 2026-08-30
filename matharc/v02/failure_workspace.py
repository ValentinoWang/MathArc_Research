"""Tamper-evident workspace façade for v0.3 failure channels.

Trace-level failure-channel helpers preserve legacy serialization.  This module
adds the stronger Workspace boundary: exact claim counterexamples must point to
content-addressed artifacts whose bytes hash to the EvidenceRecord digest before
they are allowed to trigger the legacy REFUTED cascade.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .failure_channels import (
    FailureChannelRecord,
    record_claim_counterexample,
    record_review_gap,
    record_route_failure,
)
from .schema import FailureClass, FailureRecord, digest_json

if TYPE_CHECKING:
    from ._workspace_impl import ResearchWorkspace


class WorkspaceFailureError(ValueError):
    """Raised when a failure channel lacks workspace-grade evidence."""


def record_workspace_review_gap(
    workspace: "ResearchWorkspace",
    record: FailureChannelRecord,
    *,
    actor: str = "human-reviewer",
) -> None:
    workspace._assert_committed()
    record_review_gap(workspace.trace, record)
    workspace._seal_transition(
        "REVIEW_GAP_RECORDED",
        actor=actor,
        subject_ids=(record.event_id, record.claim_id),
        details={"failure_channel_digest_sha256": record.digest_sha256},
    )


def record_workspace_route_failure(
    workspace: "ResearchWorkspace",
    record: FailureChannelRecord,
    *,
    actor: str = "falsifier",
) -> None:
    workspace._assert_committed()
    record_route_failure(workspace.trace, record)
    workspace._seal_transition(
        "ROUTE_FAILURE_RECORDED",
        actor=actor,
        subject_ids=(record.event_id, record.claim_id, record.route_id),
        details={"failure_channel_digest_sha256": record.digest_sha256},
    )


def _verify_counterexample_artifacts(
    workspace: "ResearchWorkspace", record: FailureChannelRecord
) -> None:
    missing_links = [
        evidence_id
        for evidence_id in record.evidence_ids
        if evidence_id not in workspace.evidence_artifact_links
    ]
    if missing_links:
        raise WorkspaceFailureError(
            f"counterexample evidence lacks stored artifacts: {missing_links}"
        )
    for evidence_id in record.evidence_ids:
        evidence = workspace.trace.evidence.get(evidence_id)
        if evidence is None:
            raise WorkspaceFailureError(f"unknown counterexample evidence: {evidence_id}")
        artifact_id = workspace.evidence_artifact_links[evidence_id]
        try:
            artifact = workspace.artifacts.get(artifact_id)
        except KeyError as exc:
            raise WorkspaceFailureError(
                f"counterexample artifact is missing: {artifact_id}"
            ) from exc
        if artifact.sha256 != evidence.digest_sha256:
            raise WorkspaceFailureError(
                f"counterexample artifact digest mismatch for {evidence_id}: "
                f"artifact={artifact.sha256} evidence={evidence.digest_sha256}"
            )


def record_workspace_claim_counterexample(
    workspace: "ResearchWorkspace",
    record: FailureChannelRecord,
    *,
    actor: str = "verifier",
    failure_class: FailureClass = FailureClass.FALSE_STATEMENT,
) -> FailureRecord:
    workspace._assert_committed()
    _verify_counterexample_artifacts(workspace, record)
    result = record_claim_counterexample(
        workspace.trace,
        record,
        failure_class=failure_class,
    )
    workspace._seal_transition(
        "CLAIM_COUNTEREXAMPLE_RECORDED",
        actor=actor,
        subject_ids=(
            record.event_id,
            record.claim_id,
            record.route_id,
            *record.evidence_ids,
            *result.invalidated_claim_ids,
        ),
        details={
            "failure_channel_digest_sha256": record.digest_sha256,
            "legacy_failure_digest_sha256": digest_json(result.to_dict()),
        },
    )
    return result
