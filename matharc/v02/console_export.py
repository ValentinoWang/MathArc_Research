"""Versioned, read-only payloads for the zero-build research console."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from matharc.operations import OperationsDomainStore

from .authorization import RolePolicy
from .console_topic import TopicStoreConfig, console_topic_projection
from .difficulty_ledger import DifficultyLedger
from .exploration_session import ExplorationSessionStore
from .falsification import get_kill_test_spec, iter_route_evaluations
from .novelty_audit import NoveltyAuditRecord
from .problem_gates import ProblemGateStore
from .review import ReviewRecord
from .topic_portfolio import TopicPortfolioStore
from .topic_observation import TopicObservationRunner
from .schema import canonical_json
from .workspace import ResearchWorkspace
from .workspace_index import WorkspaceIndex
from .workspace_visualization import workspace_dashboard_payload

_SCHEMA_VERSION = "1.0"
_CAMPAIGN_KEYS = frozenset({"rounds", "stop_reason", "final_metrics", "budget", "creation_log"})
_CAMPAIGN_OPTIONAL_KEYS = frozenset({"spawn_log"})
_REVIEW_RECORDS_KEY = "v03_review_records"
_PROMOTION_EVENT_TYPES = frozenset({"CLAIM_PROMOTED", "CLAIM_PROMOTION_REJECTED"})


@dataclass(frozen=True, slots=True)
class ConsoleLocalProjectionConfig:
    """Explicit read-only locations for locally completed console capabilities."""

    workspace_index_root: Path | None = None
    exploration_session_root: Path | None = None
    topic_portfolio_root: Path | None = None
    problem_gate_root: Path | None = None
    difficulty_ledger_root: Path | None = None
    operations_domain_root: Path | None = None
    novelty_audit_path: Path | None = None

    def projection(self, workspace_provenance: Mapping[str, str]) -> dict[str, Any]:
        result: dict[str, Any] = {
            "workspace_index": {"state": "not_configured"},
            "exploration_sessions": {"state": "not_configured"},
            "topic_portfolio": {"state": "not_configured"},
            "candidate_problems": {"state": "not_configured"},
            "difficulty_ledger": {"state": "not_configured"},
            "operations": {"state": "not_configured"},
            "novelty_audit": {"state": "not_configured"},
        }
        if self.workspace_index_root is not None:
            result["workspace_index"] = {
                "state": "live",
                **WorkspaceIndex.scan(self.workspace_index_root).console_dict(),
            }
        if self.exploration_session_root is not None:
            current_sessions = []
            stale_sessions = []
            for session in ExplorationSessionStore(str(self.exploration_session_root)).list():
                if dict(session.workspace_provenance) == dict(workspace_provenance):
                    current_sessions.append(session.to_dict())
                else:
                    stale_sessions.append(
                        {
                            "session_id": session.session_id,
                            "reason": "workspace_provenance_mismatch",
                        }
                    )
            result["exploration_sessions"] = {
                "state": "live" if not stale_sessions else "live_with_stale_records",
                "sessions": current_sessions,
                "stale_sessions": stale_sessions,
            }
        if self.topic_portfolio_root is not None:
            result["topic_portfolio"] = {"state": "live", **TopicPortfolioStore(str(self.topic_portfolio_root)).load().to_dict()}
        if self.problem_gate_root is not None:
            statements, candidates, graph = ProblemGateStore(str(self.problem_gate_root)).load()
            result["candidate_problems"] = {"state": "live", "statements": [item.to_dict() for item in statements], "candidates": [item.to_dict() for item in candidates], "graph": graph.to_dict()}
        if self.difficulty_ledger_root is not None:
            ledger = DifficultyLedger(str(self.difficulty_ledger_root))
            predictions, outcomes = ledger.records()
            result["difficulty_ledger"] = {"state": "live", "predictions": [item.to_dict() for item in predictions], "outcomes": [item.to_dict() for item in outcomes], "summary": ledger.summary().to_dict()}
        if self.operations_domain_root is not None:
            result["operations"] = {"state": "live", **OperationsDomainStore(self.operations_domain_root).snapshot()}
        if self.novelty_audit_path is not None:
            path = self.novelty_audit_path.resolve()
            if not path.is_file():
                raise ValueError("configured novelty audit record is missing")
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, Mapping) and "record" in payload:
                    payload = payload["record"]
                record = NoveltyAuditRecord.from_dict(payload)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError("configured novelty audit record is invalid") from exc
            authorization = record.authorization()
            result["novelty_audit"] = {
                "state": "live",
                "schema_version": "1.0",
                "provenance": dict(workspace_provenance),
                "audit": record.to_dict(),
                "authorization": {
                    "status": authorization.status.value,
                    "complete_research_budget": authorization.complete_research_budget,
                    "public_qualitative_conclusion": authorization.public_qualitative_conclusion,
                    "invalidations": [item.value for item in authorization.invalidations],
                },
                "decision_boundary": (
                    "This projection reports a persisted novelty-audit record only; "
                    "it does not infer mathematical correctness or public priority."
                ),
            }
        return result


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _workspace_provenance(workspace: ResearchWorkspace) -> dict[str, str]:
    return {
        "run_id": workspace.trace.run_id,
        "state_digest_sha256": workspace.state_digest(),
        "event_head_hash": workspace.events.head_hash,
    }


def console_routes_projection(
    workspace: ResearchWorkspace,
    workspace_provenance: Mapping[str, str],
) -> dict[str, Any]:
    """Project only route records owned by the current research workspace.

    A route's prose kill-test is a v0.2 field.  Structured kill-test specs and
    evaluations are optional v0.3 records, so an absent spec remains absent
    instead of being replaced by a fabricated execution result or topology.
    """

    evaluations = iter_route_evaluations(workspace.trace)
    known_route_ids = set(workspace.trace.routes)
    unknown_evaluations = sorted(
        {item.route_id for item in evaluations if item.route_id not in known_route_ids}
    )
    if unknown_evaluations:
        raise ValueError(
            f"route evaluation records reference unknown routes: {unknown_evaluations}"
        )
    by_route: dict[str, list[dict[str, Any]]] = {route_id: [] for route_id in known_route_ids}
    for item in evaluations:
        by_route[item.route_id].append(item.to_dict())

    routes: list[dict[str, Any]] = []
    for route_id in sorted(workspace.trace.routes):
        route = workspace.trace.routes[route_id]
        spec = get_kill_test_spec(workspace.trace, route_id)
        routes.append(
            {
                **route.to_dict(),
                "kill_test_spec": spec.to_dict() if spec is not None else None,
                "kill_test_spec_digest_sha256": (
                    spec.digest_sha256 if spec is not None else None
                ),
                "evaluations": by_route[route_id],
            }
        )
    return {
        "schema_version": _SCHEMA_VERSION,
        "state": "live",
        "provenance": dict(workspace_provenance),
        "routes": routes,
    }


def _review_records(workspace: ResearchWorkspace) -> tuple[ReviewRecord, ...]:
    raw_records = workspace.trace.metadata.get(_REVIEW_RECORDS_KEY, [])
    if not isinstance(raw_records, list):
        raise ValueError("review record metadata store is malformed")
    records: list[ReviewRecord] = []
    for raw in raw_records:
        if not isinstance(raw, Mapping):
            raise ValueError("review record entry must be an object")
        records.append(ReviewRecord.from_dict(raw))
    return tuple(records)


def console_disclosure_projection(
    workspace: ResearchWorkspace,
    workspace_provenance: Mapping[str, str],
) -> dict[str, Any]:
    """Build a conservative wording matrix from persisted records only.

    The matrix reports what records can be described, not what those records
    prove.  In particular, promotion events are never turned into public
    authorization, novelty, or open/resolved claims by this projection.
    """

    trace = workspace.trace
    state_records = [trace.claims[key].to_dict() for key in sorted(trace.claims)]
    evidence_records = [trace.evidence[key].to_dict() for key in sorted(trace.evidence)]
    current_reviews = []
    for review in _review_records(workspace):
        claim = trace.claims.get(review.claim_id)
        if (
            claim is not None
            and review.claim_revision == claim.revision
            and review.lifecycle_status.value == "ACTIVE"
        ):
            current_reviews.append(review.to_dict())
    promotion_records = [
        event.to_dict()
        for event in workspace.events.events
        if event.event_type in _PROMOTION_EVENT_TYPES
    ]

    forbidden = [
        "不得说已证明或证明完成。",
        "不得说结果新颖、首个结果或首次发现。",
        "不得说问题开放、已解决或已被解决。",
        "不得说已获得公开授权、公共认可或可以直接对外发布。",
    ]
    levels = [
        {
            "level": 1,
            "key": "internal_state",
            "state": "available",
            "basis": {
                "record_type": "current_state",
                "record_ids": [item["claim_id"] for item in state_records],
            },
            "allowed": [
                f"可说：工作区记录了 {len(state_records)} 条当前命题状态和 "
                f"{len(trace.routes)} 条路线状态。"
            ],
            "forbidden": forbidden.copy(),
        },
        {
            "level": 2,
            "key": "evidence_record",
            "state": "available" if evidence_records else "unavailable",
            "basis": {
                "record_type": "evidence",
                "record_ids": [item["evidence_id"] for item in evidence_records],
            },
            "allowed": [
                (
                    f"可说：记录列出了 {len(evidence_records)} 条证据及其类型、摘要和限制。"
                    if evidence_records
                    else "可说：当前没有证据记录可供描述。"
                )
            ],
            "forbidden": forbidden.copy(),
        },
        {
            "level": 3,
            "key": "review_record",
            "state": "available" if current_reviews else "unavailable",
            "basis": {
                "record_type": "review",
                "record_ids": [item["review_id"] for item in current_reviews],
            },
            "allowed": [
                (
                    f"可说：记录列出了 {len(current_reviews)} 条与当前命题版本匹配的评审记录及其生命周期。"
                    if current_reviews
                    else "可说：当前没有与命题版本匹配的生效评审记录。"
                )
            ],
            "forbidden": forbidden.copy(),
        },
        {
            "level": 4,
            "key": "promotion_record",
            "state": "available" if promotion_records else "unavailable",
            "basis": {
                "record_type": "promotion",
                "record_ids": [item["event_id"] for item in promotion_records],
            },
            "allowed": [
                (
                    f"可说：事件账本记录了 {len(promotion_records)} 条晋升事件及其位置。"
                    if promotion_records
                    else "可说：当前没有晋升事件记录可供描述。"
                )
            ],
            "forbidden": forbidden.copy(),
        },
    ]
    return {
        "schema_version": _SCHEMA_VERSION,
        "state": "live",
        "provenance": dict(workspace_provenance),
        "records": {
            "state": state_records,
            "evidence": evidence_records,
            "reviews": current_reviews,
            "promotions": promotion_records,
        },
        "levels": levels,
        "decision_boundary": (
            "This projection does not infer proof, novelty, open/resolved status, "
            "or public authorization."
        ),
    }


def _require_campaign_report(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or not _CAMPAIGN_KEYS.issubset(value) or set(value) - (_CAMPAIGN_KEYS | _CAMPAIGN_OPTIONAL_KEYS):
        raise ValueError("campaign report has an incompatible schema")
    if (
        not isinstance(value["rounds"], list)
        or not all(isinstance(item, dict) for item in value["rounds"])
        or not isinstance(value["stop_reason"], str)
        or not isinstance(value["final_metrics"], dict)
        or (value["budget"] is not None and not isinstance(value["budget"], dict))
        or not isinstance(value["creation_log"], list)
        or not all(isinstance(item, dict) for item in value["creation_log"])
        or ("spawn_log" in value and (not isinstance(value["spawn_log"], list) or not all(isinstance(item, dict) for item in value["spawn_log"])))
    ):
        raise ValueError("campaign report has an incompatible schema")
    normalized = dict(value)
    normalized.setdefault("spawn_log", [])
    return normalized


def campaign_snapshot(workspace: ResearchWorkspace) -> dict[str, Any]:
    """Read only the terminal, manifest-governed campaign result.

    A later workspace transition makes the prior campaign output stale.  The
    console intentionally never reads a user-supplied report file.
    """

    if not workspace.events.events:
        return {"available": False, "reason": "campaign_report_not_recorded", "report": None}
    event = workspace.events.events[-1]
    if event.event_type != "CAMPAIGN_RECORDED":
        reason = (
            "campaign_report_stale"
            if any(item.event_type == "CAMPAIGN_RECORDED" for item in workspace.events.events)
            else "campaign_report_not_recorded"
        )
        return {"available": False, "reason": reason, "report": None}
    details = event.payload.get("details")
    if not isinstance(details, dict):
        raise ValueError("campaign event has an incompatible schema")
    artifact_id = details.get("artifact_id")
    report_digest = details.get("report_digest_sha256")
    if not isinstance(artifact_id, str) or not isinstance(report_digest, str):
        raise ValueError("campaign event has an incompatible schema")
    try:
        record = workspace.artifacts.get(artifact_id)
        content = workspace.artifacts.path_for(artifact_id).read_text(encoding="utf-8")
        report = json.loads(content)
    except (KeyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("registered campaign report cannot be read") from exc
    if (
        record.logical_role != "campaign-report"
        or record.sha256 != report_digest
        or hashlib.sha256(content.encode("utf-8")).hexdigest() != report_digest
    ):
        raise ValueError("registered campaign report integrity check failed")
    return {
        "available": True,
        "reason": None,
        "report": _require_campaign_report(report),
        "artifact_id": artifact_id,
    }


def build_console_export(
    workspace_root: str | Path,
    *,
    topic_store: TopicObservationRunner | None = None,
    topic_store_config: TopicStoreConfig | None = None,
    local_projection_config: ConsoleLocalProjectionConfig | None = None,
) -> dict[str, Any]:
    """Build a truthful console payload without changing workspace state."""

    if topic_store is not None and topic_store_config is not None:
        raise ValueError("supply either topic_store or topic_store_config, not both")
    root = Path(workspace_root).resolve()
    resolved_topic_store = (
        topic_store_config.open_read_only() if topic_store_config is not None else topic_store
    )
    workspace = ResearchWorkspace.load(root)
    audit = workspace.audit()
    if not audit.valid:
        raise ValueError("refusing to export an invalid research workspace")
    provenance = _workspace_provenance(workspace)
    workspace_payload = workspace_dashboard_payload(workspace)
    for event, source_event in zip(
        workspace_payload["events"]["events"], workspace.events.events, strict=True
    ):
        event["canonical_unsigned_json"] = canonical_json(source_event.unsigned_dict())
    local_console = (
        local_projection_config.projection(provenance)
        if local_projection_config is not None
        else ConsoleLocalProjectionConfig().projection(provenance)
    )
    return {
        "schema_version": _SCHEMA_VERSION,
        "view_contract": {
            "verification_publication": "live",
            "campaign_observatory": "live_if_current_workspace_campaign_is_registered",
            "review_submission": "existing_review_service_only",
            "source_registry_projection": "live",
            "routes_projection": "live",
            "disclosure_projection": "live",
            "novelty_projection": "live_if_configured",
            "topic_observation": (
                "live_preexisting_single_topic_store"
                if resolved_topic_store is not None
                else "separate_read_model_required"
            ),
            "external_search": "not_configured",
            "operations": "isolated_local_ledger_only",
            # No authoritative read models exist yet for these M2 surfaces.
            # The prototype must therefore fail closed instead of presenting
            # its bundled demonstration account/cost constants as live data.
            "admin_roster": "not_configured_fail_closed",
            "accounting": "not_configured_fail_closed",
            "acct_overview": "not_configured_fail_closed",
            "acct_usage": "not_configured_fail_closed",
            "acct_billing": "not_configured_fail_closed",
            "acct_limits": "not_configured_fail_closed",
            "admin_cost": "not_configured_fail_closed",
        },
        "provenance": provenance,
        "workspace": workspace_payload,
        "source_topic": console_topic_projection(workspace.sources, topic_store=resolved_topic_store),
        "routes": console_routes_projection(workspace, provenance),
        "disclosure": console_disclosure_projection(workspace, provenance),
        "campaign": campaign_snapshot(workspace),
        "novelty": local_console["novelty_audit"],
        "local_console": local_console,
        "role_policy": RolePolicy.default().to_dict(),
        "unsupported": {
            "external_search": "not_configured",
            "external_identity": "not_configured",
            "external_payment": "not_configured",
        },
    }


def write_console_export(
    workspace_root: str | Path,
    output_path: str | Path,
    *,
    topic_store_config: TopicStoreConfig | None = None,
    local_projection_config: ConsoleLocalProjectionConfig | None = None,
) -> Path:
    """Write one explicit JSON export; callers choose its destination."""

    root = Path(workspace_root).resolve()
    target = Path(output_path).resolve()
    if target.suffix.lower() != ".json":
        raise ValueError("console export output must have a .json suffix")
    if target.is_relative_to(root):
        raise ValueError("console export output must be outside the workspace root")
    payload = build_console_export(
        root,
        topic_store_config=topic_store_config,
        local_projection_config=local_projection_config,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target
