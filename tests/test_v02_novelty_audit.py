from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from matharc.v02.novelty_audit import (
    CandidateResult,
    HumanAuditEntry,
    HumanAuditVerdict,
    NoveltyAuditRecord,
    NoveltyAuditStatus,
    NoveltyAuditPurpose,
    NoveltyConclusion,
    NoveltyInvalidation,
    SearchHit,
    SearchRoute,
    SearchRouteResult,
    SourceSupport,
    authorize,
)
from matharc.v02.artifact_store import ArtifactStore
from matharc.v02.source_observation import LicenseStatus, ObservationStatus, SourceObservation


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source(source_id: str) -> SourceSupport:
    return SourceSupport(
        source_id=source_id,
        canonical_uri=f"https://example.test/{source_id}",
        pinned_version="v1",
        locator="section 2, theorem statement",
        source_fingerprint_sha256=digest(source_id),
    )


def candidate() -> CandidateResult:
    return CandidateResult(
        candidate_id="CAND-FRANKL-Q6-1",
        candidate_fingerprint_sha256=digest("candidate result"),
        scope="The constrained q=6 outside-balance residual only.",
        version="draft-1",
        source_support=(source("candidate-draft"),),
    )


def route_result(route: SearchRoute, *, completed: bool = True) -> SearchRouteResult:
    hits = ()
    if route is SearchRoute.FORWARD_CITATION:
        hits = (
            SearchHit(
                hit_id="HIT-FORWARD-1",
                result_fingerprint_sha256=digest("forward hit"),
                scope="A related finite-universe verification, not the candidate scope.",
                version="v2",
                source_support=(source("forward-hit"),),
            ),
        )
    return SearchRouteResult(
        route=route,
        query_scope=f"Route-specific scope for {route.value}.",
        queries=(f"query {route.value}",),
        hits=hits,
        unresolved_items=("Await the human comparison of the scoped hit.",) if not completed else (),
        searched_at="2026-08-31T08:00:00+00:00",
        completed=completed,
    )


def all_routes(*, completed: bool = True) -> tuple[SearchRouteResult, ...]:
    return tuple(route_result(SearchRoute(value), completed=completed) for value in (
        "FORWARD_CITATION",
        "ALIAS_AND_EQUIVALENCE",
        "STRUCTURAL_SEMANTIC",
        "REVIEW_AND_EXPERT_LEAD",
    ))


def audited_record() -> NoveltyAuditRecord:
    return NoveltyAuditRecord(
        audit_id="NOVELTY-Q6-1",
        candidate=candidate(),
        route_results=all_routes(),
        conclusion=NoveltyConclusion.NO_PRIOR_RESULT_FOUND,
        human_audit=HumanAuditEntry(
            reviewer_id="literature-auditor-1",
            reviewed_at="2026-08-31T09:00:00+00:00",
            verdict=HumanAuditVerdict.APPROVED,
            conclusion=NoveltyConclusion.NO_PRIOR_RESULT_FOUND,
            rationale="All four route records were compared against the candidate's constrained scope.",
        ),
        created_at="2026-08-31T07:00:00+00:00",
        sealed_at="2026-08-31T10:00:00+00:00",
    )


def source_evidence(
    record: NoveltyAuditRecord,
    artifacts: ArtifactStore,
    *,
    source_bytes: dict[str, bytes] | None = None,
) -> dict[str, SourceObservation]:
    supports = [*record.candidate.source_support]
    supports.extend(support for route in record.route_results for hit in route.hits for support in hit.source_support)
    observations: dict[str, SourceObservation] = {}
    for support in supports:
        content = (source_bytes or {}).get(support.source_id, support.source_id.encode("utf-8"))
        artifact = artifacts.put_bytes(
            f"ART-{support.source_id}",
            content,
            logical_role="literature-observation",
            producer="matharc-literature-base",
            media_type="text/plain",
        )
        observations[support.source_id] = SourceObservation(
            observation_id=support.source_id,
            canonical_uri=support.canonical_uri,
            pinned_version=support.pinned_version,
            observed_at="2026-08-31T06:00:00+00:00",
            license_status=LicenseStatus.OPEN,
            license_basis="fixture license record",
            content_summary="A pinned literature source used by the fixture.",
            summary_basis="fixture metadata",
            media_type="text/plain",
            content_digest_sha256=hashlib.sha256(content).hexdigest(),
            artifact_id=artifact.artifact_id,
            status=ObservationStatus.OBSERVED,
        )
    return observations


class NoveltyAuditTests(unittest.TestCase):
    def test_complete_four_route_human_audit_round_trips_with_stable_digest(self) -> None:
        record = audited_record()
        restored = NoveltyAuditRecord.from_dict(record.to_dict())
        self.assertEqual(record, restored)
        self.assertEqual(record.audit_digest_sha256, restored.audit_digest_sha256)
        with tempfile.TemporaryDirectory() as directory:
            artifacts = ArtifactStore(directory)
            authorization = authorize(restored, observations=source_evidence(restored, artifacts), artifacts=artifacts)
            self.assertEqual(NoveltyAuditStatus.AUDITED, authorization.status)
            self.assertTrue(authorization.allows_complete_budget)
            self.assertTrue(authorization.allows_public_qualitative_conclusion)

    def test_missing_route_or_human_audit_fail_closed(self) -> None:
        record = NoveltyAuditRecord(
            audit_id="NOVELTY-PENDING-1",
            candidate=candidate(),
            route_results=all_routes()[:-1],
            created_at="2026-08-31T07:00:00+00:00",
            sealed_at="2026-08-31T10:00:00+00:00",
        )
        authorization = record.authorization()
        self.assertEqual(NoveltyAuditStatus.PENDING_HUMAN_AUDIT, authorization.status)
        self.assertFalse(authorization.complete_research_budget)
        self.assertFalse(authorization.public_qualitative_conclusion)
        self.assertIn(NoveltyInvalidation.MISSING_ROUTE, authorization.invalidations)
        self.assertIn(NoveltyInvalidation.MISSING_HUMAN_AUDIT, authorization.invalidations)
        self.assertIn(NoveltyInvalidation.UNASSESSED_CONCLUSION, authorization.invalidations)

    def test_incomplete_route_and_rejected_human_audit_cannot_grant_permissions(self) -> None:
        record = NoveltyAuditRecord(
            audit_id="NOVELTY-PENDING-2",
            candidate=candidate(),
            route_results=all_routes(completed=False),
            conclusion=NoveltyConclusion.INCONCLUSIVE,
            human_audit=HumanAuditEntry(
                reviewer_id="literature-auditor-1",
                reviewed_at="2026-08-31T09:00:00+00:00",
                verdict=HumanAuditVerdict.NEEDS_FOLLOW_UP,
                conclusion=NoveltyConclusion.INCONCLUSIVE,
                rationale="Search coverage requires follow-up.",
            ),
            created_at="2026-08-31T07:00:00+00:00",
            sealed_at="2026-08-31T10:00:00+00:00",
        )
        authorization = authorize(record)
        self.assertFalse(authorization.allows_complete_budget)
        self.assertFalse(authorization.allows_public_qualitative_conclusion)
        self.assertIn(NoveltyInvalidation.INCOMPLETE_ROUTE, authorization.invalidations)
        self.assertIn(NoveltyInvalidation.HUMAN_AUDIT_NOT_APPROVED, authorization.invalidations)

    def test_unreviewed_prior_result_conclusion_cannot_grant_budget_or_public_conclusion(self) -> None:
        record = NoveltyAuditRecord(
            audit_id="NOVELTY-UNREVIEWED-RESOLUTION",
            candidate=candidate(),
            route_results=all_routes(),
            conclusion=NoveltyConclusion.PRIOR_RESULT_FOUND,
            created_at="2026-08-31T07:00:00+00:00",
            sealed_at="2026-08-31T10:00:00+00:00",
        )
        authorization = record.authorization()
        self.assertEqual(NoveltyAuditStatus.PENDING_HUMAN_AUDIT, authorization.status)
        self.assertFalse(authorization.allows_complete_budget)
        self.assertFalse(authorization.allows_public_qualitative_conclusion)
        self.assertEqual((NoveltyInvalidation.MISSING_HUMAN_AUDIT,), authorization.invalidations)

    def test_candidate_requires_fingerprint_scope_version_and_source_support(self) -> None:
        with self.assertRaises(ValueError):
            CandidateResult(
                candidate_id="CANDIDATE",
                candidate_fingerprint_sha256=digest("candidate"),
                scope="scope",
                version="v1",
                source_support=(),
            )
        with self.assertRaises(ValueError):
            SearchHit(
                hit_id="HIT",
                result_fingerprint_sha256="not-a-digest",
                scope="scope",
                version="v1",
                source_support=(source("hit"),),
            )

    def test_four_routes_are_separate_and_duplicate_routes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NoveltyAuditRecord(
                audit_id="NOVELTY-DUPLICATE",
                candidate=candidate(),
                route_results=(route_result(SearchRoute.FORWARD_CITATION), route_result(SearchRoute.FORWARD_CITATION)),
                created_at="2026-08-31T07:00:00+00:00",
                sealed_at="2026-08-31T10:00:00+00:00",
            )
        self.assertEqual(
            set(SearchRoute),
            {result.route for result in all_routes()},
        )

    def test_duplicate_route_queries_or_cross_route_sources_are_rejected(self) -> None:
        routes = list(all_routes())
        routes[1] = SearchRouteResult(
            route=SearchRoute.ALIAS_AND_EQUIVALENCE,
            query_scope=routes[0].query_scope,
            queries=routes[0].queries,
            hits=(),
            unresolved_items=(),
            searched_at="2026-08-31T08:00:00+00:00",
            completed=True,
        )
        with self.assertRaisesRegex(ValueError, "independent"):
            NoveltyAuditRecord(
                audit_id="NOVELTY-COPIED-QUERY",
                candidate=candidate(),
                route_results=tuple(routes),
                created_at="2026-08-31T07:00:00+00:00",
                sealed_at="2026-08-31T10:00:00+00:00",
            )

    def test_cross_route_source_alias_with_real_observation_and_artifact_cannot_authorize(self) -> None:
        record = audited_record()
        routes = list(record.route_results)
        alias = SourceSupport(
            source_id="forward-hit-alias",
            canonical_uri="HTTPS://EXAMPLE.TEST/FORWARD-HIT/",
            pinned_version="v1",
            locator="a different local identifier for the same pinned source",
            source_fingerprint_sha256=digest("forward-hit"),
        )
        routes[1] = SearchRouteResult(
            route=SearchRoute.ALIAS_AND_EQUIVALENCE,
            query_scope=routes[1].query_scope,
            queries=routes[1].queries,
            hits=(SearchHit(
                hit_id="HIT-ALIAS-SOURCE",
                result_fingerprint_sha256=digest("alias-source-hit"),
                scope="A route-specific hit that is falsely backed by the same source.",
                version="v1",
                source_support=(alias,),
            ),),
            unresolved_items=(),
            searched_at="2026-08-31T08:00:00+00:00",
            completed=True,
        )
        object.__setattr__(record, "route_results", tuple(routes))
        with tempfile.TemporaryDirectory() as directory:
            artifacts = ArtifactStore(directory)
            observations = source_evidence(
                record,
                artifacts,
                source_bytes={"forward-hit-alias": b"forward-hit"},
            )
            alias_observation = observations["forward-hit-alias"]
            self.assertEqual(ObservationStatus.OBSERVED, alias_observation.status)
            self.assertEqual(LicenseStatus.OPEN, alias_observation.license_status)
            self.assertEqual(digest("forward-hit"), alias_observation.content_digest_sha256)
            self.assertEqual(digest("forward-hit"), artifacts.get(alias_observation.artifact_id or "").sha256)
            authorization = record.authorization(observations=observations, artifacts=artifacts)
        self.assertEqual(NoveltyAuditStatus.STALE, authorization.status)
        self.assertFalse(authorization.allows_complete_budget)
        self.assertFalse(authorization.allows_public_qualitative_conclusion)
        self.assertEqual((NoveltyInvalidation.ROUTE_NOT_INDEPENDENT,), authorization.invalidations)
        routes = list(all_routes())
        routes[1] = SearchRouteResult(
            route=SearchRoute.ALIAS_AND_EQUIVALENCE,
            query_scope=routes[1].query_scope,
            queries=routes[1].queries,
            hits=(SearchHit(
                hit_id="HIT-COPIED-SOURCE",
                result_fingerprint_sha256=digest("copied source"),
                scope="A separately described hit with copied source support.",
                version="v1",
                source_support=(source("forward-hit"),),
            ),),
            unresolved_items=(),
            searched_at="2026-08-31T08:00:00+00:00",
            completed=True,
        )
        with self.assertRaisesRegex(ValueError, "independent"):
            NoveltyAuditRecord(
                audit_id="NOVELTY-COPIED-SOURCE",
                candidate=candidate(),
                route_results=tuple(routes),
                created_at="2026-08-31T07:00:00+00:00",
                sealed_at="2026-08-31T10:00:00+00:00",
            )

    def test_serializers_reject_unknown_fields_forged_digests_and_non_array_collections(self) -> None:
        record = audited_record()
        with self.assertRaises(ValueError):
            NoveltyAuditRecord.from_dict({**record.to_dict(), "extra": True})
        forged = copy.deepcopy(record.to_dict())
        forged["audit_digest_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            NoveltyAuditRecord.from_dict(forged)
        bad_routes = copy.deepcopy(record.to_dict())
        bad_routes["route_results"] = {"not": "an array"}
        with self.assertRaises(ValueError):
            NoveltyAuditRecord.from_dict(bad_routes)
        reversed_routes = copy.deepcopy(record.to_dict())
        reversed_routes["route_results"] = list(reversed(reversed_routes["route_results"]))
        with self.assertRaises(ValueError):
            NoveltyAuditRecord.from_dict(reversed_routes)

    def test_records_are_immutable_and_do_not_depend_on_claim_or_trace_models(self) -> None:
        record = audited_record()
        with self.assertRaises(FrozenInstanceError):
            record.conclusion = NoveltyConclusion.PRIOR_RESULT_FOUND  # type: ignore[misc]
        self.assertNotIn("ClaimStatus", __import__("matharc.v02.novelty_audit", fromlist=["*"]).__dict__)
        self.assertNotIn("ResearchTrace", __import__("matharc.v02.novelty_audit", fromlist=["*"]).__dict__)

    def test_missing_or_tampered_source_observation_artifact_cannot_grant_permissions(self) -> None:
        record = audited_record()
        self.assertEqual(NoveltyAuditStatus.PENDING_SOURCE_VERIFICATION, record.authorization().status)
        with tempfile.TemporaryDirectory() as directory:
            artifacts = ArtifactStore(directory)
            observations = source_evidence(record, artifacts)
            artifacts.path_for("ART-forward-hit").write_bytes(b"tampered")
            authorization = record.authorization(observations=observations, artifacts=artifacts)
            self.assertEqual(NoveltyAuditStatus.PENDING_SOURCE_VERIFICATION, authorization.status)
            self.assertFalse(authorization.allows_complete_budget)
            self.assertFalse(authorization.allows_public_qualitative_conclusion)
            self.assertEqual((NoveltyInvalidation.SOURCE_SUPPORT_NOT_VERIFIED,), authorization.invalidations)

    def test_future_observation_with_intact_artifact_cannot_authorize_candidate_or_hit_support(self) -> None:
        record = audited_record()
        for source_id in ("candidate-draft", "forward-hit"):
            with self.subTest(source_id=source_id), tempfile.TemporaryDirectory() as directory:
                artifacts = ArtifactStore(directory)
                observations = source_evidence(record, artifacts)
                observation = observations[source_id]
                observations[source_id] = SourceObservation.from_dict(
                    {**observation.to_dict(), "observed_at": "2026-08-31T08:00:01+00:00"}
                )
                self.assertTrue(artifacts.verify()["valid"])
                authorization = record.authorization(observations=observations, artifacts=artifacts)
                self.assertEqual(NoveltyAuditStatus.PENDING_SOURCE_VERIFICATION, authorization.status)
                self.assertFalse(authorization.allows_complete_budget)
                self.assertFalse(authorization.allows_public_qualitative_conclusion)
                self.assertEqual((NoveltyInvalidation.SOURCE_SUPPORT_NOT_VERIFIED,), authorization.invalidations)

    def test_naive_observation_timestamp_with_intact_artifact_cannot_authorize(self) -> None:
        record = audited_record()
        with tempfile.TemporaryDirectory() as directory:
            artifacts = ArtifactStore(directory)
            observations = source_evidence(record, artifacts)
            observation = observations["candidate-draft"]
            observations["candidate-draft"] = SourceObservation.from_dict(
                {**observation.to_dict(), "observed_at": "2026-08-31T07:00:00"}
            )
            self.assertTrue(artifacts.verify()["valid"])
            authorization = record.authorization(observations=observations, artifacts=artifacts)
        self.assertEqual(NoveltyAuditStatus.PENDING_SOURCE_VERIFICATION, authorization.status)
        self.assertFalse(authorization.allows_complete_budget)
        self.assertFalse(authorization.allows_public_qualitative_conclusion)
        self.assertEqual((NoveltyInvalidation.SOURCE_SUPPORT_NOT_VERIFIED,), authorization.invalidations)

    def test_review_and_sealing_must_follow_each_route_search(self) -> None:
        record = audited_record()
        assert record.human_audit is not None
        object.__setattr__(record.human_audit, "reviewed_at", "2026-08-31T07:30:00+00:00")
        authorization = record.authorization()
        self.assertEqual(NoveltyAuditStatus.STALE, authorization.status)
        self.assertEqual((NoveltyInvalidation.TEMPORAL_ORDER_VIOLATION,), authorization.invalidations)
        with self.assertRaisesRegex(ValueError, "chronologically ordered"):
            NoveltyAuditRecord(
                audit_id="NOVELTY-EARLY-SEAL",
                candidate=candidate(),
                route_results=all_routes(),
                conclusion=NoveltyConclusion.NO_PRIOR_RESULT_FOUND,
                human_audit=HumanAuditEntry(
                    reviewer_id="literature-auditor-1",
                    reviewed_at="2026-08-31T09:00:00+00:00",
                    verdict=HumanAuditVerdict.APPROVED,
                    conclusion=NoveltyConclusion.NO_PRIOR_RESULT_FOUND,
                    rationale="The time-order negative test must fail.",
                ),
                created_at="2026-08-31T07:00:00+00:00",
                sealed_at="2026-08-31T08:30:00+00:00",
            )

    def test_s2_fixture_records_each_route_and_requires_scope_limited_human_audit(self) -> None:
        fixture = Path(__file__).parents[1] / "agents-results/2026-08-31/problem-intelligence-plane/evidence/s2-fixtures/q6-candidate-audit.json"
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual("s2-novelty-audit-fixture", payload["fixture_kind"])
        record = NoveltyAuditRecord.from_dict(payload["record"])
        self.assertEqual(set(SearchRoute), {item.route for item in record.route_results})
        self.assertEqual(NoveltyAuditPurpose.CONTRACT_FIXTURE, record.purpose)
        with tempfile.TemporaryDirectory() as directory:
            artifacts = ArtifactStore(directory)
            authorization = record.authorization(
                observations=source_evidence(record, artifacts),
                artifacts=artifacts,
            )
        self.assertEqual(NoveltyAuditStatus.CONTRACT_ONLY, authorization.status)
        self.assertFalse(authorization.allows_complete_budget)
        self.assertFalse(authorization.allows_public_qualitative_conclusion)
        self.assertEqual((NoveltyInvalidation.CONTRACT_ONLY_RECORD,), authorization.invalidations)
