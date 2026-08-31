from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, cast

from ..v02.schema import digest_json, utc_now


class _Enum(str, Enum):
    def __str__(self) -> str:
        return cast(str, self.value)


class ScientificClosure(_Enum):
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"


class EvidenceIntegrity(_Enum):
    INCOMPLETE = "INCOMPLETE"
    REPLAYABLE = "REPLAYABLE"
    INDEPENDENTLY_AUDITED = "INDEPENDENTLY_AUDITED"


class ManuscriptState(_Enum):
    NONE = "NONE"
    DRAFT = "DRAFT"
    REVIEWABLE = "REVIEWABLE"


class TechnicalPreflight(_Enum):
    FAIL = "FAIL"
    PASS = "PASS"


class HumanSignoffState(_Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"


class SubmissionRoute(_Enum):
    UNDECIDED = "UNDECIDED"
    ARXIV_FIRST = "ARXIV_FIRST"
    JOURNAL_FIRST = "JOURNAL_FIRST"
    VERSION_REPLACEMENT = "VERSION_REPLACEMENT"


@dataclass(frozen=True, slots=True)
class HumanSignoff:
    gate: str
    decision: str
    reviewer: str
    reviewed_at: str
    artifact_digest: str
    notes: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"gate": self.gate, "decision": self.decision, "reviewer": self.reviewer,
                "reviewed_at": self.reviewed_at, "artifact_digest": self.artifact_digest,
                "notes": self.notes}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "HumanSignoff":
        required = {"gate", "decision", "reviewer", "reviewed_at", "artifact_digest", "notes"}
        unknown = set(value) - required
        if unknown:
            raise ValueError(f"unknown human signoff fields: {sorted(unknown)}")
        fields = {name: str(value.get(name, "")).strip() for name in required}
        for name in ("gate", "decision", "reviewer", "reviewed_at", "artifact_digest"):
            if not fields[name]:
                raise ValueError(f"human signoff field is empty: {name}")
        return cls(*(fields[name] for name in
                     ("gate", "decision", "reviewer", "reviewed_at", "artifact_digest", "notes")))


@dataclass(frozen=True, slots=True)
class ReviewBundleRef:
    bundle_id: str
    claim_id: str
    claim_revision: int
    digest_sha256: str
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"bundle_id": self.bundle_id, "claim_id": self.claim_id,
                "claim_revision": self.claim_revision, "digest_sha256": self.digest_sha256,
                "path": self.path}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ReviewBundleRef":
        return cls(str(value["bundle_id"]), str(value["claim_id"]), int(value["claim_revision"]),
                   str(value["digest_sha256"]), str(value.get("path", "")))


@dataclass(slots=True)
class PublicationBundle:
    paper_id: str
    paper_version: int
    claim_revisions: dict[str, int]
    review_bundles: tuple[ReviewBundleRef, ...] = ()
    workspace_audit_digest: str = ""
    source_registry_digest: str = ""
    object_registry_digest: str = ""
    artifact_manifest_digest: str = ""
    latex_tree_digest: str = ""
    submission_history: dict[str, Any] = field(default_factory=dict)
    human_signoffs: tuple[HumanSignoff, ...] = ()
    scientific_closure: ScientificClosure = ScientificClosure.BLOCKED
    evidence_integrity: EvidenceIntegrity = EvidenceIntegrity.INCOMPLETE
    manuscript_state: ManuscriptState = ManuscriptState.NONE
    technical_preflight: TechnicalPreflight = TechnicalPreflight.FAIL
    human_signoff: HumanSignoffState = HumanSignoffState.PENDING
    submission_route: SubmissionRoute = SubmissionRoute.UNDECIDED
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.paper_id.strip() or self.paper_version < 1:
            raise ValueError("paper_id and positive paper_version are required")
        if any(revision < 0 for revision in self.claim_revisions.values()):
            raise ValueError("claim revisions must be non-negative")
        bundle_ids = [item.bundle_id for item in self.review_bundles]
        if len(bundle_ids) != len(set(bundle_ids)):
            raise ValueError("duplicate review bundle reference")

    def content_dict(self) -> dict[str, Any]:
        return {"paper_id": self.paper_id, "paper_version": self.paper_version,
                "claim_revisions": dict(sorted(self.claim_revisions.items())),
                "review_bundles": [x.to_dict() for x in sorted(self.review_bundles, key=lambda x: x.bundle_id)],
                "workspace_audit_digest": self.workspace_audit_digest,
                "source_registry_digest": self.source_registry_digest,
                "object_registry_digest": self.object_registry_digest,
                "artifact_manifest_digest": self.artifact_manifest_digest,
                "latex_tree_digest": self.latex_tree_digest,
                "submission_history": self.submission_history,
                "human_signoffs": [x.to_dict() for x in self.human_signoffs],
                "scientific_closure": self.scientific_closure.value,
                "evidence_integrity": self.evidence_integrity.value,
                "manuscript_state": self.manuscript_state.value,
                "technical_preflight": self.technical_preflight.value,
                "human_signoff": self.human_signoff.value,
                "submission_route": self.submission_route.value}

    @property
    def digest_sha256(self) -> str:
        return digest_json(self.content_dict())

    @property
    def readiness(self) -> str:
        """Derive the user-facing state without collapsing domain statuses."""
        if self.technical_preflight is TechnicalPreflight.FAIL:
            return "NOT_READY"
        if (
            self.scientific_closure is ScientificClosure.BLOCKED
            or self.evidence_integrity is not EvidenceIntegrity.INDEPENDENTLY_AUDITED
        ):
            return "DRAFT_READY"
        if self.human_signoff is HumanSignoffState.PENDING:
            return "READY_FOR_HUMAN_SUBMISSION_REVIEW"
        if not self.human_signoffs:
            return "READY_FOR_HUMAN_SUBMISSION_REVIEW"
        return "RELEASE_CANDIDATE"

    def to_dict(self) -> dict[str, Any]:
        result = self.content_dict()
        result.update({"schema_version": "1.0", "digest_sha256": self.digest_sha256,
                       "created_at": self.created_at})
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PublicationBundle":
        allowed = set(cls.__dataclass_fields__) | {"schema_version", "digest_sha256"}
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"unknown publication bundle fields: {sorted(unknown)}")
        bundle = cls(
            paper_id=str(value["paper_id"]), paper_version=int(value["paper_version"]),
            claim_revisions={str(k): int(v) for k, v in dict(value.get("claim_revisions", {})).items()},
            review_bundles=tuple(ReviewBundleRef.from_dict(x) for x in value.get("review_bundles", [])),
            workspace_audit_digest=str(value.get("workspace_audit_digest", "")),
            source_registry_digest=str(value.get("source_registry_digest", "")),
            object_registry_digest=str(value.get("object_registry_digest", "")),
            artifact_manifest_digest=str(value.get("artifact_manifest_digest", "")),
            latex_tree_digest=str(value.get("latex_tree_digest", "")),
            submission_history=dict(value.get("submission_history", {})),
            human_signoffs=tuple(HumanSignoff.from_dict(x) for x in value.get("human_signoffs", [])),
            scientific_closure=ScientificClosure(str(value.get("scientific_closure", "BLOCKED"))),
            evidence_integrity=EvidenceIntegrity(str(value.get("evidence_integrity", "INCOMPLETE"))),
            manuscript_state=ManuscriptState(str(value.get("manuscript_state", "NONE"))),
            technical_preflight=TechnicalPreflight(str(value.get("technical_preflight", "FAIL"))),
            human_signoff=HumanSignoffState(str(value.get("human_signoff", "PENDING"))),
            submission_route=SubmissionRoute(str(value.get("submission_route", "UNDECIDED"))),
            created_at=str(value.get("created_at") or utc_now()),
        )
        expected = str(value.get("digest_sha256", ""))
        if expected and expected != bundle.digest_sha256:
            raise ValueError("publication bundle digest does not match content")
        return bundle
