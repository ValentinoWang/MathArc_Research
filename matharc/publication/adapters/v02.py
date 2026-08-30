from __future__ import annotations

from ...v02.schema import digest_json
from ...v02.workspace import ResearchWorkspace
from ..models import PublicationBundle, ReviewBundleRef


def publication_bundle_for_workspace(
    workspace: ResearchWorkspace,
    *,
    paper_id: str,
    paper_version: int = 1,
    review_bundles: tuple[ReviewBundleRef, ...] = (),
) -> PublicationBundle:
    """Create a reference-only aggregate from the v0.2 workspace."""
    report = workspace.audit(require_current_commit=True)
    return PublicationBundle(
        paper_id=paper_id,
        paper_version=paper_version,
        claim_revisions={key: claim.revision for key, claim in workspace.trace.claims.items()},
        review_bundles=review_bundles,
        workspace_audit_digest=digest_json(report.to_dict()),
        source_registry_digest=digest_json(workspace.sources.to_dict()),
        object_registry_digest=digest_json(workspace.objects.to_dict()),
        artifact_manifest_digest=digest_json(workspace.artifacts.to_dict()),
    )
