"""Deterministic, non-authorizing route-ablation evaluation for R1 fixtures."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .schema import digest_json


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_ROUTES = (
    "FORWARD_CITATION",
    "ALIAS_AND_EQUIVALENCE",
    "STRUCTURAL_SEMANTIC",
    "REVIEW_AND_EXPERT_LEAD",
)
_CASE_IDS = (
    "P-FRANKL-Q6",
    "P-ARXIV-2601-22401-COLLISION",
    "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS",
)
_EXPECTED_STATUS_BY_CASE = {
    "P-FRANKL-Q6": "OPEN_REPORTED",
    "P-ARXIV-2601-22401-COLLISION": "RESOLVED_REPORTED",
    "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS": "OPEN_REPORTED",
}
_A4_EVIDENCE_ID = "EV-A4-ACCEPTED-1"
_A4_EVIDENCE_DIGEST = "85a3e6335bf8e5c886bef328e87f853c8eadc132a793b55ff39a962caae618dd"
_A4_SOURCE_HEAD = "46d924fbfc4daa00eb02d3ffaf06cb17a78be4fe"
_T2_FIXTURE_DIGEST = "475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c"
_FIXTURE_CONTENT_DIGEST = "be18b8bae4b359d0b55a10f6b5da95e541897cff677a1555ee9db659d8dd44e9"
_OUTCOMES = {"hit", "miss", "gap"}


class RegressionValidationError(ValueError):
    """Raised when a fixed R1 evaluation fixture violates its contract."""


def _fields(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown or missing:
        raise RegressionValidationError(f"{label} fields mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegressionValidationError(f"{label} must be non-empty text")
    return value


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise RegressionValidationError(f"{label} must be a SHA-256 digest")
    return value


def _git_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not _GIT_SHA.fullmatch(value):
        raise RegressionValidationError(f"{label} must be a Git object ID")
    return value


def _string_list(value: object, label: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise RegressionValidationError(f"{label} must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise RegressionValidationError(f"{label} must contain non-empty text")
    result = tuple(value)
    if len(result) != len(set(result)) or result != tuple(sorted(result)):
        raise RegressionValidationError(f"{label} must be unique and sorted")
    return result


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


@dataclass(frozen=True, slots=True)
class RouteResult:
    route: str
    query_scope: str
    queries: tuple[str, ...]
    source_ids: tuple[str, ...]
    hit_ids: tuple[str, ...]
    unresolved: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.route not in _ROUTES:
            raise RegressionValidationError("unsupported route")
        _text(self.query_scope, "query_scope")
        _string_list(list(self.queries), "queries")
        _string_list(list(self.source_ids), "source_ids")
        _string_list(list(self.hit_ids), "hits", allow_empty=True)
        _string_list(list(self.unresolved), "unresolved", allow_empty=True)

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "query_scope": self.query_scope,
            "queries": list(self.queries),
            "source_ids": list(self.source_ids),
            "hits": list(self.hit_ids),
            "unresolved": list(self.unresolved),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RouteResult":
        _fields(value, {"route", "query_scope", "queries", "source_ids", "hits", "unresolved"}, "route")
        return cls(
            route=_text(value["route"], "route"),
            query_scope=_text(value["query_scope"], "query_scope"),
            queries=_string_list(value["queries"], "queries"),
            source_ids=_string_list(value["source_ids"], "source_ids"),
            hit_ids=_string_list(value["hits"], "hits", allow_empty=True),
            unresolved=_string_list(value["unresolved"], "unresolved", allow_empty=True),
        )


@dataclass(frozen=True, slots=True)
class RegressionCase:
    case_id: str
    expected_status: str
    manual_minutes: float
    outcome_labels: tuple[str, ...]
    routes: tuple[RouteResult, ...]

    def __post_init__(self) -> None:
        if self.case_id not in _CASE_IDS:
            raise RegressionValidationError("unknown case_id")
        _text(self.expected_status, "expected_status")
        if self.expected_status != _EXPECTED_STATUS_BY_CASE[self.case_id]:
            raise RegressionValidationError("expected_status does not match the accepted A4 case")
        if not isinstance(self.manual_minutes, (int, float)) or isinstance(self.manual_minutes, bool):
            raise RegressionValidationError("manual_minutes must be numeric")
        if not math.isfinite(self.manual_minutes) or not 0 <= self.manual_minutes <= 240:
            raise RegressionValidationError("manual_minutes must be finite and within the R1 bound")
        if not self.outcome_labels or set(self.outcome_labels) - _OUTCOMES:
            raise RegressionValidationError("expected_outcomes must be drawn from hit, miss, gap")
        if tuple(sorted(self.outcome_labels)) != self.outcome_labels:
            raise RegressionValidationError("expected_outcomes must be sorted")
        if len(self.routes) != len(_ROUTES) or tuple(route.route for route in self.routes) != _ROUTES:
            raise RegressionValidationError("each case must retain exactly the four ordered routes")
        scopes = tuple(_normalized(route.query_scope) for route in self.routes)
        queries = tuple(_normalized(query) for route in self.routes for query in route.queries)
        source_ids = tuple(source_id for route in self.routes for source_id in route.source_ids)
        if (
            len(scopes) != len(set(scopes))
            or len(queries) != len(set(queries))
            or len(source_ids) != len(set(source_ids))
        ):
            raise RegressionValidationError("route scopes, queries, and sources must be independent")

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "expected_status": self.expected_status,
            "manual_minutes": self.manual_minutes,
            "expected_outcomes": list(self.outcome_labels),
            "routes": [route.to_dict() for route in self.routes],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RegressionCase":
        _fields(value, {"case_id", "expected_status", "manual_minutes", "expected_outcomes", "routes"}, "case")
        if not isinstance(value["routes"], list) or any(not isinstance(item, Mapping) for item in value["routes"]):
            raise RegressionValidationError("routes must be an array of objects")
        outcomes = _string_list(value["expected_outcomes"], "expected_outcomes")
        return cls(
            case_id=_text(value["case_id"], "case_id"),
            expected_status=_text(value["expected_status"], "expected_status"),
            manual_minutes=value["manual_minutes"],
            outcome_labels=outcomes,
            routes=tuple(RouteResult.from_dict(item) for item in value["routes"]),
        )


@dataclass(frozen=True, slots=True)
class RouteAblation:
    route: str
    incremental_hits: tuple[str, ...]
    leave_one_out_loss: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    case_id: str
    full_hit_ids: tuple[str, ...]
    outcome_labels: tuple[str, ...]
    manual_minutes: float
    routes: tuple[RouteAblation, ...]

    @property
    def route_names(self) -> tuple[str, ...]:
        return tuple(item.route for item in self.routes)


@dataclass(frozen=True, slots=True)
class RegressionEvaluation:
    case_ids: tuple[str, ...]
    cases: tuple[CaseEvaluation, ...]

    @property
    def digest_sha256(self) -> str:
        return digest_json({
            "case_ids": list(self.case_ids),
            "cases": [
                {
                    "case_id": case.case_id,
                    "full_hit_ids": list(case.full_hit_ids),
                    "outcome_labels": list(case.outcome_labels),
                    "manual_minutes": case.manual_minutes,
                    "routes": [
                        {
                            "route": route.route,
                            "incremental_hits": list(route.incremental_hits),
                            "leave_one_out_loss": list(route.leave_one_out_loss),
                        }
                        for route in case.routes
                    ],
                }
                for case in self.cases
            ],
        })

    def case_by_id(self, case_id: str) -> CaseEvaluation:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise RegressionValidationError("unknown evaluated case")


@dataclass(frozen=True, slots=True)
class RegressionSuite:
    topic_id: str
    a4_evidence_id: str
    a4_evidence_digest: str
    a4_source_head: str
    t2_fixture_sha256: str
    cases: tuple[RegressionCase, ...]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RegressionSuite":
        _fields(value, {
            "fixture_kind", "schema_version", "topic_id", "a4_evidence_id", "a4_evidence_digest",
            "a4_source_head", "t2_fixture_sha256", "fixture_content_sha256", "route_order", "case_ids", "cases",
        }, "suite")
        if value["fixture_kind"] != "r1-four-route-regression" or value["schema_version"] != "1.0":
            raise RegressionValidationError("unsupported regression fixture")
        if value["route_order"] != list(_ROUTES):
            raise RegressionValidationError("route_order must match the R1 contract")
        if value["case_ids"] != list(_CASE_IDS):
            raise RegressionValidationError("case_ids must match the accepted A4 archive order")
        if not isinstance(value["cases"], list) or any(not isinstance(item, Mapping) for item in value["cases"]):
            raise RegressionValidationError("cases must be an array of objects")
        cases = tuple(RegressionCase.from_dict(item) for item in value["cases"])
        if tuple(case.case_id for case in cases) != _CASE_IDS:
            raise RegressionValidationError("cases must match the accepted A4 archive order")
        declared_content_digest = _sha(value["fixture_content_sha256"], "fixture_content_sha256")
        content = dict(value)
        content.pop("fixture_content_sha256")
        if (
            declared_content_digest != _FIXTURE_CONTENT_DIGEST
            or digest_json(content) != declared_content_digest
        ):
            raise RegressionValidationError("fixed regression fixture content drift")
        suite = cls(
            topic_id=_text(value["topic_id"], "topic_id"),
            a4_evidence_id=_text(value["a4_evidence_id"], "a4_evidence_id"),
            a4_evidence_digest=_sha(value["a4_evidence_digest"], "a4_evidence_digest"),
            a4_source_head=_git_sha(value["a4_source_head"], "a4_source_head"),
            t2_fixture_sha256=_sha(value["t2_fixture_sha256"], "t2_fixture_sha256"),
            cases=cases,
        )
        if (
            suite.topic_id != "union-closed"
            or
            suite.a4_evidence_id != _A4_EVIDENCE_ID
            or suite.a4_evidence_digest != _A4_EVIDENCE_DIGEST
            or suite.a4_source_head != _A4_SOURCE_HEAD
            or suite.t2_fixture_sha256 != _T2_FIXTURE_DIGEST
        ):
            raise RegressionValidationError("accepted A4, T2, or topic identity drift")
        source_ids = tuple(
            source_id
            for case in cases
            for route in case.routes
            for source_id in route.source_ids
        )
        if len(source_ids) != len(set(source_ids)):
            raise RegressionValidationError("route source identities must be unique across the R1 fixture")
        return suite

    def evaluate(self) -> RegressionEvaluation:
        evaluated: list[CaseEvaluation] = []
        for case in self.cases:
            route_sets = tuple(set(route.hit_ids) for route in case.routes)
            full = set().union(*route_sets)
            ablations = []
            for index, route in enumerate(case.routes):
                without = set().union(*(route_sets[:index] + route_sets[index + 1:]))
                incremental = tuple(sorted(route_sets[index] - without))
                ablations.append(RouteAblation(route.route, incremental, tuple(sorted(full - without))))
            evaluated.append(CaseEvaluation(
                case_id=case.case_id,
                full_hit_ids=tuple(sorted(full)),
                outcome_labels=case.outcome_labels,
                manual_minutes=float(case.manual_minutes),
                routes=tuple(ablations),
            ))
        return RegressionEvaluation(_CASE_IDS, tuple(evaluated))
