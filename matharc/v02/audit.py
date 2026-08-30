from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable

from .falsification import (
    FalsificationContractError,
    get_kill_test_spec,
    iter_route_evaluations,
    qualifying_evaluation_for_route,
)
from .object_registry import ObjectStatus
from .schema import ClaimStatus, EvidenceKind, EvidenceStatus, RouteStatus, ToolStatus
from .source_registry import SourceClaimStatus

if TYPE_CHECKING:  # pragma: no cover
    from ._workspace_impl import ResearchWorkspace


class AuditSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AuditCategory(str, Enum):
    TRACE = "TRACE"
    DEPENDENCY = "DEPENDENCY"
    OBJECT = "OBJECT"
    SOURCE = "SOURCE"
    EVIDENCE = "EVIDENCE"
    TOOL = "TOOL"
    ARTIFACT = "ARTIFACT"
    INDEPENDENCE = "INDEPENDENCE"
    SCOPE = "SCOPE"
    FAILURE = "FAILURE"
    EVENT_LEDGER = "EVENT_LEDGER"
    BENCHMARK = "BENCHMARK"


@dataclass(slots=True, frozen=True)
class AuditIssue:
    issue_id: str
    severity: AuditSeverity
    category: AuditCategory
    message: str
    subject_ids: tuple[str, ...]
    repair: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "subject_ids": list(self.subject_ids),
            "repair": self.repair,
        }


@dataclass(slots=True)
class AuditReport:
    run_id: str
    issues: tuple[AuditIssue, ...]
    current_state_digest_sha256: str
    committed_state_digest_sha256: str

    @property
    def valid(self) -> bool:
        return not any(item.severity is AuditSeverity.ERROR for item in self.issues)

    @property
    def error_count(self) -> int:
        return sum(item.severity is AuditSeverity.ERROR for item in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(item.severity is AuditSeverity.WARNING for item in self.issues)

    def blockers_for(self, claim_ids: Iterable[str]) -> tuple[AuditIssue, ...]:
        relevant = set(claim_ids)
        return tuple(
            item
            for item in self.issues
            if item.severity is AuditSeverity.ERROR
            and (not item.subject_ids or relevant.intersection(item.subject_ids))
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "valid": self.valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "current_state_digest_sha256": self.current_state_digest_sha256,
            "committed_state_digest_sha256": self.committed_state_digest_sha256,
            "issues": [item.to_dict() for item in self.issues],
        }


class _IssueBuilder:
    def __init__(self) -> None:
        self.items: list[AuditIssue] = []
        self._counter = 0

    def add(
        self,
        severity: AuditSeverity,
        category: AuditCategory,
        message: str,
        subject_ids: Iterable[str] = (),
        repair: str = "",
    ) -> None:
        self._counter += 1
        self.items.append(
            AuditIssue(
                issue_id=f"AUDIT-{self._counter:04d}",
                severity=severity,
                category=category,
                message=message,
                subject_ids=tuple(str(item) for item in subject_ids),
                repair=repair,
            )
        )


def audit_workspace(
    workspace: "ResearchWorkspace",
    *,
    require_current_commit: bool = True,
) -> AuditReport:
    """Run a deterministic cross-registry audit over a research workspace."""

    issues = _IssueBuilder()
    trace_validation = workspace.trace.validate()
    for message in trace_validation["errors"]:
        issues.add(
            AuditSeverity.ERROR,
            AuditCategory.TRACE,
            message,
            repair="repair the trace before accepting any further claim promotion",
        )
    for message in trace_validation["warnings"]:
        issues.add(
            AuditSeverity.WARNING,
            AuditCategory.TRACE,
            message,
            repair="add a cold replay or independent verifier",
        )

    object_validation = workspace.objects.validate()
    for message in object_validation["errors"]:
        issues.add(
            AuditSeverity.ERROR,
            AuditCategory.OBJECT,
            message,
            repair="repair the object definition, type or dependency chain",
        )
    for message in object_validation["warnings"]:
        issues.add(
            AuditSeverity.WARNING,
            AuditCategory.OBJECT,
            message,
            repair="complete the object ledger before using it in a critical theorem",
        )

    source_validation = workspace.sources.validate(workspace.trace.claims.keys())
    for message in source_validation["errors"]:
        issues.add(
            AuditSeverity.ERROR,
            AuditCategory.SOURCE,
            message,
            repair="pin and reverify the primary source",
        )
    for message in source_validation["warnings"]:
        issues.add(
            AuditSeverity.WARNING,
            AuditCategory.SOURCE,
            message,
            repair="the source remains pending and cannot carry a proof dependency",
        )

    artifact_validation = workspace.artifacts.verify()
    for message in artifact_validation["errors"]:
        issues.add(
            AuditSeverity.ERROR,
            AuditCategory.ARTIFACT,
            message,
            repair="restore the content-addressed artifact or update no records",
        )

    ledger_validation = workspace.events.validate()
    for message in ledger_validation["errors"]:
        issues.add(
            AuditSeverity.ERROR,
            AuditCategory.EVENT_LEDGER,
            message,
            repair="reject the mutated export and replay from the last valid ledger head",
        )

    current_digest = workspace.state_digest()
    committed_digest = workspace.committed_state_digest
    if require_current_commit and current_digest != committed_digest:
        issues.add(
            AuditSeverity.ERROR,
            AuditCategory.EVENT_LEDGER,
            "workspace state differs from the last sealed event",
            repair="commit the state transition through ResearchWorkspace or reject the mutation",
        )

    claim_ids = set(workspace.trace.claims)
    object_ids = {item.object_id for item in workspace.objects.objects}
    source_ids = {item.source_claim_id for item in workspace.sources.claims}
    artifact_ids = {item.artifact_id for item in workspace.artifacts.records}

    for claim_id, links in workspace.claim_object_links.items():
        if claim_id not in claim_ids:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.DEPENDENCY,
                f"object links reference unknown claim {claim_id}",
                (claim_id,),
                "remove the stale link or restore the claim",
            )
        for object_id in links:
            if object_id not in object_ids:
                issues.add(
                    AuditSeverity.ERROR,
                    AuditCategory.OBJECT,
                    f"claim {claim_id} references unknown object {object_id}",
                    (claim_id, object_id),
                    "declare the mathematical object before using it",
                )

    for claim_id, links in workspace.claim_source_links.items():
        if claim_id not in claim_ids:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.DEPENDENCY,
                f"source links reference unknown claim {claim_id}",
                (claim_id,),
                "remove the stale link or restore the claim",
            )
        for source_id in links:
            if source_id not in source_ids:
                issues.add(
                    AuditSeverity.ERROR,
                    AuditCategory.SOURCE,
                    f"claim {claim_id} references unknown source claim {source_id}",
                    (claim_id, source_id),
                    "register and verify the source claim",
                )

    for evidence_id, artifact_id in workspace.evidence_artifact_links.items():
        if evidence_id not in workspace.trace.evidence:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.EVIDENCE,
                f"artifact link references unknown evidence {evidence_id}",
                (evidence_id,),
                "remove the stale link or restore the evidence",
            )
        if artifact_id not in artifact_ids:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.ARTIFACT,
                f"evidence {evidence_id} references unknown artifact {artifact_id}",
                (evidence_id, artifact_id),
                "store the artifact in the content-addressed store",
            )
        elif evidence_id in workspace.trace.evidence:
            evidence = workspace.trace.evidence[evidence_id]
            artifact = workspace.artifacts.get(artifact_id)
            if evidence.digest_sha256 != artifact.sha256:
                issues.add(
                    AuditSeverity.ERROR,
                    AuditCategory.ARTIFACT,
                    f"evidence {evidence_id} digest differs from artifact {artifact_id}",
                    (evidence_id, artifact_id),
                    "recreate the evidence record from the stored artifact digest",
                )

    for tool_id, artifact_ids_for_tool in workspace.tool_artifact_links.items():
        if tool_id not in workspace.trace.tool_calls:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.TOOL,
                f"artifact links reference unknown tool call {tool_id}",
                (tool_id,),
                "remove the stale link or restore the tool call",
            )
        for artifact_id in artifact_ids_for_tool:
            if artifact_id not in artifact_ids:
                issues.add(
                    AuditSeverity.ERROR,
                    AuditCategory.ARTIFACT,
                    f"tool call {tool_id} references unknown artifact {artifact_id}",
                    (tool_id, artifact_id),
                    "store stdout, stderr or certificate under the declared artifact ID",
                )

    for claim in workspace.trace.claims.values():
        linked_objects = workspace.claim_object_links.get(claim.claim_id, ())
        linked_sources = workspace.claim_source_links.get(claim.claim_id, ())
        if claim.critical and not linked_objects:
            issues.add(
                AuditSeverity.WARNING,
                AuditCategory.OBJECT,
                f"critical claim {claim.claim_id} has no declared mathematical objects",
                (claim.claim_id,),
                "link every load-bearing object used in the statement and proof",
            )
        for object_id in linked_objects:
            if object_id in object_ids:
                item = workspace.objects.get(object_id)
                if claim.status is ClaimStatus.PROVED and item.status is not ObjectStatus.VERIFIED:
                    issues.add(
                        AuditSeverity.ERROR,
                        AuditCategory.OBJECT,
                        f"proved claim {claim.claim_id} uses unverified object {object_id}",
                        (claim.claim_id, object_id),
                        "verify the object definition and dependencies or retract the claim",
                    )
        for source_id in linked_sources:
            if source_id in source_ids:
                source = workspace.sources.get(source_id)
                if claim.status is ClaimStatus.PROVED and source.status is not SourceClaimStatus.VERIFIED:
                    issues.add(
                        AuditSeverity.ERROR,
                        AuditCategory.SOURCE,
                        f"proved claim {claim.claim_id} uses unverified source {source_id}",
                        (claim.claim_id, source_id),
                        "verify the exact source version and statement correspondence",
                    )
                elif source.status is SourceClaimStatus.VERIFIED and claim.claim_id not in source.linked_claim_ids:
                    issues.add(
                        AuditSeverity.ERROR,
                        AuditCategory.SOURCE,
                        f"source {source_id} is not declared applicable to claim {claim.claim_id}",
                        (claim.claim_id, source_id),
                        "add an explicit, audited claim link",
                    )
        if workspace.strict_artifacts:
            for evidence_id in claim.evidence_ids:
                stored = workspace.trace.evidence.get(evidence_id)
                if stored is None or stored.status is not EvidenceStatus.ACCEPTED:
                    continue
                if evidence_id not in workspace.evidence_artifact_links:
                    issues.add(
                        AuditSeverity.ERROR,
                        AuditCategory.ARTIFACT,
                        f"accepted evidence {evidence_id} has no stored artifact",
                        (claim.claim_id, evidence_id),
                        "store and link the exact evidence bytes",
                    )
        if claim.status is ClaimStatus.PROVED and not claim.boundary.strip():
            issues.add(
                AuditSeverity.WARNING,
                AuditCategory.SCOPE,
                f"proved claim {claim.claim_id} has no explicit applicability boundary",
                (claim.claim_id,),
                "state what the theorem does not prove",
            )

    for evidence in workspace.trace.evidence.values():
        if evidence.kind is EvidenceKind.LITERATURE_RESULT:
            linked = {
                source_id
                for claim_id in evidence.claim_ids
                for source_id in workspace.claim_source_links.get(claim_id, ())
            }
            verified = [
                source_id
                for source_id in linked
                if source_id in source_ids
                and workspace.sources.get(source_id).status is SourceClaimStatus.VERIFIED
            ]
            if not verified:
                issues.add(
                    AuditSeverity.ERROR,
                    AuditCategory.SOURCE,
                    f"literature evidence {evidence.evidence_id} lacks a verified source claim",
                    (evidence.evidence_id, *evidence.claim_ids),
                    "register the primary result and verify its exact applicability",
                )

    for tool in workspace.trace.tool_calls.values():
        if tool.status is ToolStatus.PASS and not tool.replayable:
            issues.add(
                AuditSeverity.WARNING,
                AuditCategory.TOOL,
                f"passing tool call {tool.call_id} is not cold-replayable",
                (tool.call_id, *tool.linked_claim_ids),
                "record command, input/output digests and environment digest",
            )

    # v0.3 structured routes use one shared, typed execution record. Public
    # reasoning is not proof that a KillTestSpec actually ran. Legacy v0.2
    # prose-only routes keep the old warning path until they are migrated.
    reasoning_routes = {
        route_id
        for step in workspace.trace.public_reasoning
        if step.falsification_test.strip() and step.observation.strip()
        for route_id in step.linked_route_ids
    }
    failed_routes = {failure.route_id for failure in workspace.trace.failures}
    try:
        route_evaluations = iter_route_evaluations(workspace.trace)
    except FalsificationContractError as exc:
        route_evaluations = ()
        issues.add(
            AuditSeverity.ERROR,
            AuditCategory.FAILURE,
            f"structured route-evaluation store is invalid: {exc}",
            repair="repair or remove malformed RouteEvaluationRecord metadata",
        )

    for record in route_evaluations:
        if record.route_id not in workspace.trace.routes:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.FAILURE,
                f"route evaluation {record.evaluation_id} references unknown route {record.route_id}",
                (record.evaluation_id, record.route_id),
                "restore the route or remove the stale evaluation",
            )
        if record.claim_id not in workspace.trace.claims:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.FAILURE,
                f"route evaluation {record.evaluation_id} references unknown claim {record.claim_id}",
                (record.evaluation_id, record.claim_id),
                "restore the claim or remove the stale evaluation",
            )
        if record.tool_call_id not in workspace.trace.tool_calls:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.TOOL,
                f"route evaluation {record.evaluation_id} references unknown tool call {record.tool_call_id}",
                (record.evaluation_id, record.tool_call_id),
                "restore the replayable tool call or rerun the evaluation",
            )
        if record.witness_artifact_id and record.witness_artifact_id not in artifact_ids:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.ARTIFACT,
                f"route evaluation {record.evaluation_id} references missing witness artifact {record.witness_artifact_id}",
                (record.evaluation_id, record.witness_artifact_id),
                "store the independently verified witness before treating it as a counterexample",
            )

    for route in workspace.trace.routes.values():
        if route.status not in {RouteStatus.ACTIVE, RouteStatus.CLOSED}:
            continue
        try:
            structured_spec = get_kill_test_spec(workspace.trace, route.route_id)
        except FalsificationContractError as exc:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.FAILURE,
                f"route {route.route_id} has invalid structured kill-test metadata: {exc}",
                (route.route_id, *route.claim_ids),
                "restore the content-addressed KillTestSpec before further promotion",
            )
            continue
        if structured_spec is not None:
            for claim_id in route.claim_ids:
                if claim_id not in workspace.trace.claims:
                    continue
                try:
                    qualifying = qualifying_evaluation_for_route(
                        workspace.trace, route.route_id, claim_id
                    )
                except FalsificationContractError as exc:
                    issues.add(
                        AuditSeverity.ERROR,
                        AuditCategory.FAILURE,
                        f"route {route.route_id} cannot validate its current evaluation: {exc}",
                        (route.route_id, claim_id),
                        "repair the shared RouteEvaluationRecord store",
                    )
                    continue
                if qualifying is None:
                    issues.add(
                        AuditSeverity.ERROR,
                        AuditCategory.FAILURE,
                        f"route {route.route_id} has no current PASS_BOUNDED RouteEvaluationRecord for claim {claim_id}",
                        (route.route_id, claim_id),
                        "execute the current KillTestSpec and record its typed result before promotion",
                    )
            continue
        if route.route_id not in reasoning_routes and route.route_id not in failed_routes:
            issues.add(
                AuditSeverity.WARNING,
                AuditCategory.FAILURE,
                f"legacy route {route.route_id} has no recorded execution of its kill test",
                (route.route_id, *route.claim_ids),
                "migrate the route to KillTestSpec/RouteEvaluationRecord or record the legacy observation",
            )

    for failure in workspace.trace.failures:
        if failure.exact and not failure.evidence_ids:
            issues.add(
                AuditSeverity.ERROR,
                AuditCategory.FAILURE,
                f"exact failure {failure.failure_id} has no evidence artifact",
                (failure.failure_id, failure.claim_id, failure.route_id),
                "attach the minimal witness and an independent checker",
            )

    sorted_issues = tuple(
        sorted(
            issues.items,
            key=lambda item: (
                {AuditSeverity.ERROR: 0, AuditSeverity.WARNING: 1, AuditSeverity.INFO: 2}[item.severity],
                item.category.value,
                item.issue_id,
            ),
        )
    )
    return AuditReport(
        run_id=workspace.trace.run_id,
        issues=sorted_issues,
        current_state_digest_sha256=current_digest,
        committed_state_digest_sha256=committed_digest,
    )
