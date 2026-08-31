from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.artifact_store import ArtifactStore
from matharc.v02.problem_status import (
    ObservationDigestRef,
    OpenStatusCertificate,
    ProblemDossierSnapshot,
    ProblemStatus,
    ProblemStatusValidation,
    StatementVersion,
    StatusInvalidation,
    validate,
)
from matharc.v02.source_observation import LicenseStatus, ObservationStatus, SourceObservation


def observed_source(**overrides: object) -> SourceObservation:
    content = b"observed source"
    values: dict[str, object] = {
        "observation_id": "OBS-OPEN-1",
        "canonical_uri": "https://example.test/open-problem",
        "pinned_version": "v1",
        "observed_at": "2026-08-31T00:00:00+00:00",
        "license_status": LicenseStatus.OPEN,
        "license_basis": "publisher license page",
        "content_summary": "The abstract identifies the research question and its scope.",
        "summary_basis": "abstract",
        "media_type": "application/pdf",
        "content_digest_sha256": hashlib.sha256(content).hexdigest(),
        "artifact_id": "ART-OPEN-1",
        "status": ObservationStatus.OBSERVED,
    }
    values.update(overrides)
    return SourceObservation(**values)  # type: ignore[arg-type]


def valid_snapshot() -> tuple[ProblemDossierSnapshot, SourceObservation]:
    source = observed_source()
    statement = StatementVersion(
        problem_id="P-UNION-CLOSED",
        version=1,
        statement="Every finite union-closed family has an element in at least half its sets.",
    )
    certificate = OpenStatusCertificate(
        certificate_id="CERT-OPEN-1",
        problem_id=statement.problem_id,
        version=1,
        statement_version_id=statement.statement_version_id,
        statement_digest_sha256=statement.statement_digest_sha256,
        source_observations=(ObservationDigestRef.from_observation(source),),
        status=ProblemStatus.OPEN_REPORTED,
        limitations=("This is a time-bounded source report, not a mathematical proof.",),
        reviewer="status reviewer",
        issued_at="2026-08-31T00:00:00+00:00",
        expires_at="2026-09-30T00:00:00+00:00",
    )
    return (
        ProblemDossierSnapshot(
            snapshot_id="DOSSIER-OPEN-1",
            problem_id=statement.problem_id,
            version=1,
            statement=statement,
            certificate=certificate,
            snapshot_at="2026-08-31T00:00:00+00:00",
        ),
        source,
    )


class ProblemStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.artifacts = ArtifactStore(self.directory.name)
        self.artifacts.put_bytes(
            "ART-OPEN-1",
            b"observed source",
            logical_role="literature-observation",
            producer="matharc-literature-base",
            media_type="application/pdf",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_valid_open_snapshot_round_trips_with_stable_digests(self) -> None:
        snapshot, source = valid_snapshot()
        restored = ProblemDossierSnapshot.from_dict(snapshot.to_dict())
        self.assertEqual(snapshot, restored)
        self.assertEqual(snapshot.snapshot_digest_sha256, restored.snapshot_digest_sha256)
        result = validate(restored, {source.observation_id: source}, as_of="2026-09-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertEqual(ProblemStatus.OPEN_REPORTED, result.status)
        self.assertTrue(result.is_open)
        self.assertEqual((), result.invalidations)

    def test_versions_are_immutable(self) -> None:
        snapshot, _ = valid_snapshot()
        with self.assertRaises(FrozenInstanceError):
            snapshot.statement.statement = "rewritten"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            snapshot.certificate = None  # type: ignore[misc]

    def test_statement_change_invalidates_certificate(self) -> None:
        snapshot, source = valid_snapshot()
        changed = StatementVersion(
            problem_id=snapshot.problem_id,
            version=2,
            statement="Every union-closed family has an element in at least half its sets.",
        )
        stale = ProblemDossierSnapshot(
            snapshot_id="DOSSIER-OPEN-2",
            problem_id=snapshot.problem_id,
            version=2,
            statement=changed,
            certificate=snapshot.certificate,
            snapshot_at="2026-09-01T00:00:00+00:00",
        )
        result = stale.validate({source.observation_id: source}, as_of="2026-09-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertEqual(ProblemStatus.STALE, result.status)
        self.assertIn(StatusInvalidation.STATEMENT_VERSION_MISMATCH, result.invalidations)
        self.assertIn(StatusInvalidation.STATEMENT_DIGEST_MISMATCH, result.invalidations)

    def test_expired_or_missing_source_fails_closed(self) -> None:
        snapshot, source = valid_snapshot()
        expired = validate(snapshot, {source.observation_id: source}, as_of="2026-10-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertEqual(ProblemStatus.STALE, expired.status)
        self.assertEqual((StatusInvalidation.CERTIFICATE_EXPIRED,), expired.invalidations)
        missing = validate(snapshot, {}, as_of="2026-09-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertEqual(ProblemStatus.STALE, missing.status)
        self.assertEqual((StatusInvalidation.MISSING_SOURCE,), missing.invalidations)

    def test_changed_source_summary_invalidates_the_observed_source_reference(self) -> None:
        snapshot, source = valid_snapshot()
        changed_source = observed_source(content_summary="The abstract records a revised descriptive summary.")
        result = validate(snapshot, {source.observation_id: changed_source}, as_of="2026-09-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertEqual(ProblemStatus.STALE, result.status)
        self.assertEqual((StatusInvalidation.SOURCE_DIGEST_MISMATCH,), result.invalidations)

    def test_missing_certificate_is_unassessed_not_a_solved_claim(self) -> None:
        snapshot, source = valid_snapshot()
        no_certificate = ProblemDossierSnapshot(
            snapshot_id="DOSSIER-NO-CERTIFICATE",
            problem_id=snapshot.problem_id,
            version=2,
            statement=snapshot.statement,
            certificate=None,
            snapshot_at="2026-09-01T00:00:00+00:00",
        )
        result = no_certificate.validate({source.observation_id: source}, as_of="2026-09-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertEqual(ProblemStatus.UNASSESSED, result.status)
        self.assertEqual((), result.invalidations)

    def test_serializers_reject_unknown_fields_and_forged_digests(self) -> None:
        snapshot, _ = valid_snapshot()
        with self.assertRaises(ValueError):
            StatementVersion.from_dict({**snapshot.statement.to_dict(), "extra": True})
        with self.assertRaises(ValueError):
            OpenStatusCertificate.from_dict({**snapshot.certificate.to_dict(), "extra": True})  # type: ignore[union-attr]
        with self.assertRaises(ValueError):
            ProblemDossierSnapshot.from_dict({**snapshot.to_dict(), "extra": True})
        forged = snapshot.to_dict()
        forged["snapshot_digest_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            ProblemDossierSnapshot.from_dict(forged)

    def test_certificate_requires_sorted_unique_source_references(self) -> None:
        snapshot, source = valid_snapshot()
        reference = ObservationDigestRef.from_observation(source)
        with self.assertRaises(ValueError):
            OpenStatusCertificate(
                certificate_id="CERT-DUPLICATE",
                problem_id=snapshot.problem_id,
                version=2,
                statement_version_id=snapshot.statement.statement_version_id,
                statement_digest_sha256=snapshot.statement.statement_digest_sha256,
                source_observations=(reference, reference),
                status=ProblemStatus.OPEN_REPORTED,
                limitations=("A reported status is not a mathematical proof.",),
                reviewer="status reviewer",
                issued_at="2026-08-31T00:00:00+00:00",
                expires_at="2026-09-30T00:00:00+00:00",
            )

    def test_certificate_rejects_mutable_collections_and_bare_status_strings(self) -> None:
        snapshot, source = valid_snapshot()
        reference = ObservationDigestRef.from_observation(source)
        with self.assertRaises(TypeError):
            OpenStatusCertificate(
                certificate_id="CERT-MUTABLE",
                problem_id=snapshot.problem_id,
                version=2,
                statement_version_id=snapshot.statement.statement_version_id,
                statement_digest_sha256=snapshot.statement.statement_digest_sha256,
                source_observations=[reference],  # type: ignore[arg-type]
                status=ProblemStatus.OPEN_REPORTED,
                limitations=("Status report only.",),
                reviewer="status reviewer",
                issued_at="2026-08-31T00:00:00+00:00",
                expires_at="2026-09-30T00:00:00+00:00",
            )
        with self.assertRaises(TypeError):
            OpenStatusCertificate(
                certificate_id="CERT-BARE-STATUS",
                problem_id=snapshot.problem_id,
                version=2,
                statement_version_id=snapshot.statement.statement_version_id,
                statement_digest_sha256=snapshot.statement.statement_digest_sha256,
                source_observations=(reference,),
                status="OPEN_REPORTED",  # type: ignore[arg-type]
                limitations=("Status report only.",),
                reviewer="status reviewer",
                issued_at="2026-08-31T00:00:00+00:00",
                expires_at="2026-09-30T00:00:00+00:00",
            )

    def test_required_timestamps_reject_naive_values(self) -> None:
        snapshot, source = valid_snapshot()
        assert snapshot.certificate is not None
        with self.assertRaises(ValueError):
            OpenStatusCertificate(
                certificate_id="CERT-NAIVE",
                problem_id=snapshot.problem_id,
                version=2,
                statement_version_id=snapshot.statement.statement_version_id,
                statement_digest_sha256=snapshot.statement.statement_digest_sha256,
                source_observations=(ObservationDigestRef.from_observation(source),),
                status=ProblemStatus.OPEN_REPORTED,
                limitations=("Reported status requires independent mathematical review.",),
                reviewer="status reviewer",
                issued_at="2026-08-31T00:00:00",
                expires_at="2026-09-30T00:00:00+00:00",
            )
        with self.assertRaises(ValueError):
            ProblemDossierSnapshot(
                snapshot_id="DOSSIER-NAIVE",
                problem_id=snapshot.problem_id,
                version=2,
                statement=snapshot.statement,
                certificate=snapshot.certificate,
                snapshot_at="2026-08-31T00:00:00",
            )

    def test_validation_fails_closed_for_naive_or_malformed_timestamps(self) -> None:
        snapshot, source = valid_snapshot()
        naive_as_of = validate(
            snapshot,
            {source.observation_id: source},
            as_of="2026-09-01T00:00:00",
            artifacts=self.artifacts,
        )
        self.assertEqual(
            ProblemStatusValidation(ProblemStatus.STALE, (StatusInvalidation.INVALID_INPUT,)),
            naive_as_of,
        )

        mixed_source = observed_source(observed_at="2026-08-31T00:00:00")
        mixed = validate(
            snapshot,
            {mixed_source.observation_id: mixed_source},
            as_of="2026-09-01T00:00:00+00:00",
            artifacts=self.artifacts,
        )
        self.assertEqual(
            ProblemStatusValidation(ProblemStatus.STALE, (StatusInvalidation.INVALID_INPUT,)),
            mixed,
        )

        assert snapshot.certificate is not None
        object.__setattr__(snapshot.certificate, "expires_at", "not-a-timestamp")
        malformed = validate(
            snapshot,
            {source.observation_id: source},
            as_of="2026-09-01T00:00:00+00:00",
            artifacts=self.artifacts,
        )
        self.assertEqual(
            ProblemStatusValidation(ProblemStatus.STALE, (StatusInvalidation.INVALID_INPUT,)),
            malformed,
        )

    def test_validation_fails_closed_before_certificate_source_or_snapshot_exists(self) -> None:
        snapshot, source = valid_snapshot()
        assert snapshot.certificate is not None
        cases = (
            (
                "certificate",
                replace(
                    snapshot,
                    certificate=replace(
                        snapshot.certificate,
                        issued_at="2026-09-02T00:00:00+00:00",
                        expires_at="2026-10-02T00:00:00+00:00",
                    ),
                ),
                source,
                StatusInvalidation.CERTIFICATE_NOT_YET_ISSUED,
            ),
            (
                "source",
                replace(source, observed_at="2026-09-02T00:00:00+00:00"),
                None,
                StatusInvalidation.SOURCE_NOT_YET_OBSERVED,
            ),
            (
                "snapshot",
                replace(snapshot, snapshot_at="2026-09-02T00:00:00+00:00"),
                source,
                StatusInvalidation.SNAPSHOT_NOT_YET_CREATED,
            ),
        )
        for case, candidate, case_source, expected in cases:
            with self.subTest(case=case):
                if case == "source":
                    future_source = candidate
                    assert isinstance(future_source, SourceObservation)
                    candidate = replace(
                        snapshot,
                        certificate=replace(
                            snapshot.certificate,
                            source_observations=(ObservationDigestRef.from_observation(future_source),),
                        ),
                    )
                    case_source = future_source
                assert isinstance(candidate, ProblemDossierSnapshot)
                assert isinstance(case_source, SourceObservation)
                result = validate(
                    candidate,
                    {case_source.observation_id: case_source},
                    as_of="2026-09-01T00:00:00+00:00",
                    artifacts=self.artifacts,
                )
                self.assertEqual(ProblemStatus.STALE, result.status)
                expected_invalidations = (expected,)
                if case == "certificate":
                    expected_invalidations += (StatusInvalidation.SNAPSHOT_PREDATES_CERTIFICATE,)
                elif case == "source":
                    expected_invalidations += (StatusInvalidation.SOURCE_AFTER_CERTIFICATE_ISSUED,)
                self.assertEqual(expected_invalidations, result.invalidations)

    def test_artifact_backed_source_after_certificate_issued_fails_closed(self) -> None:
        snapshot, source = valid_snapshot()
        assert snapshot.certificate is not None
        late_source = replace(source, observed_at="2026-09-01T00:00:00+00:00")
        certificate = replace(
            snapshot.certificate,
            source_observations=(ObservationDigestRef.from_observation(late_source),),
        )
        candidate = replace(
            snapshot,
            certificate=certificate,
            snapshot_at="2026-09-02T00:00:00+00:00",
        )

        result = validate(
            candidate,
            {late_source.observation_id: late_source},
            as_of="2026-09-03T00:00:00+00:00",
            artifacts=self.artifacts,
        )

        self.assertEqual(ProblemStatus.STALE, result.status)
        self.assertEqual(
            (StatusInvalidation.SOURCE_AFTER_CERTIFICATE_ISSUED,),
            result.invalidations,
        )

    def test_artifact_backed_snapshot_predating_certificate_fails_closed(self) -> None:
        snapshot, source = valid_snapshot()
        assert snapshot.certificate is not None
        certificate = replace(
            snapshot.certificate,
            issued_at="2026-09-02T00:00:00+00:00",
            expires_at="2026-10-02T00:00:00+00:00",
        )
        candidate = replace(snapshot, certificate=certificate, snapshot_at="2026-09-01T00:00:00+00:00")

        result = validate(
            candidate,
            {source.observation_id: source},
            as_of="2026-09-03T00:00:00+00:00",
            artifacts=self.artifacts,
        )

        self.assertEqual(ProblemStatus.STALE, result.status)
        self.assertEqual(
            (StatusInvalidation.SNAPSHOT_PREDATES_CERTIFICATE,),
            result.invalidations,
        )

    def test_validation_invalidations_are_immutable_and_inputs_are_not_mutated(self) -> None:
        snapshot, source = valid_snapshot()
        observations = {source.observation_id: source}
        snapshot_before = snapshot.to_dict()
        observation_before = source.to_dict()
        result = validate(snapshot, observations, as_of="2026-10-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertIsInstance(result.invalidations, tuple)
        with self.assertRaises(TypeError):
            ProblemStatusValidation(ProblemStatus.STALE, [StatusInvalidation.INVALID_INPUT])  # type: ignore[arg-type]
        self.assertEqual(snapshot_before, snapshot.to_dict())
        self.assertEqual(observation_before, source.to_dict())
        self.assertEqual({source.observation_id: source}, observations)

    def test_missing_or_tampered_artifact_stales_a_report(self) -> None:
        snapshot, source = valid_snapshot()
        without_store = validate(snapshot, {source.observation_id: source}, as_of="2026-09-01T00:00:00+00:00")
        self.assertEqual(ProblemStatus.STALE, without_store.status)
        self.assertEqual((StatusInvalidation.SOURCE_ARTIFACT_INVALID,), without_store.invalidations)
        self.artifacts.path_for("ART-OPEN-1").write_bytes(b"tampered")
        tampered = validate(snapshot, {source.observation_id: source}, as_of="2026-09-01T00:00:00+00:00", artifacts=self.artifacts)
        self.assertEqual(ProblemStatus.STALE, tampered.status)
        self.assertEqual((StatusInvalidation.SOURCE_ARTIFACT_INVALID,), tampered.invalidations)

    def test_reported_resolved_and_contested_statuses_remain_distinct(self) -> None:
        snapshot, source = valid_snapshot()
        assert snapshot.certificate is not None
        for status in (ProblemStatus.RESOLVED_REPORTED, ProblemStatus.CONTESTED):
            certificate = OpenStatusCertificate(
                certificate_id=f"CERT-{status.value}",
                problem_id=snapshot.problem_id,
                version=2,
                statement_version_id=snapshot.statement.statement_version_id,
                statement_digest_sha256=snapshot.statement.statement_digest_sha256,
                source_observations=snapshot.certificate.source_observations,
                status=status,
                limitations=("Reported status requires independent mathematical review.",),
                reviewer="status reviewer",
                issued_at="2026-08-31T00:00:00+00:00",
                expires_at="2026-09-30T00:00:00+00:00",
            )
            report = ProblemDossierSnapshot(
                snapshot_id=f"DOSSIER-{status.value}",
                problem_id=snapshot.problem_id,
                version=2,
                statement=snapshot.statement,
                certificate=certificate,
                snapshot_at="2026-08-31T00:00:00+00:00",
            )
            self.assertEqual(status, report.validate({source.observation_id: source}, as_of="2026-09-01T00:00:00+00:00", artifacts=self.artifacts).status)

    def test_three_paper_dry_run_fixtures_pin_exact_status_facts(self) -> None:
        fixture_root = Path(__file__).parents[1] / "agents-results/2026-08-31/problem-intelligence-plane/evidence/s1-fixtures"
        fixtures = sorted(fixture_root.glob("*.json"))
        self.assertEqual(3, len(fixtures))
        payloads = {payload["problem_id"]: payload for payload in (json.loads(path.read_text(encoding="utf-8")) for path in fixtures)}
        self.assertEqual(
            {
                "P-FRANKL-Q6",
                "P-ARXIV-2601-22401-COLLISION",
                "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS",
            },
            set(payloads),
        )
        for path in fixtures:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("s1-paper-dry-run", payload["fixture_kind"])
            self.assertIn(
                ProblemStatus(payload["expected_report_status"]),
                {ProblemStatus.OPEN_REPORTED, ProblemStatus.RESOLVED_REPORTED, ProblemStatus.CONTESTED},
            )
            self.assertTrue(payload["problem_id"])
            self.assertGreaterEqual(payload["statement_version"], 1)
            self.assertTrue(payload["case_role"])
            self.assertTrue(payload["statement"])
            self.assertTrue(payload["source_assertions"])
            self.assertTrue(payload["limitations"])

        frankl_residual = payloads["P-FRANKL-Q6"]
        self.assertEqual("frankl-q6-constrained-residual", frankl_residual["case_role"])
        self.assertEqual(
            "Resolve the constrained q=6 outside-balance residual after the at-most-three-small-outside-parts cases; this target is not the global Frankl conjecture.",
            frankl_residual["statement"],
        )
        self.assertEqual(
            [
                {
                    "source_kind": "local-document",
                    "source_path": "docs/engineering-progress.md",
                    "assertion": "The remaining q=6 counterexample must contain at least four small outside parts; global Frankl remains open.",
                }
            ],
            frankl_residual["source_assertions"],
        )
        self.assertEqual(ProblemStatus.OPEN_REPORTED.value, frankl_residual["expected_report_status"])
        self.assertIn("not a claim about the global Frankl conjecture", frankl_residual["limitations"][0])
        engineering_progress = (Path(__file__).parents[1] / "docs/engineering-progress.md").read_text(encoding="utf-8")
        self.assertIn("Remaining q=6 counterexample must contain at least four small outside parts; global Frankl remains open", engineering_progress)

        collision = payloads["P-ARXIV-2601-22401-COLLISION"]
        self.assertEqual("database-open-literature-resolved-collision", collision["case_role"])
        self.assertEqual(ProblemStatus.RESOLVED_REPORTED.value, collision["expected_report_status"])
        self.assertEqual(
            [
                {
                    "source_kind": "database",
                    "asserted_status": "OPEN",
                    "assertion": "The database labels the selected control problem open.",
                },
                {
                    "source_kind": "literature",
                    "canonical_uri": "https://arxiv.org/abs/2601.22401",
                    "asserted_status": "RESOLVED",
                    "assertion": "arXiv:2601.22401 is the approved literature source for the database-open, literature-resolved control.",
                },
            ],
            collision["source_assertions"],
        )

        four_or_more = payloads["P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS"]
        self.assertEqual("frankl-q6-four-or-more-small-outside-parts-residual", four_or_more["case_role"])
        self.assertEqual(
            "In the same q=6 setup, classify admissible small-part hypergraphs of size at least four and prove the corresponding coarse balance is nonnegative, or output an exact negative configuration that survives the full trace constraints.",
            four_or_more["statement"],
        )
        self.assertEqual(
            [
                {
                    "source_kind": "local-document",
                    "source_path": "docs/frankl-q6-exactly-three-small-outside-parts.md",
                    "assertion": "The current proof does not cover four or more small outside parts; the next target is the stated at-least-four-small-parts residual.",
                }
            ],
            four_or_more["source_assertions"],
        )
        self.assertEqual(ProblemStatus.OPEN_REPORTED.value, four_or_more["expected_report_status"])
        self.assertNotEqual(frankl_residual["case_role"], four_or_more["case_role"])
        q6_residual_source = (Path(__file__).parents[1] / "docs/frankl-q6-exactly-three-small-outside-parts.md").read_text(encoding="utf-8")
        self.assertIn(f"> {four_or_more['statement']}", q6_residual_source)
        self.assertIn("No statement in this document upgrades the result to the general minimum-three-set case or to Frankl's conjecture.", q6_residual_source)


if __name__ == "__main__":
    unittest.main()
