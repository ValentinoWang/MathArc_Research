from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from matharc.v02.console_topic import TopicStoreConfig, console_topic_projection
from matharc.v02.source_observation import LicenseStatus, new_observation
from matharc.v02.source_registry import SourceClaim, SourceKind, SourceRegistry
from matharc.v02.topic_observation import TopicObservationBatch, TopicObservationInput, TopicObservationRunner


class ConsoleTopicTests(unittest.TestCase):
    def test_projection_surfaces_verification_fields_without_status_inference(self) -> None:
        source = SourceClaim("SRC", SourceKind.PAPER, "citation", "https://example.invalid", "v1", "p.1", "reported result", ("scope",))
        registry = SourceRegistry([source])
        payload = console_topic_projection(registry)
        row = payload["source_claims"][0]
        for key in ("canonical_uri", "pinned_version", "locator", "verification_method", "statement_correspondence"):
            self.assertIn(key, row)
        self.assertEqual(payload["topic_observations"]["external_search_statistics"], "not_inferred")
        self.assertIn("does not infer open", payload["status_boundary"])

    def test_preexisting_store_is_projected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "topic"
            content = b"fixture source"
            observation = new_observation(
                observation_id="OBS-1", canonical_uri="https://example.test/1", pinned_version="v1",
                license_status=LicenseStatus.OPEN, license_basis="fixture", content_summary="Fixture metadata.",
                summary_basis="fixture", media_type="text/plain", content_digest_sha256=hashlib.sha256(content).hexdigest(),
                observed_at="2026-09-01T00:00:00+00:00",
            )
            runner = TopicObservationRunner(root, topic_id="union-closed", initial_cursor="c0")
            runner.run(TopicObservationBatch("union-closed", "c0", "c1", (TopicObservationInput("item", observation, content),)))
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            loaded = TopicStoreConfig(root, "union-closed", "c0").open_read_only()
            payload = console_topic_projection(SourceRegistry(), topic_store=loaded)
            self.assertEqual("c1", payload["topic_observations"]["next_cursor"])
            self.assertEqual(1, payload["topic_observations"]["observed_count"])
            after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(before, after)

    def test_missing_store_is_rejected_without_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "missing"
            with self.assertRaisesRegex(ValueError, "complete observation state"):
                TopicStoreConfig(root, "union-closed", "c0").open_read_only()
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
