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
) -> SourceObservation:
    return new_observation(
        observation_id=observation_id,
        canonical_uri="https://integrity.example/paper",
        pinned_version="v1",
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
