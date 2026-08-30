from __future__ import annotations

import unittest

from matharc.v02.legacy_harness import (
    ImportPolicy,
    LegacyHarnessError,
    import_legacy_harness,
)


class LegacyHarnessImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.progress = {
            "run_id": "GTC-INTERLEAVED-GLUING-012",
            "problem": "Graceful Tree Conjecture",
            "state": "BLOCKED_EXACT",
            "phase": "ADVERSARIAL_AUDIT",
            "current_weighted_progress_percent": 82,
            "full_conjecture_logical_closure": "0/1",
            "new_closed_nodes": [
                {
                    "id": "C-LOCAL",
                    "statement": "A named finite component family admits the stated gluing.",
                    "status": "PROVED_AND_AUDITED",
                }
            ],
            "critical_open_obligations": [
                {
                    "id": "O-GLOBAL",
                    "statement": "Close the remaining universal decomposition quantifier.",
                }
            ],
            "scope_limit": "The local family is not the full conjecture.",
        }
        self.validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "counts": {"acceptance_records": 0},
        }

    def test_metadata_import_never_launders_verified_status(self) -> None:
        result = import_legacy_harness(self.progress, validation=self.validation)
        self.assertEqual(result["release_state"], "BLOCKED_EXACT")
        self.assertEqual(result["progress"]["theorem_closure_bit"], 0)
        self.assertEqual(result["imported_claims"][0]["matharc_status"], "SUPPORTED")
        self.assertIn("zero acceptance records", " ".join(result["warnings"]))

    def test_replay_manifest_requires_independent_reconstruction(self) -> None:
        manifest = {
            "acceptance_records": [
                {
                    "claim_id": "C-LOCAL",
                    "artifact_sha256": "a" * 64,
                    "statement_sha256": "b" * 64,
                    "replay_command": "python verify.py",
                    "result": "PASS",
                    "independent_reconstruction": False,
                }
            ]
        }
        result = import_legacy_harness(
            self.progress,
            validation=self.validation,
            acceptance_manifest=manifest,
            policy=ImportPolicy(mode="replay_manifest"),
        )
        claim = result["imported_claims"][0]
        self.assertEqual(claim["matharc_status"], "SUPPORTED")
        self.assertIn("missing independent reconstruction", claim["promotion_blockers"])

    def test_even_replayed_local_claim_does_not_close_open_theorem(self) -> None:
        manifest = {
            "acceptance_records": [
                {
                    "claim_id": "C-LOCAL",
                    "artifact_sha256": "a" * 64,
                    "statement_sha256": "b" * 64,
                    "replay_command": "python verify.py",
                    "result": "PASS",
                    "independent_reconstruction": True,
                }
            ]
        }
        result = import_legacy_harness(
            self.progress,
            validation=self.validation,
            acceptance_manifest=manifest,
            policy=ImportPolicy(mode="replay_manifest"),
        )
        self.assertEqual(result["imported_claims"][0]["matharc_status"], "VERIFIED")
        self.assertEqual(result["release_state"], "BLOCKED_EXACT")
        self.assertEqual(result["progress"]["theorem_closure_bit"], 0)

    def test_closed_source_requires_replay_for_every_claim(self) -> None:
        progress = dict(self.progress)
        progress["full_conjecture_logical_closure"] = "1/1"
        progress["critical_open_obligations"] = []
        result = import_legacy_harness(progress, validation=self.validation)
        self.assertEqual(result["release_state"], "BLOCKED_EXACT")
        self.assertTrue(any("did not re-establish" in item for item in result["warnings"]))

    def test_invalid_progress_range_is_rejected(self) -> None:
        progress = dict(self.progress)
        progress["current_weighted_progress_percent"] = 120
        with self.assertRaises(LegacyHarnessError):
            import_legacy_harness(progress, validation=self.validation)


if __name__ == "__main__":
    unittest.main()
