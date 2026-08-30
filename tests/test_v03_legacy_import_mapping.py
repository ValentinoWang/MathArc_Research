from __future__ import annotations

import unittest

from matharc.v02.legacy_harness import (
    ImportPolicy,
    LegacyHarnessError,
    build_importable_trace,
    import_legacy_harness,
)
from matharc.v02.review import nominate_for_review


def _progress(nodes: list[dict[str, object]]) -> dict[str, object]:
    return {
        "run_id": "LEGACY-RUN-1",
        "problem": "A legacy conjecture",
        "state": "BLOCKED_EXACT",
        "phase": "ADVERSARIAL_AUDIT",
        "full_conjecture_logical_closure": "0/1",
        "new_closed_nodes": nodes,
        "critical_open_obligations": [
            {"id": "O-GLOBAL", "statement": "Close the remaining quantifier."}
        ],
        "scope_limit": "n <= 30",
    }


def _validation() -> dict[str, object]:
    return {"valid": True, "errors": [], "warnings": [], "counts": {"acceptance_records": 1}}


class DependencyMappingTests(unittest.TestCase):
    def test_dependencies_are_carried_into_the_report(self) -> None:
        progress = _progress(
            [
                {"id": "C-BASE", "statement": "base case", "status": "PROVED_AND_AUDITED"},
                {
                    "id": "C-STEP",
                    "statement": "inductive step",
                    "status": "PROVED_AND_AUDITED",
                    "dependencies": ["C-BASE"],
                },
            ]
        )
        result = import_legacy_harness(progress, validation=_validation())
        by_id = {item["claim_id"]: item for item in result["imported_claims"]}
        self.assertEqual(by_id["C-STEP"]["dependencies"], ["C-BASE"])
        self.assertEqual(by_id["C-BASE"]["dependencies"], [])

    def test_dangling_dependency_is_rejected(self) -> None:
        progress = _progress(
            [{"id": "C-STEP", "statement": "s", "status": "PROVED", "dependencies": ["C-GHOST"]}]
        )
        with self.assertRaises(LegacyHarnessError):
            import_legacy_harness(progress, validation=_validation())

    def test_self_dependency_is_rejected(self) -> None:
        progress = _progress(
            [{"id": "C-STEP", "statement": "s", "status": "PROVED", "dependencies": ["C-STEP"]}]
        )
        with self.assertRaises(LegacyHarnessError):
            import_legacy_harness(progress, validation=_validation())


class BuildImportableTraceTests(unittest.TestCase):
    def test_supported_node_never_launders_to_proved(self) -> None:
        # This is the exact invariant DEV_PATH_V03 names: "人核节点 SUPPORTED
        # 不洗白" -- a legacy PROVED_AND_AUDITED node, imported with zero
        # replay evidence, must land as CANDIDATE (reviewable) and nothing
        # stronger, no matter how confident the legacy source string sounds.
        progress = _progress(
            [{"id": "C-LOCAL", "statement": "a bold legacy claim", "status": "PROVED_AND_AUDITED"}]
        )
        report = import_legacy_harness(progress, validation=_validation())
        self.assertEqual(report["imported_claims"][0]["matharc_status"], "SUPPORTED")
        trace = build_importable_trace(report)
        self.assertEqual(trace.claims["C-LOCAL"].status.value, "CANDIDATE")
        self.assertEqual(trace.claims["C-LOCAL"].evidence_ids, ())

    def test_dependency_order_is_preserved_and_add_claim_succeeds(self) -> None:
        progress = _progress(
            [
                {"id": "C-BASE", "statement": "base", "status": "PROVED_AND_AUDITED"},
                {
                    "id": "C-STEP",
                    "statement": "step",
                    "status": "PROVED_AND_AUDITED",
                    "dependencies": ["C-BASE"],
                },
            ]
        )
        report = import_legacy_harness(progress, validation=_validation())
        trace = build_importable_trace(report)
        self.assertEqual(trace.claims["C-STEP"].dependencies, ("C-BASE",))
        self.assertIn("C-BASE", trace.claims)

    def test_dependency_cycle_is_rejected_at_the_mapping_boundary(self) -> None:
        progress = _progress(
            [
                {"id": "C-A", "statement": "a", "status": "PROVED", "dependencies": ["C-B"]},
                {"id": "C-B", "statement": "b", "status": "PROVED", "dependencies": ["C-A"]},
            ]
        )
        report = import_legacy_harness(progress, validation=_validation())
        with self.assertRaises(LegacyHarnessError) as ctx:
            build_importable_trace(report)
        self.assertIn("cycle", str(ctx.exception))

    def test_verified_node_gets_real_replayable_evidence(self) -> None:
        progress = _progress(
            [{"id": "C-LOCAL", "statement": "a legacy claim", "status": "PROVED_AND_AUDITED"}]
        )
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
        report = import_legacy_harness(
            progress,
            validation=_validation(),
            acceptance_manifest=manifest,
            policy=ImportPolicy(mode="replay_manifest"),
        )
        self.assertEqual(report["imported_claims"][0]["matharc_status"], "VERIFIED")
        trace = build_importable_trace(report, acceptance_manifest=manifest)
        self.assertEqual(trace.claims["C-LOCAL"].status.value, "CANDIDATE")
        evidence_ids = trace.claims["C-LOCAL"].evidence_ids
        self.assertEqual(len(evidence_ids), 1)
        evidence = trace.evidence[evidence_ids[0]]
        self.assertTrue(evidence.replayable)
        self.assertNotEqual(evidence.producer, evidence.verifier)

    def test_open_obligations_are_preserved_not_dropped(self) -> None:
        progress = _progress(
            [{"id": "C-LOCAL", "statement": "s", "status": "PROVED_AND_AUDITED"}]
        )
        report = import_legacy_harness(progress, validation=_validation())
        trace = build_importable_trace(report)
        preserved = trace.metadata["legacy_import_open_obligations"]
        self.assertEqual(len(preserved), 1)
        self.assertEqual(preserved[0]["obligation_id"], "O-GLOBAL")

    def test_wrong_schema_version_is_rejected(self) -> None:
        with self.assertRaises(LegacyHarnessError):
            build_importable_trace({"schema_version": "not-a-real-schema"})

    def test_imported_candidate_claim_closes_the_loop_into_r1_nomination(self) -> None:
        # The point of the whole mapping layer: prove a mapped claim is
        # actually usable by the rest of the review pipeline (R0-R6), not
        # just a standalone data structure disconnected from it.
        #
        # This particular imported claim has zero ResearchRoutes -- the
        # mapping layer only creates claims/evidence, never fabricates a
        # route the legacy source never had. R1's own rule ("every ACTIVE
        # route needs a completed execution record") is then vacuously
        # satisfied by "there are no active routes to check" -- which is
        # the real, correct-per-spec R1 behavior, not something the import
        # layer bypasses. A route-bearing claim would still need real
        # route execution before nominating, exactly as R1's own test
        # suite (test_v03_review.py::NominationTests) already covers.
        progress = _progress(
            [{"id": "C-LOCAL", "statement": "s", "status": "PROVED_AND_AUDITED"}]
        )
        report = import_legacy_harness(progress, validation=_validation())
        trace = build_importable_trace(report)
        nomination = nominate_for_review(trace, "C-LOCAL")
        self.assertEqual(nomination.claim_id, "C-LOCAL")
        self.assertEqual(nomination.route_ids, ())


if __name__ == "__main__":
    unittest.main()
