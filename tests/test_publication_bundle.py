from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.publication.models import PublicationBundle
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
