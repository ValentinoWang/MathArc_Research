from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping, TypeVar

from .artifact_store import ArtifactRecord, ArtifactStore
from .audit import AuditReport, AuditSeverity, audit_workspace
from .event_log import EventLedger
from .object_registry import MathematicalObject, ObjectRegistry, ObjectStatus
from .schema import (
    ClaimRecord,
    EvidenceRecord,
    FailureRecord,
    PublicReasoningStep,
    ResearchRoute,
    ToolCallRecord,
    canonical_json,
    digest_json,
)
from .source_registry import SourceClaim, SourceClaimStatus, SourceRegistry
from .trace import ResearchTrace, TraceValidationError, load_trace, save_trace

_ResearchWorkspaceT = TypeVar("_ResearchWorkspaceT", bound="ResearchWorkspace")


class WorkspaceAuditError(TraceValidationError):
    """Raised when cross-registry audit blocks a workspace transition."""


class ResearchWorkspace:
    """Tamper-evident, typed workspace for long-horizon theorem research.

    `ResearchTrace` remains the mathematical claim authority.  The workspace
    adds typed object definitions, pinned source claims, content-addressed
    artifacts, cross-links and an append-only event ledger.  Direct mutations
    outside workspace methods are detected because the resulting state digest
    no longer matches the last sealed event.
    """

    def __init__(
        self,
        root: str | Path,
        trace: ResearchTrace,
        *,
        objects: ObjectRegistry | None = None,
        sources: SourceRegistry | None = None,
        events: EventLedger | None = None,
        artifacts: ArtifactStore | None = None,
        claim_object_links: Mapping[str, Iterable[str]] | None = None,
        claim_source_links: Mapping[str, Iterable[str]] | None = None,
        evidence_artifact_links: Mapping[str, str] | None = None,
        tool_artifact_links: Mapping[str, Iterable[str]] | None = None,
        strict_artifacts: bool = True,
        initialize_event: bool = True,
    ) -> None:
        self.root = Path(root)
        self.trace = trace
        self.objects = objects or ObjectRegistry()
        self.sources = sources or SourceRegistry()
        self.events = events or EventLedger()
        self.artifacts = artifacts or ArtifactStore(self.root / "artifacts")
        self.claim_object_links = self._normalize_multi_links(claim_object_links)
        self.claim_source_links = self._normalize_multi_links(claim_source_links)
        self.evidence_artifact_links = {
            str(key): str(value)
            for key, value in (evidence_artifact_links or {}).items()
        }
        self.tool_artifact_links = self._normalize_multi_links(tool_artifact_links)
        self.strict_artifacts = bool(strict_artifacts)
        if initialize_event and not self.events.events:
            self._seal_transition(
                "WORKSPACE_CREATED",
                actor="system",
                subject_ids=(self.trace.run_id,),
                details={"schema_version": "1.0"},
            )

    @property
    def committed_state_digest(self) -> str:
        if not self.events.events:
            return ""
        return str(self.events.events[-1].payload.get("state_digest_after", ""))

    def state_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "trace": self.trace.to_dict(),
            "objects": self.objects.to_dict(),
            "sources": self.sources.to_dict(),
            "artifacts": self.artifacts.to_dict(),
            "links": self.links_dict(),
            "strict_artifacts": self.strict_artifacts,
        }

    def state_digest(self) -> str:
        return digest_json(self.state_dict())

    def links_dict(self) -> dict[str, Any]:
        return {
            "claim_object_links": {
                key: list(value) for key, value in sorted(self.claim_object_links.items())
            },
            "claim_source_links": {
                key: list(value) for key, value in sorted(self.claim_source_links.items())
            },
            "evidence_artifact_links": dict(
                sorted(self.evidence_artifact_links.items())
            ),
            "tool_artifact_links": {
                key: list(value) for key, value in sorted(self.tool_artifact_links.items())
            },
        }

    def audit(self, *, require_current_commit: bool = True) -> AuditReport:
        return audit_workspace(self, require_current_commit=require_current_commit)

    def add_claim(self, claim: ClaimRecord, *, actor: str = "strategist") -> None:
        self._assert_committed()
        self.trace.add_claim(claim)
        self._seal_transition(
            "CLAIM_ADDED",
            actor=actor,
            subject_ids=(claim.claim_id,),
            details={"claim_digest_sha256": digest_json(claim.to_dict())},
        )

    def add_route(self, route: ResearchRoute, *, actor: str = "strategist") -> None:
        self._assert_committed()
        self.trace.add_route(route)
        self._seal_transition(
            "ROUTE_ADDED",
            actor=actor,
            subject_ids=(route.route_id, *route.claim_ids),
            details={"route_digest_sha256": digest_json(route.to_dict())},
        )

    def add_object(
        self,
        item: MathematicalObject,
        *,
        actor: str = "mathematical-object-auditor",
    ) -> None:
        self._assert_committed()
        self.objects.add(item)
        self._seal_transition(
            "OBJECT_ADDED",
            actor=actor,
            subject_ids=(item.object_id,),
            details={"object_digest_sha256": digest_json(item.to_dict())},
        )

    def verify_object(
        self,
        object_id: str,
        *,
        actor: str = "mathematical-object-auditor",
    ) -> None:
        self._assert_committed()
        self.objects.verify(object_id)
        self._seal_transition(
            "OBJECT_VERIFIED",
            actor=actor,
            subject_ids=(object_id,),
            details={},
        )

    def link_claim_objects(
        self,
        claim_id: str,
        object_ids: Iterable[str],
        *,
        actor: str = "strategist",
    ) -> None:
        self._assert_committed()
        self._require_claim(claim_id)
        values = tuple(dict.fromkeys(str(item) for item in object_ids))
        for object_id in values:
            self.objects.get(object_id)
        self.claim_object_links[claim_id] = values
        self._seal_transition(
            "CLAIM_OBJECTS_LINKED",
            actor=actor,
            subject_ids=(claim_id, *values),
            details={},
        )

    def add_source_claim(
        self,
        source: SourceClaim,
        *,
        actor: str = "literature-auditor",
    ) -> None:
        self._assert_committed()
        self.sources.add(source)
        self._seal_transition(
            "SOURCE_CLAIM_ADDED",
            actor=actor,
            subject_ids=(source.source_claim_id, *source.linked_claim_ids),
            details={"source_claim_digest_sha256": digest_json(source.to_dict())},
        )

    def verify_source_claim(
        self,
        source_claim_id: str,
        *,
        source_digest_sha256: str,
        verified_by: str,
        verification_method: str,
        statement_correspondence: str,
        actor: str = "literature-auditor",
    ) -> None:
        self._assert_committed()
        self.sources.verify(
            source_claim_id,
            source_digest_sha256=source_digest_sha256,
            verified_by=verified_by,
            verification_method=verification_method,
            statement_correspondence=statement_correspondence,
        )
        self._seal_transition(
            "SOURCE_CLAIM_VERIFIED",
            actor=actor,
            subject_ids=(source_claim_id,),
            details={"source_digest_sha256": source_digest_sha256},
        )

    def link_claim_sources(
        self,
        claim_id: str,
        source_claim_ids: Iterable[str],
        *,
        actor: str = "literature-auditor",
    ) -> None:
        self._assert_committed()
        self._require_claim(claim_id)
        values = tuple(dict.fromkeys(str(item) for item in source_claim_ids))
        for source_id in values:
            source = self.sources.get(source_id)
            if claim_id not in source.linked_claim_ids:
                raise ValueError(
                    f"source {source_id} is not declared applicable to claim {claim_id}"
                )
        self.claim_source_links[claim_id] = values
        self._seal_transition(
            "CLAIM_SOURCES_LINKED",
            actor=actor,
            subject_ids=(claim_id, *values),
            details={},
        )

    def add_evidence(
        self,
        evidence: EvidenceRecord,
        *,
        artifact_content: bytes | str | Mapping[str, Any] | None = None,
        artifact_id: str | None = None,
        actor: str = "verifier",
    ) -> None:
        self._assert_committed()
        self.trace.add_evidence(evidence)
        linked_artifact: ArtifactRecord | None = None
        if artifact_content is not None:
            target_id = artifact_id or f"ART-{evidence.evidence_id}"
            linked_artifact = self._store_content(
                target_id,
                artifact_content,
                logical_role="evidence",
                producer=actor,
                linked_claim_ids=evidence.claim_ids,
            )
            if linked_artifact.sha256 != evidence.digest_sha256:
                del self.trace.evidence[evidence.evidence_id]
                for claim_id in evidence.claim_ids:
                    claim = self.trace.claims[claim_id]
                    claim.evidence_ids = tuple(
                        item for item in claim.evidence_ids if item != evidence.evidence_id
                    )
                raise ValueError(
                    f"evidence digest {evidence.digest_sha256} does not match stored artifact "
                    f"{linked_artifact.sha256}"
                )
            self.evidence_artifact_links[evidence.evidence_id] = linked_artifact.artifact_id
        elif self.strict_artifacts and evidence.status.value == "ACCEPTED":
            # Keep construction possible, but the unlinked evidence cannot pass
            # workspace audit or claim promotion.
            pass
        self._seal_transition(
            "EVIDENCE_ADDED",
            actor=actor,
            subject_ids=(evidence.evidence_id, *evidence.claim_ids),
            details={
                "evidence_digest_sha256": digest_json(evidence.to_dict()),
                "artifact_id": linked_artifact.artifact_id if linked_artifact else None,
            },
        )

    def add_tool_call(
        self,
        tool_call: ToolCallRecord,
        *,
        stdout: bytes | str | None = None,
        stderr: bytes | str | None = None,
        actor: str = "tool-runner",
    ) -> None:
        self._assert_committed()
        self.trace.add_tool_call(tool_call)
        artifact_ids: list[str] = []
        if stdout is not None:
            record = self._store_content(
                f"ART-{tool_call.call_id}-STDOUT",
                stdout,
                logical_role="tool-stdout",
                producer=actor,
                linked_claim_ids=tool_call.linked_claim_ids,
                linked_tool_call_ids=(tool_call.call_id,),
            )
            artifact_ids.append(record.artifact_id)
        if stderr is not None:
            record = self._store_content(
                f"ART-{tool_call.call_id}-STDERR",
                stderr,
                logical_role="tool-stderr",
                producer=actor,
                linked_claim_ids=tool_call.linked_claim_ids,
                linked_tool_call_ids=(tool_call.call_id,),
            )
            artifact_ids.append(record.artifact_id)
        if artifact_ids:
            self.tool_artifact_links[tool_call.call_id] = tuple(artifact_ids)
        self._seal_transition(
            "TOOL_CALL_ADDED",
            actor=actor,
            subject_ids=(tool_call.call_id, *tool_call.linked_claim_ids),
            details={
                "tool_call_digest_sha256": digest_json(tool_call.to_dict()),
                "artifact_ids": artifact_ids,
            },
        )

    def add_public_reasoning(
        self,
        step: PublicReasoningStep,
        *,
        actor: str | None = None,
    ) -> None:
        self._assert_committed()
        self.trace.add_public_reasoning(step)
        self._seal_transition(
            "PUBLIC_REASONING_ADDED",
            actor=actor or step.role,
            subject_ids=(
                step.step_id,
                *step.linked_claim_ids,
                *step.linked_route_ids,
                *step.linked_tool_call_ids,
            ),
            details={"reasoning_digest_sha256": digest_json(step.to_dict())},
        )

    def record_failure(
        self,
        failure: FailureRecord,
        *,
        actor: str = "falsifier",
    ) -> FailureRecord:
        self._assert_committed()
        record = self.trace.record_failure(failure)
        self._seal_transition(
            "FAILURE_RECORDED",
            actor=actor,
            subject_ids=(
                record.failure_id,
                record.claim_id,
                record.route_id,
                *record.invalidated_claim_ids,
            ),
            details={"failure_digest_sha256": digest_json(record.to_dict())},
        )
        return record

    def promote_claim(
        self,
        claim_id: str,
        *,
        actor: str = "promotion-gate",
        minimum_independent_groups: int | None = None,
    ) -> None:
        self._assert_committed()
        self._require_claim(claim_id)
        linked_objects = self.claim_object_links.get(claim_id, ())
        unresolved_objects = [
            object_id
            for object_id in linked_objects
            if self.objects.get(object_id).status is not ObjectStatus.VERIFIED
        ]
        if unresolved_objects:
            raise WorkspaceAuditError(
                f"claim {claim_id} uses unverified objects {unresolved_objects}"
            )
        linked_sources = self.claim_source_links.get(claim_id, ())
        unresolved_sources = [
            source_id
            for source_id in linked_sources
            if self.sources.get(source_id).status is not SourceClaimStatus.VERIFIED
            or not self.sources.usable_for_claim(source_id, claim_id)
        ]
        if unresolved_sources:
            raise WorkspaceAuditError(
                f"claim {claim_id} uses unverified or inapplicable sources {unresolved_sources}"
            )
        if self.strict_artifacts:
            claim = self.trace.claims[claim_id]
            unlinked = [
                evidence_id
                for evidence_id in claim.evidence_ids
                if evidence_id in self.trace.evidence
                and self.trace.evidence[evidence_id].status.value == "ACCEPTED"
                and evidence_id not in self.evidence_artifact_links
            ]
            if unlinked:
                raise WorkspaceAuditError(
                    f"claim {claim_id} has accepted evidence without stored artifacts {unlinked}"
                )
        report = self.audit(require_current_commit=True)
        if not report.valid:
            messages = [
                issue.message
                for issue in report.issues
                if issue.severity is AuditSeverity.ERROR
            ]
            raise WorkspaceAuditError("; ".join(messages))
        self.trace.promote_claim(
            claim_id,
            minimum_independent_groups=minimum_independent_groups,
        )
        self._seal_transition(
            "CLAIM_PROMOTED",
            actor=actor,
            subject_ids=(claim_id,),
            details={"status": "PROVED"},
        )

    def save(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        self._assert_committed()
        report = self.audit(require_current_commit=True)
        if not report.valid:
            raise WorkspaceAuditError(
                "; ".join(
                    issue.message
                    for issue in report.issues
                    if issue.severity is AuditSeverity.ERROR
                )
            )
        trace_path = save_trace(self.trace, self.root / "research-trace.json")
        object_path = self.objects.save(self.root / "objects.json")
        source_path = self.sources.save(self.root / "sources.json")
        event_path = self.events.save(self.root / "events.json")
        artifact_manifest = self.artifacts.save_manifest()
        links_path = self.root / "links.json"
        links_path.write_text(
            json.dumps(self.links_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        audit_path = self.root / "audit.json"
        audit_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        files = {
            "research-trace.json": self._file_sha256(trace_path),
            "objects.json": self._file_sha256(object_path),
            "sources.json": self._file_sha256(source_path),
            "events.json": self._file_sha256(event_path),
            "links.json": self._file_sha256(links_path),
            "audit.json": self._file_sha256(audit_path),
            "artifacts/manifest.json": self._file_sha256(artifact_manifest),
        }
        manifest = {
            "schema_version": "1.0",
            "run_id": self.trace.run_id,
            "strict_artifacts": self.strict_artifacts,
            "state_digest_sha256": self.state_digest(),
            "event_head_hash": self.events.head_hash,
            "files": files,
        }
        manifest_path = self.root / "workspace.json"
        temporary = manifest_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, manifest_path)
        return manifest_path

    @classmethod
    def load(cls: "type[_ResearchWorkspaceT]", root: str | Path) -> "_ResearchWorkspaceT":
        root_path = Path(root)
        manifest_path = root_path / "workspace.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("workspace manifest root must be an object")
        allowed = {
            "schema_version",
            "run_id",
            "strict_artifacts",
            "state_digest_sha256",
            "event_head_hash",
            "files",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown workspace fields: {sorted(unknown)}")
        if str(payload.get("schema_version")) != "1.0":
            raise ValueError("unsupported workspace schema")
        for relative, expected in dict(payload.get("files") or {}).items():
            path = (root_path / relative).resolve()
            if root_path.resolve() not in path.parents:
                raise ValueError(f"workspace file escapes root: {relative}")
            if not path.is_file():
                raise ValueError(f"workspace file is missing: {relative}")
            actual = cls._file_sha256(path)
            if actual != expected:
                raise ValueError(f"workspace file digest mismatch: {relative}")
        links = json.loads((root_path / "links.json").read_text(encoding="utf-8"))
        workspace = cls(
            root_path,
            load_trace(root_path / "research-trace.json"),
            objects=ObjectRegistry.load(root_path / "objects.json"),
            sources=SourceRegistry.load(root_path / "sources.json"),
            events=EventLedger.load(root_path / "events.json"),
            artifacts=ArtifactStore.load(root_path / "artifacts"),
            claim_object_links=links.get("claim_object_links", {}),
            claim_source_links=links.get("claim_source_links", {}),
            evidence_artifact_links=links.get("evidence_artifact_links", {}),
            tool_artifact_links=links.get("tool_artifact_links", {}),
            strict_artifacts=bool(payload.get("strict_artifacts", True)),
            initialize_event=False,
        )
        if workspace.trace.run_id != str(payload["run_id"]):
            raise ValueError("workspace run id mismatch")
        if workspace.events.head_hash != str(payload["event_head_hash"]):
            raise ValueError("workspace event head mismatch")
        if workspace.state_digest() != str(payload["state_digest_sha256"]):
            raise ValueError("workspace state digest mismatch")
        report = workspace.audit(require_current_commit=True)
        if not report.valid:
            raise WorkspaceAuditError(
                "; ".join(
                    issue.message
                    for issue in report.issues
                    if issue.severity is AuditSeverity.ERROR
                )
            )
        return workspace

    def _store_content(
        self,
        artifact_id: str,
        content: bytes | str | Mapping[str, Any],
        *,
        logical_role: str,
        producer: str,
        linked_claim_ids: Iterable[str] = (),
        linked_tool_call_ids: Iterable[str] = (),
    ) -> ArtifactRecord:
        if isinstance(content, bytes):
            return self.artifacts.put_bytes(
                artifact_id,
                content,
                logical_role=logical_role,
                producer=producer,
                linked_claim_ids=linked_claim_ids,
                linked_tool_call_ids=linked_tool_call_ids,
            )
        if isinstance(content, str):
            return self.artifacts.put_text(
                artifact_id,
                content,
                logical_role=logical_role,
                producer=producer,
                linked_claim_ids=linked_claim_ids,
                linked_tool_call_ids=linked_tool_call_ids,
            )
        return self.artifacts.put_json(
            artifact_id,
            dict(content),
            logical_role=logical_role,
            producer=producer,
            linked_claim_ids=linked_claim_ids,
            linked_tool_call_ids=linked_tool_call_ids,
        )

    def _assert_committed(self) -> None:
        if self.state_digest() != self.committed_state_digest:
            raise WorkspaceAuditError(
                "workspace contains an unsealed direct mutation; reload the last valid state "
                "or explicitly reconstruct the transition through ResearchWorkspace"
            )

    def _seal_transition(
        self,
        event_type: str,
        *,
        actor: str,
        subject_ids: Iterable[str],
        details: Mapping[str, Any],
    ) -> None:
        state_digest = self.state_digest()
        payload = {
            "details": dict(details),
            "state_digest_after": state_digest,
        }
        self.events.append(
            event_id=f"EV-{len(self.events.events):06d}-{uuid.uuid4().hex[:10]}",
            event_type=event_type,
            actor=actor,
            subject_ids=subject_ids,
            payload=payload,
        )

    def _require_claim(self, claim_id: str) -> None:
        if claim_id not in self.trace.claims:
            raise KeyError(f"unknown claim: {claim_id}")

    @staticmethod
    def _normalize_multi_links(
        links: Mapping[str, Iterable[str]] | None,
    ) -> dict[str, tuple[str, ...]]:
        return {
            str(key): tuple(dict.fromkeys(str(item) for item in values))
            for key, values in (links or {}).items()
        }

    @staticmethod
    def _file_sha256(path: str | Path) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
