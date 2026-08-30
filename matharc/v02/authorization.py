from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .object_registry import MathematicalObject
from .schema import (
    ClaimRecord,
    EvidenceRecord,
    FailureRecord,
    PublicReasoningStep,
    ResearchRoute,
    ToolCallRecord,
)
from .source_registry import SourceClaim
from .trace import ResearchTrace
from .workspace import ResearchWorkspace


class Capability(str, Enum):
    ADD_CLAIM = "ADD_CLAIM"
    ADD_ROUTE = "ADD_ROUTE"
    ADD_OBJECT = "ADD_OBJECT"
    VERIFY_OBJECT = "VERIFY_OBJECT"
    LINK_OBJECT = "LINK_OBJECT"
    ADD_SOURCE = "ADD_SOURCE"
    VERIFY_SOURCE = "VERIFY_SOURCE"
    LINK_SOURCE = "LINK_SOURCE"
    ADD_EVIDENCE = "ADD_EVIDENCE"
    ADD_TOOL_CALL = "ADD_TOOL_CALL"
    ADD_PUBLIC_REASONING = "ADD_PUBLIC_REASONING"
    RECORD_FAILURE_CANDIDATE = "RECORD_FAILURE_CANDIDATE"
    RECORD_EXACT_FAILURE = "RECORD_EXACT_FAILURE"
    PROMOTE_CLAIM = "PROMOTE_CLAIM"
    EXPORT_WORKSPACE = "EXPORT_WORKSPACE"


@dataclass(slots=True, frozen=True)
class ActorContext:
    actor_id: str
    role: str
    session_id: str

    def __post_init__(self) -> None:
        if not self.actor_id.strip() or not self.role.strip() or not self.session_id.strip():
            raise ValueError("actor_id, role and session_id must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {
            "actor_id": self.actor_id,
            "role": self.role,
            "session_id": self.session_id,
        }


class AuthorizationError(PermissionError):
    pass


class RolePolicy:
    def __init__(self, grants: Mapping[str, Iterable[Capability | str]]) -> None:
        self.grants: dict[str, frozenset[Capability]] = {}
        for role, values in grants.items():
            capabilities = frozenset(
                value if isinstance(value, Capability) else Capability(str(value))
                for value in values
            )
            if not role.strip():
                raise ValueError("role name cannot be empty")
            self.grants[role] = capabilities

    def allows(self, actor: ActorContext, capability: Capability) -> bool:
        return capability in self.grants.get(actor.role, frozenset())

    def require(self, actor: ActorContext, capability: Capability) -> None:
        if actor.role not in self.grants:
            raise AuthorizationError(f"unknown role: {actor.role}")
        if not self.allows(actor, capability):
            raise AuthorizationError(
                f"actor {actor.actor_id} with role {actor.role} lacks {capability.value}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "grants": {
                role: sorted(capability.value for capability in capabilities)
                for role, capabilities in sorted(self.grants.items())
            },
            "boundary": (
                "The policy controls application authority inside one MathArc process. "
                "It does not authenticate a human identity or replace operating-system isolation."
            ),
        }

    @classmethod
    def default(cls) -> "RolePolicy":
        return cls(
            {
                "research-director": {
                    Capability.ADD_CLAIM,
                    Capability.ADD_ROUTE,
                    Capability.LINK_OBJECT,
                    Capability.LINK_SOURCE,
                    Capability.ADD_PUBLIC_REASONING,
                },
                "prover": {
                    Capability.ADD_PUBLIC_REASONING,
                    Capability.ADD_TOOL_CALL,
                },
                "falsifier": {
                    Capability.ADD_PUBLIC_REASONING,
                    Capability.ADD_TOOL_CALL,
                    Capability.RECORD_FAILURE_CANDIDATE,
                },
                "verifier": {
                    Capability.ADD_EVIDENCE,
                    Capability.ADD_TOOL_CALL,
                    Capability.ADD_PUBLIC_REASONING,
                    Capability.RECORD_EXACT_FAILURE,
                },
                "object-auditor": {
                    Capability.ADD_OBJECT,
                    Capability.VERIFY_OBJECT,
                    Capability.LINK_OBJECT,
                    Capability.ADD_PUBLIC_REASONING,
                },
                "literature-auditor": {
                    Capability.ADD_SOURCE,
                    Capability.VERIFY_SOURCE,
                    Capability.LINK_SOURCE,
                    Capability.ADD_PUBLIC_REASONING,
                },
                "promotion-gate": {
                    Capability.PROMOTE_CLAIM,
                    Capability.EXPORT_WORKSPACE,
                    Capability.ADD_PUBLIC_REASONING,
                },
                "human-reviewer": {
                    Capability.ADD_PUBLIC_REASONING,
                    Capability.EXPORT_WORKSPACE,
                },
            }
        )


class SecuredResearchWorkspace:
    """Capability-checked façade over ResearchWorkspace.

    The underlying workspace remains deterministic and verifier-gated.  This
    façade prevents a proposal worker from reaching mutating methods that are
    outside its role.  Actor context is copied into the event ledger through the
    `actor_id/role/session_id` label.
    """

    def __init__(
        self,
        workspace: ResearchWorkspace,
        policy: RolePolicy | None = None,
    ) -> None:
        self.workspace = workspace
        self.policy = policy or RolePolicy.default()

    @property
    def trace(self) -> ResearchTrace:
        return self.workspace.trace

    def add_claim(self, actor: ActorContext, claim: ClaimRecord) -> None:
        self.policy.require(actor, Capability.ADD_CLAIM)
        self.workspace.add_claim(claim, actor=self._actor_label(actor))

    def add_route(self, actor: ActorContext, route: ResearchRoute) -> None:
        self.policy.require(actor, Capability.ADD_ROUTE)
        self.workspace.add_route(route, actor=self._actor_label(actor))

    def add_object(self, actor: ActorContext, item: MathematicalObject) -> None:
        self.policy.require(actor, Capability.ADD_OBJECT)
        self.workspace.add_object(item, actor=self._actor_label(actor))

    def verify_object(self, actor: ActorContext, object_id: str) -> None:
        self.policy.require(actor, Capability.VERIFY_OBJECT)
        self.workspace.verify_object(object_id, actor=self._actor_label(actor))

    def link_claim_objects(
        self,
        actor: ActorContext,
        claim_id: str,
        object_ids: Iterable[str],
    ) -> None:
        self.policy.require(actor, Capability.LINK_OBJECT)
        self.workspace.link_claim_objects(
            claim_id,
            object_ids,
            actor=self._actor_label(actor),
        )

    def add_source_claim(self, actor: ActorContext, source: SourceClaim) -> None:
        self.policy.require(actor, Capability.ADD_SOURCE)
        self.workspace.add_source_claim(source, actor=self._actor_label(actor))

    def verify_source_claim(
        self,
        actor: ActorContext,
        source_claim_id: str,
        *,
        source_digest_sha256: str,
        verified_by: str,
        verification_method: str,
        statement_correspondence: str,
    ) -> None:
        self.policy.require(actor, Capability.VERIFY_SOURCE)
        self.workspace.verify_source_claim(
            source_claim_id,
            source_digest_sha256=source_digest_sha256,
            verified_by=verified_by,
            verification_method=verification_method,
            statement_correspondence=statement_correspondence,
            actor=self._actor_label(actor),
        )

    def link_claim_sources(
        self,
        actor: ActorContext,
        claim_id: str,
        source_claim_ids: Iterable[str],
    ) -> None:
        self.policy.require(actor, Capability.LINK_SOURCE)
        self.workspace.link_claim_sources(
            claim_id,
            source_claim_ids,
            actor=self._actor_label(actor),
        )

    def add_evidence(
        self,
        actor: ActorContext,
        evidence: EvidenceRecord,
        *,
        artifact_content: bytes | str | Mapping[str, Any] | None = None,
        artifact_id: str | None = None,
    ) -> None:
        self.policy.require(actor, Capability.ADD_EVIDENCE)
        self.workspace.add_evidence(
            evidence,
            artifact_content=artifact_content,
            artifact_id=artifact_id,
            actor=self._actor_label(actor),
        )

    def add_tool_call(
        self,
        actor: ActorContext,
        tool_call: ToolCallRecord,
        *,
        stdout: bytes | str | None = None,
        stderr: bytes | str | None = None,
    ) -> None:
        self.policy.require(actor, Capability.ADD_TOOL_CALL)
        self.workspace.add_tool_call(
            tool_call,
            stdout=stdout,
            stderr=stderr,
            actor=self._actor_label(actor),
        )

    def add_public_reasoning(
        self,
        actor: ActorContext,
        step: PublicReasoningStep,
    ) -> None:
        self.policy.require(actor, Capability.ADD_PUBLIC_REASONING)
        self.workspace.add_public_reasoning(step, actor=self._actor_label(actor))

    def record_failure(
        self,
        actor: ActorContext,
        failure: FailureRecord,
    ) -> FailureRecord:
        capability = (
            Capability.RECORD_EXACT_FAILURE
            if failure.exact
            else Capability.RECORD_FAILURE_CANDIDATE
        )
        self.policy.require(actor, capability)
        return self.workspace.record_failure(
            failure,
            actor=self._actor_label(actor),
        )

    def promote_claim(
        self,
        actor: ActorContext,
        claim_id: str,
        *,
        minimum_independent_groups: int | None = None,
    ) -> None:
        self.policy.require(actor, Capability.PROMOTE_CLAIM)
        self.workspace.promote_claim(
            claim_id,
            actor=self._actor_label(actor),
            minimum_independent_groups=minimum_independent_groups,
        )

    def save(self, actor: ActorContext) -> Path:
        self.policy.require(actor, Capability.EXPORT_WORKSPACE)
        return self.workspace.save()

    @staticmethod
    def _actor_label(actor: ActorContext) -> str:
        return f"{actor.actor_id}|{actor.role}|{actor.session_id}"
