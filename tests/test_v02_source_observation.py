from __future__ import annotations

import hashlib
import unittest

from matharc.v02.source_observation import (
    LicenseStatus,
    ObservationStatus,
    SourceObservation,
)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def observation(**overrides: object) -> SourceObservation:
    values: dict[str, object] = {
        "observation_id": "OBS-1",
        "canonical_uri": "https://arxiv.org/abs/2601.22401",
        "pinned_version": "v1",
        "observed_at": "2026-08-31T00:00:00+00:00",
        "license_status": LicenseStatus.OPEN,
        "license_basis": "publisher metadata, checked 2026-08-31",
        "content_summary": "Metadata and abstract describe the stated research question.",
        "summary_basis": "abstract, section 1",
        "media_type": "application/pdf",
        "content_digest_sha256": digest(b"source"),
        "artifact_id": "ART-1",
        "status": ObservationStatus.OBSERVED,
    }
    values.update(overrides)
    return SourceObservation(**values)  # type: ignore[arg-type]


class SourceObservationTests(unittest.TestCase):
    def test_round_trip_and_deterministic_key(self) -> None:
        value = observation()
        restored = SourceObservation.from_dict(value.to_dict())
        self.assertEqual(value, restored)
        self.assertEqual(value.idempotency_key, restored.idempotency_key)

    def test_same_identity_different_digest_is_conflict(self) -> None:
        self.assertTrue(observation().conflicts_with(observation(content_digest_sha256=digest(b"other"))))

    def test_unknown_license_is_pending_only(self) -> None:
        value = observation(license_status=LicenseStatus.UNKNOWN, status=ObservationStatus.PENDING)
        self.assertEqual(value.status, ObservationStatus.PENDING)
        with self.assertRaises(ValueError):
            observation(license_status=LicenseStatus.UNKNOWN)

    def test_rejects_latest_version_and_unsupported_media(self) -> None:
        with self.assertRaises(ValueError):
            observation(pinned_version="latest")
        with self.assertRaises(ValueError):
            observation(media_type="image/png")

    def test_rejects_invalid_timestamp_and_bare_status_strings(self) -> None:
        with self.assertRaises(ValueError):
            observation(observed_at="yesterday")
        with self.assertRaises(TypeError):
            observation(status="OBSERVED")
        with self.assertRaises(TypeError):
            observation(license_status="OPEN")

    def test_rejects_proof_language_in_summary(self) -> None:
        with self.assertRaises(ValueError):
            observation(content_summary="The theorem is proved and the problem is solved.")

    def test_allows_descriptive_open_word_without_status_assertion(self) -> None:
        value = observation(content_summary="The paper studies an open dataset and records metadata.")
        self.assertEqual(value.status, ObservationStatus.OBSERVED)

    def test_observation_is_not_a_source_claim(self) -> None:
        value = observation()
        self.assertNotIn("claimed_result", value.to_dict())
        self.assertNotIn("linked_claim_ids", value.to_dict())

    def test_rejects_unknown_fields_and_bad_digest(self) -> None:
        with self.assertRaises(ValueError):
            SourceObservation.from_dict({**observation().to_dict(), "extra": True})
        with self.assertRaises(ValueError):
            observation(content_digest_sha256="bad")


if __name__ == "__main__":
    unittest.main()
