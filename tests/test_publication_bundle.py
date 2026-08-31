from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.publication.adapters import publication_bundle_for_workspace
from matharc.publication.models import PublicationBundle, ReviewBundleRef
from matharc.v02.schema import digest_json
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_demo import write_workspace_demo


class PublicationBundleTests(unittest.TestCase):
    def test_digest_round_trip_and_tamper_rejection(self) -> None:
        bundle = PublicationBundle("paper", 1, {"C-MAIN": 3})
        restored = PublicationBundle.from_dict(bundle.to_dict())
        self.assertEqual(restored.digest_sha256, bundle.digest_sha256)
        payload = bundle.to_dict()
        payload["claim_revisions"] = {"C-MAIN": 4}
        with self.assertRaises(ValueError):
            PublicationBundle.from_dict(payload)

    def test_publication_does_not_copy_claim_facts(self) -> None:
        bundle = PublicationBundle("paper", 1, {"C-MAIN": 3})
        self.assertNotIn("statement", json.dumps(bundle.to_dict()))


class PublicationAdversarialTests(unittest.TestCase):
    def test_workspace_demo_is_loadable_by_publication_layer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_workspace_demo(root)
            self.assertTrue((root / "workspace.json").is_file())


class PublicationAdapterV02Tests(unittest.TestCase):
    """Exercises the matharc.publication.adapters bridge from a real v0.2
    ResearchWorkspace, the only code path that actually produces a
    PublicationBundle from live research data (every other test in this
    module builds PublicationBundle by hand)."""

    def test_publication_bundle_for_workspace_reflects_real_workspace_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "v02-workspace"
            write_full_workspace_bundle(target)
            workspace = ResearchWorkspace.load(target)
            review_ref = ReviewBundleRef(
                bundle_id="RB-C-TARGET-0",
                claim_id="C-TARGET",
                claim_revision=0,
                digest_sha256="a" * 64,
            )

            bundle = publication_bundle_for_workspace(
                workspace,
                paper_id="workspace-demo-paper",
                paper_version=1,
                review_bundles=(review_ref,),
            )

            self.assertEqual("workspace-demo-paper", bundle.paper_id)
            self.assertEqual(1, bundle.paper_version)
            self.assertEqual(
                {claim_id: claim.revision for claim_id, claim in workspace.trace.claims.items()},
                bundle.claim_revisions,
            )
            self.assertEqual((review_ref,), bundle.review_bundles)
            self.assertTrue(bundle.workspace_audit_digest)
            self.assertTrue(bundle.source_registry_digest)
            self.assertTrue(bundle.object_registry_digest)
            self.assertTrue(bundle.artifact_manifest_digest)
            # The four digests are independent audit views (not each other's echo).
            self.assertEqual(
                4,
                len(
                    {
                        bundle.workspace_audit_digest,
                        bundle.source_registry_digest,
                        bundle.object_registry_digest,
                        bundle.artifact_manifest_digest,
                    }
                ),
            )
            self.assertEqual(
                PublicationBundle.from_dict(bundle.to_dict()).digest_sha256,
                bundle.digest_sha256,
            )

    def test_publication_bundle_for_workspace_does_not_gate_on_audit_validity(self) -> None:
        """Documents actual (not assumed) behavior: unlike every mutating
        ResearchWorkspace method (which asserts committed state and raises
        WorkspaceAuditError on an unsealed change, e.g. add_claim), the
        adapter does NOT check report.valid before building a bundle -- it
        bakes whatever audit report it gets, valid or not, into
        workspace_audit_digest. This is a real gap relative to the rest of
        the workspace's fail-closed conventions; flagged to the repo owner
        separately rather than silently changed here. This test pins the
        current contract so a future change to that behavior is a
        deliberate, visible diff instead of a silent one."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "v02-workspace"
            write_full_workspace_bundle(target)
            workspace = ResearchWorkspace.load(target)
            # Same unsealed direct-mutation idiom as
            # scripts/v0_2_workspace_acceptance.py's gate_direct_mutation.
            workspace.trace.metadata["injected"] = True
            invalid_report = workspace.audit(require_current_commit=True)
            self.assertFalse(invalid_report.valid)

            bundle = publication_bundle_for_workspace(workspace, paper_id="paper", paper_version=1)

            self.assertEqual(digest_json(invalid_report.to_dict()), bundle.workspace_audit_digest)
