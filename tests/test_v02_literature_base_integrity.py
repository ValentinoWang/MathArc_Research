from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.literature_base import ImportDisposition, LiteratureBase
from matharc.v02.source_observation import (
    LicenseStatus,
    ObservationStatus,
    SourceObservation,
    new_observation,
)


def observation(
    observation_id: str,
    digest: str,
    status: ObservationStatus = ObservationStatus.OBSERVED,
    *,
    canonical_uri: str = "https://integrity.example/paper",
    pinned_version: str = "v1",
) -> SourceObservation:
    return new_observation(
        observation_id=observation_id,
        canonical_uri=canonical_uri,
        pinned_version=pinned_version,
        observed_at="2026-09-02T08:00:00+00:00",
        license_status=LicenseStatus.OPEN,
        license_basis="integrity fixture license",
        content_summary="Descriptive integrity fixture metadata.",
        summary_basis="fixture",
        media_type="text/plain",
        content_digest_sha256=digest,
        status=status,
    )


class LiteratureBaseIntegrityTests(unittest.TestCase):
    def test_source_identity_preserves_path_case_and_delimiter_fields(self) -> None:
        content = b"identity collision fixture"
        digest = hashlib.sha256(content).hexdigest()
        cases = (
            (
                observation("OBS-UPPER", digest, canonical_uri="HTTPS://INTEGRITY.EXAMPLE/Paper"),
                observation("OBS-LOWER", digest, canonical_uri="https://integrity.example/paper"),
            ),
            (
                observation("OBS-LEFT", digest, canonical_uri="https://integrity.example/a|b", pinned_version="c"),
                observation("OBS-RIGHT", digest, canonical_uri="https://integrity.example/a", pinned_version="b|c"),
            ),
        )
        for left, right in cases:
            with self.subTest(left=left.observation_id, right=right.observation_id):
                self.assertNotEqual(left.logical_identity, right.logical_identity)
                self.assertNotEqual(left.idempotency_key, right.idempotency_key)
                with tempfile.TemporaryDirectory() as directory:
                    base = LiteratureBase(directory)
                    self.assertEqual(
                        ImportDisposition.IMPORTED,
                        base.import_bytes(left, content).disposition,
                    )
                    self.assertEqual(
                        ImportDisposition.IMPORTED,
                        base.import_bytes(right, content).disposition,
                    )
                    self.assertEqual(
                        {left.observation_id, right.observation_id},
                        {item.observation_id for item in base.observations},
                    )

    def test_distinct_input_id_can_replay_one_observed_record_idempotently(self) -> None:
        content = b"same logical source"
        digest = hashlib.sha256(content).hexdigest()
        first = observation("OBS-A", digest)
        alternate = observation("OBS-B", digest)
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            self.assertEqual(ImportDisposition.IMPORTED, base.import_bytes(first, content).disposition)
            result = base.import_bytes(alternate, content)
            self.assertEqual(ImportDisposition.IDEMPOTENT, result.disposition)
            self.assertEqual(1, len(base.observations))

    def test_persisted_distinct_records_cannot_reuse_idempotency_key(self) -> None:
        content = b"duplicate logical identity"
        digest = hashlib.sha256(content).hexdigest()
        first = observation("OBS-A", digest)
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            self.assertEqual(ImportDisposition.IMPORTED, base.import_bytes(first, content).disposition)
            manifest_path = Path(directory) / "observations.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            duplicate = dict(payload["observations"][0])
            duplicate["observation_id"] = "OBS-C"
            payload["observations"].append(duplicate)
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "idempotency key"):
                LiteratureBase(directory)

    def test_distinct_pending_record_with_same_idempotency_key_is_rejected(self) -> None:
        content = b"pending duplicate logical identity"
        digest = hashlib.sha256(content).hexdigest()
        first = observation("OBS-A", digest)
        alternate = observation("OBS-B", digest)
        first = SourceObservation.from_dict(
            {
                **first.to_dict(),
                "license_status": LicenseStatus.RESTRICTED.value,
                "status": ObservationStatus.PENDING.value,
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            self.assertEqual(ImportDisposition.PENDING, base.import_bytes(first, content).disposition)
            result = base.import_bytes(alternate, content)
            self.assertEqual(ImportDisposition.REJECTED, result.disposition)
            self.assertIn("idempotency key", result.reason)
            self.assertEqual(1, len(base.observations))


if __name__ == "__main__":
    unittest.main()
