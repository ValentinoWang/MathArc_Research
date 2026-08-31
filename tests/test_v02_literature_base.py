from __future__ import annotations

import hashlib
import json
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

    def test_observed_record_cannot_be_downgraded_by_incomplete_retry(self) -> None:
        content = b"immutable observed"
        digest = hashlib.sha256(content).hexdigest()
        complete = obs(uri="https://example.test/immutable", digest=digest)
        incomplete = new_observation(
            observation_id=complete.observation_id,
            canonical_uri=complete.canonical_uri,
            pinned_version=complete.pinned_version,
            license_status=LicenseStatus.OPEN,
            license_basis="publisher license page",
            content_summary="metadata",
            summary_basis="abstract",
            media_type="application/pdf",
        )
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            first = base.import_bytes(complete, content)
            result = base.import_bytes(incomplete, content)
            self.assertEqual(first.observation.status, ObservationStatus.OBSERVED)
            self.assertEqual(result.disposition, ImportDisposition.REJECTED)
            self.assertEqual(base.observations[0].status, ObservationStatus.OBSERVED)
            self.assertEqual(base.observations[0].artifact_id, first.observation.artifact_id)

    def test_idempotent_replay_fails_closed_when_blob_is_corrupted(self) -> None:
        content = b"integrity checked"
        digest = hashlib.sha256(content).hexdigest()
        observation = obs(uri="https://example.test/corrupt", digest=digest)
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            first = base.import_bytes(observation, content)
            assert first.artifact is not None
            base.artifacts.path_for(first.artifact.artifact_id).write_bytes(b"tampered")
            result = base.import_bytes(observation, content)
            self.assertEqual(result.disposition, ImportDisposition.REJECTED)
            self.assertEqual(base.observations[0].status, ObservationStatus.OBSERVED)
            with self.assertRaises(ValueError):
                LiteratureBase(directory)

    def test_replay_recovers_artifact_written_before_observation_manifest(self) -> None:
        content = b"recoverable artifact"
        digest = hashlib.sha256(content).hexdigest()
        observation = obs(uri="https://example.test/recover", digest=digest)
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            first = base.import_bytes(observation, content)
            self.assertEqual(first.disposition, ImportDisposition.IMPORTED)
            (Path(directory) / "observations.json").unlink()
            restored = LiteratureBase(directory)
            result = restored.import_bytes(observation, content)
            self.assertEqual(result.disposition, ImportDisposition.IMPORTED)
            self.assertEqual(len(restored.artifacts.records), 1)
            self.assertEqual(len(restored.observations), 1)

    def test_observed_replay_requires_open_license_and_budget(self) -> None:
        content = b"replay gates"
        digest = hashlib.sha256(content).hexdigest()
        observation = obs(uri="https://example.test/replay-gates", digest=digest)
        restricted = new_observation(
            observation_id=observation.observation_id,
            canonical_uri=observation.canonical_uri,
            pinned_version=observation.pinned_version,
            license_status=LicenseStatus.RESTRICTED,
            license_basis="terms",
            content_summary="metadata",
            summary_basis="abstract",
            media_type="application/pdf",
            content_digest_sha256=digest,
        )
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            base.import_bytes(observation, content)
            self.assertEqual(base.import_bytes(restricted, content).disposition, ImportDisposition.REJECTED)
            exhausted = LiteratureBase(directory, BudgetLedger(cost_usd_limit=0.0, spent_cost_usd=0.0))
            self.assertEqual(exhausted.import_bytes(observation, content).disposition, ImportDisposition.REJECTED)

    def test_conflict_record_does_not_hide_observed_replay(self) -> None:
        content_a = b"first"
        content_b = b"second"
        digest_a = hashlib.sha256(content_a).hexdigest()
        digest_b = hashlib.sha256(content_b).hexdigest()
        observed = new_observation(
            observation_id="z-observed", canonical_uri="https://example.test/order", pinned_version="v1",
            license_status=LicenseStatus.OPEN, license_basis="license", content_summary="metadata",
            summary_basis="abstract", media_type="application/pdf", content_digest_sha256=digest_a,
        )
        conflict = new_observation(
            observation_id="a-conflict", canonical_uri=observed.canonical_uri, pinned_version="v1",
            license_status=LicenseStatus.OPEN, license_basis="license", content_summary="metadata",
            summary_basis="abstract", media_type="application/pdf", content_digest_sha256=digest_b,
        )
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            base.import_bytes(observed, content_a)
            self.assertEqual(base.import_bytes(conflict, content_b).disposition, ImportDisposition.CONFLICT)
            self.assertEqual(base.import_bytes(observed, content_a).disposition, ImportDisposition.IDEMPOTENT)

    def test_conflict_id_does_not_overwrite_unrelated_observed_record(self) -> None:
        content_a = b"first"
        content_b = b"second"
        digest_a = hashlib.sha256(content_a).hexdigest()
        digest_b = hashlib.sha256(content_b).hexdigest()
        observed = new_observation(
            observation_id="shared", canonical_uri="https://example.test/one", pinned_version="v1",
            license_status=LicenseStatus.OPEN, license_basis="license", content_summary="metadata",
            summary_basis="abstract", media_type="application/pdf", content_digest_sha256=digest_a,
        )
        conflicting = new_observation(
            observation_id="shared", canonical_uri=observed.canonical_uri, pinned_version="v1",
            license_status=LicenseStatus.OPEN, license_basis="license", content_summary="metadata",
            summary_basis="abstract", media_type="application/pdf", content_digest_sha256=digest_b,
        )
        unrelated = new_observation(
            observation_id="shared-conflict-" + hashlib.sha256(
                f"{conflicting.logical_identity}|{digest_b}".encode("utf-8")
            ).hexdigest(),
            canonical_uri="https://example.test/unrelated", pinned_version="v1",
            license_status=LicenseStatus.OPEN, license_basis="license", content_summary="metadata",
            summary_basis="abstract", media_type="application/pdf", content_digest_sha256=digest_b,
        )
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            self.assertEqual(base.import_bytes(observed, content_a).disposition, ImportDisposition.IMPORTED)
            self.assertEqual(base.import_bytes(unrelated, content_b).disposition, ImportDisposition.IMPORTED)
            result = base.import_bytes(conflicting, content_b)
            self.assertEqual(result.disposition, ImportDisposition.REJECTED)
            restored = LiteratureBase(directory)
            self.assertEqual(
                restored._observations[unrelated.observation_id].logical_identity,
                unrelated.logical_identity,
            )

    def test_two_instances_merge_distinct_writes_from_the_same_root(self) -> None:
        content_a = b"first instance"
        content_b = b"second instance"
        with tempfile.TemporaryDirectory() as directory:
            first = LiteratureBase(directory)
            second = LiteratureBase(directory)
            first_result = first.import_bytes(
                obs(uri="https://example.test/first", digest=hashlib.sha256(content_a).hexdigest()),
                content_a,
            )
            second_result = second.import_bytes(
                obs(uri="https://example.test/second", digest=hashlib.sha256(content_b).hexdigest()),
                content_b,
            )
            self.assertEqual(first_result.disposition, ImportDisposition.IMPORTED)
            self.assertEqual(second_result.disposition, ImportDisposition.IMPORTED)
            restored = LiteratureBase(directory)
            self.assertEqual(len(restored.observations), 2)

    def test_replay_rejects_conflicting_artifact_metadata(self) -> None:
        content = b"metadata integrity"
        digest = hashlib.sha256(content).hexdigest()
        observation = obs(uri="https://example.test/metadata", digest=digest)
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            first = base.import_bytes(observation, content)
            assert first.artifact is not None
            manifest_path = Path(directory) / "artifacts" / "manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["records"][0]["producer"] = "untrusted-producer"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                restored = LiteratureBase(directory)
                restored.import_bytes(observation, content)


if __name__ == "__main__":
    unittest.main()
