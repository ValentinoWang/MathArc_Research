from __future__ import annotations

import unittest

from matharc.v02.console_topic import console_topic_projection
from matharc.v02.source_registry import SourceClaim, SourceKind, SourceRegistry


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


if __name__ == "__main__":
    unittest.main()
