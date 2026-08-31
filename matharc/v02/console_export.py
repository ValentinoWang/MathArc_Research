"""Versioned, read-only payloads for the zero-build research console."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .authorization import RolePolicy
from .console_topic import console_topic_projection
from .schema import canonical_json
from .workspace import ResearchWorkspace
from .workspace_visualization import workspace_dashboard_payload

_SCHEMA_VERSION = "1.0"
_CAMPAIGN_KEYS = frozenset({"rounds", "stop_reason", "final_metrics", "budget", "creation_log"})


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


def _require_campaign_report(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _CAMPAIGN_KEYS:
        raise ValueError("campaign report has an incompatible schema")
    if (
        not isinstance(value["rounds"], list)
        or not all(isinstance(item, dict) for item in value["rounds"])
        or not isinstance(value["stop_reason"], str)
        or not isinstance(value["final_metrics"], dict)
        or (value["budget"] is not None and not isinstance(value["budget"], dict))
        or not isinstance(value["creation_log"], list)
        or not all(isinstance(item, dict) for item in value["creation_log"])
    ):
        raise ValueError("campaign report has an incompatible schema")
    return value


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
) -> dict[str, Any]:
    """Build a truthful console payload without changing workspace state."""

    root = Path(workspace_root).resolve()
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
    return {
        "schema_version": _SCHEMA_VERSION,
        "view_contract": {
            "verification_publication": "live",
            "campaign_observatory": "live_if_current_workspace_campaign_is_registered",
            "review_submission": "existing_review_service_only",
            "source_registry_projection": "live",
            "topic_observation": "separate_read_model_required",
            "external_search": "not_configured",
            "operations": "isolated_local_ledger_only",
        },
        "provenance": provenance,
        "workspace": workspace_payload,
        "source_topic": console_topic_projection(workspace.sources),
        "campaign": campaign_snapshot(workspace),
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
) -> Path:
    """Write one explicit JSON export; callers choose its destination."""

    root = Path(workspace_root).resolve()
    target = Path(output_path).resolve()
    if target.suffix.lower() != ".json":
        raise ValueError("console export output must have a .json suffix")
    if target.is_relative_to(root):
        raise ValueError("console export output must be outside the workspace root")
    payload = build_console_export(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target
