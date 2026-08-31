from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from matharc.v02.budget import BudgetLedger
from matharc.v02.literature_base import ImportDisposition, LiteratureBase
from matharc.v02.source_observation import LicenseStatus, ObservationStatus, new_observation


def obs(uri: str = "https://example.test/paper.pdf", digest: str = ""):
    return new_observation(
        observation_id=uri + digest[:4], canonical_uri=uri, pinned_version="v1",
        license_status=LicenseStatus.OPEN, license_basis="publisher license page",
        content_summary="descriptive bibliographic metadata", summary_basis="abstract",
        media_type="application/pdf", content_digest_sha256=digest,
    )


class LiteratureBaseTests(unittest.TestCase):
    def test_pending_license_can_be_retried_after_license_confirmation(self) -> None:
        content = b"<html>abstract</html>"
        digest = hashlib.sha256(content).hexdigest()
        restricted = new_observation(
            observation_id="retry", canonical_uri="https://example.test/retry", pinned_version="v1",
            license_status=LicenseStatus.RESTRICTED, license_basis="terms", content_summary="metadata",
            summary_basis="abstract", media_type="text/html", content_digest_sha256=digest,
        )
        opened = new_observation(
            observation_id="retry", canonical_uri="https://example.test/retry", pinned_version="v1",
            license_status=LicenseStatus.OPEN, license_basis="publisher license page", content_summary="metadata",
            summary_basis="abstract", media_type="text/html", content_digest_sha256=digest,
        )
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            self.assertEqual(base.import_bytes(restricted, content).disposition, ImportDisposition.PENDING)
            result = base.import_bytes(opened, content, source_filename="abstract.html")
            self.assertEqual(result.disposition, ImportDisposition.IMPORTED)
            self.assertEqual(result.observation.status, ObservationStatus.OBSERVED)
            self.assertEqual(result.artifact.size_bytes if result.artifact else None, len(content))

    def test_import_idempotency_conflict_and_reload(self) -> None:
        content = b"%PDF-1.7 sample"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            first = base.import_bytes(obs(digest=digest), content, source_filename="paper.pdf")
            self.assertEqual(first.disposition, ImportDisposition.IMPORTED)
            replay = base.import_bytes(obs(uri="https://example.test/paper.pdf", digest=digest), content)
            self.assertEqual(replay.disposition, ImportDisposition.IDEMPOTENT)
            conflict = base.import_bytes(obs(uri="https://example.test/paper.pdf", digest="a" * 64), b"other")
            self.assertEqual(conflict.disposition, ImportDisposition.CONFLICT)
            restored = LiteratureBase(directory)
            self.assertEqual(len(restored.observations), 2)
            self.assertEqual(len(restored.artifacts.records), 1)

    def test_failures_remain_pending_without_artifacts(self) -> None:
        content = b"%PDF"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            restricted = new_observation(
                observation_id="restricted", canonical_uri="https://example.test/r", pinned_version="v1",
                license_status=LicenseStatus.RESTRICTED, license_basis="terms", content_summary="metadata",
                summary_basis="abstract", media_type="application/pdf", content_digest_sha256=digest,
            )
            base = LiteratureBase(directory)
            result = base.import_bytes(restricted, content)
            self.assertEqual(result.disposition, ImportDisposition.PENDING)
            self.assertEqual(result.observation.status, ObservationStatus.PENDING)
            self.assertEqual(len(base.artifacts.records), 0)

    def test_digest_errors_and_missing_digest_remain_pending(self) -> None:
        content = b"%PDF"
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            missing = obs(uri="https://example.test/missing")
            self.assertEqual(base.import_bytes(missing, content).disposition, ImportDisposition.PENDING)
            mismatch = obs(uri="https://example.test/mismatch", digest="a" * 64)
            self.assertEqual(base.import_bytes(mismatch, content).disposition, ImportDisposition.PENDING)
            self.assertEqual(len(base.artifacts.records), 0)

    def test_registry_is_not_created_or_mutated(self) -> None:
        content = b"%PDF registry boundary"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            base.import_bytes(obs(digest=digest), content)
            self.assertFalse((Path(directory) / "source-registry.json").exists())
            self.assertFalse((Path(directory) / "claims.json").exists())

    def test_unsupported_media_is_rejected_by_observation_contract(self) -> None:
        with self.assertRaises(ValueError):
            new_observation(
                observation_id="image", canonical_uri="https://example.test/image", pinned_version="v1",
                license_status=LicenseStatus.OPEN, license_basis="license", content_summary="metadata",
                summary_basis="abstract", media_type="image/png", content_digest_sha256="a" * 64,
            )

    def test_duplicate_observation_id_cannot_overwrite_another_identity(self) -> None:
        content = b"same id"
        digest = hashlib.sha256(content).hexdigest()
        first = obs(uri="https://example.test/one", digest=digest)
        second = obs(uri="https://example.test/two", digest=digest)
        second = new_observation(
            observation_id=first.observation_id, canonical_uri=second.canonical_uri, pinned_version="v1",
            license_status=LicenseStatus.OPEN, license_basis="publisher license page", content_summary="metadata",
            summary_basis="abstract", media_type="application/pdf", content_digest_sha256=digest,
        )
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            self.assertEqual(base.import_bytes(first, content).disposition, ImportDisposition.IMPORTED)
            result = base.import_bytes(second, content)
            self.assertEqual(result.disposition, ImportDisposition.REJECTED)
            self.assertEqual(len(base.observations), 1)

    def test_budget_blocks_before_write_and_does_not_create_claims(self) -> None:
        content = b"%PDF"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory, BudgetLedger(cost_usd_limit=0.0, spent_cost_usd=0.0))
            result = base.import_bytes(obs(digest=digest), content)
            self.assertEqual(result.disposition, ImportDisposition.PENDING)
            self.assertEqual(len(base.artifacts.records), 0)
            self.assertIsNone(result.observation.artifact_id)


if __name__ == "__main__":
    unittest.main()
