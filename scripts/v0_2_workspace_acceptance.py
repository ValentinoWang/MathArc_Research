from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from matharc.v02.artifact_store import ArtifactStore
from matharc.v02.event_log import EventLedger
from matharc.v02.schema import (
    ClaimRecord,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    TheoremContract,
)
from matharc.v02.source_registry import SourceClaim, SourceKind
from matharc.v02.trace import PromotionError, ResearchTrace
from matharc.v02.workspace import ResearchWorkspace, WorkspaceAuditError
from matharc.v02.workspace_bundle import write_full_workspace_bundle

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def sha(value: bytes | str) -> str:
    content = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


@dataclass(slots=True)
class Gate:
    gate_id: str
    description: str
    check: Callable[[], dict[str, Any]]


def trace() -> ResearchTrace:
    return ResearchTrace(
        "WORKSPACE-ACCEPTANCE",
        TheoremContract("K", "prove C", ("C",), "test scope"),
    )


def gate_bundle() -> dict[str, Any]:
    target = ARTIFACTS / "v02-workspace"
    paths = write_full_workspace_bundle(target)
    missing = [key for key, path in paths.items() if not path.is_file()]
    assert not missing, missing
    workspace = ResearchWorkspace.load(target)
    audit = workspace.audit()
    assert audit.valid, audit.to_dict()
    return {
        "files": {key: str(path.relative_to(ROOT)) for key, path in paths.items()},
        "state_digest_sha256": workspace.state_digest(),
        "event_head_hash": workspace.events.head_hash,
        "audit_errors": audit.error_count,
        "audit_warnings": audit.warning_count,
    }


def gate_cold_replay() -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "examples/workspace_v02.py",
            "--out-dir",
            "artifacts/v02-workspace",
            "--verify",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is True
    return {"returncode": completed.returncode, "audit": payload}


def gate_event_tamper() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = ResearchWorkspace(directory, trace())
        payload = workspace.events.to_dict()
        payload["events"][0]["actor"] = "tampered"
        try:
            EventLedger.from_dict(payload)
        except ValueError as exc:
            return {"rejected": True, "reason": str(exc)}
    raise AssertionError("tampered event ledger was accepted")


def gate_artifact_tamper() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        store = ArtifactStore(directory)
        record = store.put_text(
            "A",
            "original",
            logical_role="certificate",
            producer="acceptance",
        )
        store.path_for(record.artifact_id).write_text("tampered", encoding="utf-8")
        result = store.verify()
        assert not result["valid"]
        return result


def gate_direct_mutation() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = ResearchWorkspace(directory, trace())
        workspace.trace.metadata["injected"] = True
        report = workspace.audit()
        assert not report.valid
        try:
            workspace.add_claim(ClaimRecord("C", "C", "scope"))
        except WorkspaceAuditError as exc:
            return {
                "audit_error_count": report.error_count,
                "transition_rejected": True,
                "reason": str(exc),
            }
    raise AssertionError("unsealed direct mutation was accepted")


def gate_evidence_atomicity() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = ResearchWorkspace(directory, trace())
        workspace.add_claim(ClaimRecord("C", "C", "scope"))
        before = workspace.state_digest()
        evidence = EvidenceRecord(
            evidence_id="E",
            claim_ids=("C",),
            kind=EvidenceKind.EXACT_CERTIFICATE,
            status=EvidenceStatus.ACCEPTED,
            summary="mismatched certificate",
            artifact_uri="workspace://E",
            digest_sha256=sha("expected"),
            producer="p",
            verifier="v",
            independence_group="g",
            replay_command="python replay.py",
            statement_correspondence="checks C",
        )
        try:
            workspace.add_evidence(evidence, artifact_content="different")
        except ValueError as exc:
            assert workspace.state_digest() == before
            assert workspace.committed_state_digest == before
            assert "E" not in workspace.trace.evidence
            assert not workspace.artifacts.records
            return {"atomic": True, "reason": str(exc)}
    raise AssertionError("mismatched evidence was accepted")


def gate_source_atomicity() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = ResearchWorkspace(directory, trace())
        workspace.add_claim(ClaimRecord("C", "C", "scope"))
        source = SourceClaim(
            source_claim_id="S",
            source_kind=SourceKind.PAPER,
            bibliographic_citation="Pinned source",
            canonical_uri="urn:test:source",
            pinned_version="v1",
            locator="Theorem 1",
            claimed_result="C",
            applicability_conditions=("test scope",),
            linked_claim_ids=("C",),
        )
        workspace.add_source_claim(source)
        before = workspace.state_digest()
        try:
            workspace.verify_source_claim(
                "S",
                source_digest_sha256="bad",
                verified_by="auditor",
                verification_method="primary-source inspection",
                statement_correspondence="matches C",
            )
        except ValueError as exc:
            assert workspace.state_digest() == before
            assert workspace.committed_state_digest == before
            return {"atomic": True, "reason": str(exc)}
    raise AssertionError("invalid source verification was accepted")


def gate_rejected_promotion() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = ResearchWorkspace(directory, trace(), strict_artifacts=False)
        workspace.add_claim(ClaimRecord("C", "C", "scope"))
        before = len(workspace.events.events)
        try:
            workspace.promote_claim("C")
        except PromotionError as exc:
            assert len(workspace.events.events) == before + 1
            assert workspace.events.events[-1].event_type == "CLAIM_PROMOTION_REJECTED"
            assert workspace.state_digest() == workspace.committed_state_digest
            return {"sealed": True, "reason": str(exc)}
    raise AssertionError("unsupported promotion passed")


def gate_dashboard_contract() -> dict[str, Any]:
    dashboard = ARTIFACTS / "v02-workspace" / "workspace-dashboard.html"
    text = dashboard.read_text(encoding="utf-8")
    panels = [
        "命题依赖图",
        "独立证据矩阵",
        "公开研究轨迹",
        "工具调用与冷重放",
        "事件哈希链",
        "数学对象账本",
        "文献命题账本",
        "失败传播",
        "对抗审计",
        "基准资格",
    ]
    missing = [panel for panel in panels if panel not in text]
    assert not missing, missing
    assert "普遍更强" in text
    return {"panel_count": len(panels), "dashboard_bytes": dashboard.stat().st_size}


def gate_workspace_file_tamper() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "bundle"
        write_full_workspace_bundle(target)
        trace_path = target / "research-trace.json"
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        payload["metadata"]["tampered"] = True
        trace_path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            ResearchWorkspace.load(target)
        except ValueError as exc:
            return {"rejected": True, "reason": str(exc)}
    raise AssertionError("tampered workspace file was accepted")


def main() -> None:
    gates = [
        Gate("W01", "full workspace bundle exports and audits", gate_bundle),
        Gate("W02", "workspace cold replay succeeds", gate_cold_replay),
        Gate("W03", "event mutation breaks the hash chain", gate_event_tamper),
        Gate("W04", "artifact byte mutation is detected", gate_artifact_tamper),
        Gate("W05", "direct state injection is rejected", gate_direct_mutation),
        Gate("W06", "evidence mismatch failure is atomic", gate_evidence_atomicity),
        Gate("W07", "source-verification failure is atomic", gate_source_atomicity),
        Gate("W08", "unsupported promotion is sealed as a rejection event", gate_rejected_promotion),
        Gate("W09", "startup dashboard exposes all research ledgers", gate_dashboard_contract),
        Gate("W10", "exported workspace file tampering is rejected", gate_workspace_file_tamper),
    ]
    records: list[dict[str, Any]] = []
    for gate in gates:
        try:
            details = gate.check()
            records.append(
                {
                    "gate_id": gate.gate_id,
                    "description": gate.description,
                    "status": "PASS",
                    "details": details,
                }
            )
        except Exception as exc:  # pragma: no cover
            records.append(
                {
                    "gate_id": gate.gate_id,
                    "description": gate.description,
                    "status": "FAIL",
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
            )
    passed = sum(record["status"] == "PASS" for record in records)
    result = {
        "schema_version": "1.0",
        "release": "MathArc Research v0.2 workspace",
        "passed": passed,
        "total": len(records),
        "valid": passed == len(records),
        "gates": records,
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    output = ARTIFACTS / "v0.2-workspace-acceptance.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
