from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .artifact_store import ArtifactStore
from .demo import build_research_demo
from .object_registry import (
    MathematicalObject,
    ObjectKind,
    ObjectRegistry,
    ObjectStatus,
)
from .source_registry import SourceClaim, SourceClaimStatus, SourceKind, SourceRegistry
from .visualization import render_research_dashboard
from .workspace import ResearchWorkspace


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _verified_objects() -> ObjectRegistry:
    registry = ObjectRegistry()
    objects = [
        MathematicalObject(
            object_id="OBJ-N",
            symbol="N",
            name="natural numbers",
            kind=ObjectKind.SET,
            definition="The set generated from zero by the successor operation.",
            type_signature="N : Set",
            construction_source="The arithmetic foundation declared in the theorem contract.",
            current_role="Domain of every quantified integer variable in the demo theorem.",
            status=ObjectStatus.DEFINED,
            applicability_boundary="Only nonnegative integers are covered.",
            failure_if_removed="The universal quantifier has no declared domain.",
        ),
        MathematicalObject(
            object_id="OBJ-S",
            symbol="S_n",
            name="partial odd-number sum",
            kind=ObjectKind.MAP,
            definition="S_n is the sum of the first n positive odd integers, with S_0=0.",
            type_signature="S : N -> N",
            construction_source="Defined explicitly for the target theorem.",
            current_role="Left-hand side of C-BASE, C-STEP and C-TARGET.",
            status=ObjectStatus.DEFINED,
            domain="N",
            codomain="N",
            dependencies=("OBJ-N",),
            applicability_boundary="Finite sums only; no analytic infinite series is asserted.",
            failure_if_removed="The target identity has no left-hand side.",
        ),
        MathematicalObject(
            object_id="OBJ-P",
            symbol="P(n)",
            name="odd-sum identity predicate",
            kind=ObjectKind.MAP,
            definition="P(n) is the proposition S_n = n^2.",
            type_signature="P : N -> Prop",
            construction_source="Predicate extracted from C-TARGET.",
            current_role="Property transported by mathematical induction.",
            status=ObjectStatus.DEFINED,
            domain="N",
            codomain="Prop",
            dependencies=("OBJ-N", "OBJ-S"),
            applicability_boundary="The predicate concerns the declared finite sum only.",
            failure_if_removed="The induction rule has no property to propagate.",
        ),
    ]
    for item in objects:
        registry.add(item)
        registry.verify(item.object_id)
    return registry


def _verified_sources() -> SourceRegistry:
    registry = SourceRegistry()
    source = SourceClaim(
        source_claim_id="SRC-INDUCTION",
        source_kind=SourceKind.BOOK,
        bibliographic_citation="Pinned arithmetic foundations, induction theorem.",
        canonical_uri="urn:matharc:demo:induction-rule",
        pinned_version="matharc-demo-v1",
        locator="Induction axiom",
        claimed_result="P(0) and forall n(P(n) implies P(n+1)) imply forall n P(n).",
        applicability_conditions=(
            "P is a proposition defined for every natural number.",
            "The base and successor obligations are established in the same arithmetic theory.",
        ),
        linked_claim_ids=("C-TARGET",),
        status=SourceClaimStatus.PENDING,
    )
    registry.add(source)
    registry.verify(
        "SRC-INDUCTION",
        source_digest_sha256=_sha("pinned induction rule bytes"),
        verified_by="workspace-demo-literature-auditor",
        verification_method="compare the pinned rule with the target dependency closure",
        statement_correspondence="The source supplies exactly the final inference from C-BASE and C-STEP to C-TARGET.",
    )
    return registry


def build_workspace_demo(root: str | Path) -> ResearchWorkspace:
    target = Path(root)
    trace = build_research_demo()
    store = ArtifactStore(target / "artifacts")
    artifact_content = {
        "E-FINITE-COUNTEREXAMPLE": "agree-0-100;differ-101",
        "E-BASE": "0=0",
        "E-STEP-A": "0-polynomial",
        "E-STEP-B": "coefficients:[1,2,1]",
        "E-TARGET-INDUCTION": "base+step=>forall-n",
        "E-TARGET-AUDIT": "dependency-audit:C-BASE,C-STEP=>C-TARGET",
    }
    evidence_links: dict[str, str] = {}
    for evidence_id, content in artifact_content.items():
        record = store.put_text(
            f"ART-{evidence_id}",
            content,
            logical_role="evidence",
            producer="workspace-demo",
            linked_claim_ids=trace.evidence[evidence_id].claim_ids,
        )
        if record.sha256 != trace.evidence[evidence_id].digest_sha256:
            raise AssertionError(f"demo artifact digest mismatch: {evidence_id}")
        evidence_links[evidence_id] = record.artifact_id

    workspace = ResearchWorkspace(
        target,
        trace,
        objects=_verified_objects(),
        sources=_verified_sources(),
        artifacts=store,
        claim_object_links={
            "C-FINITE-LEAP": ("OBJ-N", "OBJ-P"),
            "C-BASE": ("OBJ-N", "OBJ-S", "OBJ-P"),
            "C-STEP": ("OBJ-N", "OBJ-S", "OBJ-P"),
            "C-TARGET": ("OBJ-N", "OBJ-S", "OBJ-P"),
        },
        claim_source_links={"C-TARGET": ("SRC-INDUCTION",)},
        evidence_artifact_links=evidence_links,
        strict_artifacts=True,
    )
    report = workspace.audit()
    if not report.valid:
        raise AssertionError(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return workspace


def write_workspace_demo(root: str | Path) -> dict[str, Path]:
    target = Path(root)
    workspace = build_workspace_demo(target)
    manifest = workspace.save()
    audit_path = target / "audit.json"
    dashboard = render_research_dashboard(
        workspace.trace,
        target / "research-dashboard.html",
        title="MathArc Research v0.2 · Tamper-evident workspace",
    )
    summary = target / "workspace-summary.json"
    summary.write_text(
        json.dumps(
            {
                "run_id": workspace.trace.run_id,
                "state_digest_sha256": workspace.state_digest(),
                "event_head_hash": workspace.events.head_hash,
                "event_count": len(workspace.events.events),
                "object_count": len(workspace.objects.objects),
                "source_claim_count": len(workspace.sources.claims),
                "artifact_count": len(workspace.artifacts.records),
                "audit": workspace.audit().to_dict(),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "workspace_manifest": manifest,
        "summary": summary,
        "audit": audit_path,
        "dashboard": dashboard,
        "event_ledger": target / "events.json",
        "object_registry": target / "objects.json",
        "source_registry": target / "sources.json",
        "artifact_manifest": target / "artifacts" / "manifest.json",
    }
