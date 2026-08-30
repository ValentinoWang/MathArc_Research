"""Atomic public workspace API.

The package form re-exports the base implementation and strengthens transitions
that can fail after partial validation.  All caller-visible validation failures
are preflighted or sealed as explicit rejected events, so the workspace never
silently remains in an uncommitted half-state.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import Any, Mapping

from .._workspace_impl import ResearchWorkspace as _ResearchWorkspaceImpl
from .._workspace_impl import WorkspaceAuditError
from ..schema import EvidenceRecord
from ..trace import PromotionError


def _content_bytes(value: bytes | str | Mapping[str, Any]) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return (
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


class ResearchWorkspace(_ResearchWorkspaceImpl):
    def add_evidence(
        self,
        evidence: EvidenceRecord,
        *,
        artifact_content: bytes | str | Mapping[str, Any] | None = None,
        artifact_id: str | None = None,
        actor: str = "verifier",
    ) -> None:
        if artifact_content is not None:
            actual = hashlib.sha256(_content_bytes(artifact_content)).hexdigest()
            if actual != evidence.digest_sha256:
                raise ValueError(
                    f"evidence digest {evidence.digest_sha256} does not match "
                    f"prospective artifact {actual}"
                )
        super().add_evidence(
            evidence,
            artifact_content=artifact_content,
            artifact_id=artifact_id,
            actor=actor,
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
        source = self.sources.get(source_claim_id)
        candidate = dataclasses.replace(
            source,
            source_digest_sha256=source_digest_sha256,
            verified_by=verified_by,
            verification_method=verification_method,
            statement_correspondence=statement_correspondence,
        )
        issues = self.sources.verification_issues(candidate)
        if issues:
            raise ValueError("; ".join(issues))
        super().verify_source_claim(
            source_claim_id,
            source_digest_sha256=source_digest_sha256,
            verified_by=verified_by,
            verification_method=verification_method,
            statement_correspondence=statement_correspondence,
            actor=actor,
        )

    def promote_claim(
        self,
        claim_id: str,
        *,
        actor: str = "promotion-gate",
        minimum_independent_groups: int | None = None,
    ) -> None:
        try:
            super().promote_claim(
                claim_id,
                actor=actor,
                minimum_independent_groups=minimum_independent_groups,
            )
        except PromotionError as exc:
            # ResearchTrace records a boundary violation on failed promotion.
            # Seal that mutation before returning the rejection to the caller.
            self._seal_transition(
                "CLAIM_PROMOTION_REJECTED",
                actor=actor,
                subject_ids=(claim_id,),
                details={"reason": str(exc)},
            )
            raise


__all__ = ["ResearchWorkspace", "WorkspaceAuditError"]
