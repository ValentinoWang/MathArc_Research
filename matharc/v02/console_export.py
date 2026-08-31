"""Versioned, read-only payloads for the zero-build research console."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .authorization import RolePolicy
from .console_topic import console_topic_projection
from .workspace import ResearchWorkspace
from .workspace_visualization import workspace_dashboard_payload

_SCHEMA_VERSION = "1.0"
_CAMPAIGN_KEYS = frozenset({"rounds", "stop_reason", "final_metrics", "budget", "creation_log"})


def campaign_snapshot(path: str | Path | None) -> dict[str, Any]:
    """Read the optional campaign report under the one shared console contract."""
    if path is None:
        return {"available": False, "reason": "campaign_report_not_supplied", "report": None}
    source = Path(path)
    if not source.is_file():
        return {"available": False, "reason": "campaign_report_not_found", "report": None}
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid campaign report: {source}") from exc
    if not isinstance(value, dict) or set(value) != _CAMPAIGN_KEYS:
        raise ValueError("campaign report has an incompatible schema")
    return {"available": True, "reason": None, "report": value}


def build_console_export(
    workspace_root: str | Path,
    *,
    campaign_report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a truthful console payload without changing workspace state."""

    root = Path(workspace_root).resolve()
    workspace = ResearchWorkspace.load(root)
    audit = workspace.audit()
    if not audit.valid:
        raise ValueError("refusing to export an invalid research workspace")
    return {
        "schema_version": _SCHEMA_VERSION,
        "view_contract": {
            "verification_publication": "live",
            "campaign_observatory": "live_if_campaign_report_supplied",
            "review_submission": "existing_review_service_only",
            "source_registry_projection": "live",
            "topic_observation": "separate_read_model_required",
            "external_search": "not_configured",
            "operations": "isolated_local_ledger_only",
        },
        "provenance": {
            "workspace_root": str(root),
            "run_id": workspace.trace.run_id,
            "state_digest_sha256": workspace.state_digest(),
            "event_head_hash": workspace.events.head_hash,
        },
        "workspace": workspace_dashboard_payload(workspace),
        "source_topic": console_topic_projection(workspace.sources),
        "campaign": campaign_snapshot(campaign_report_path),
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
    campaign_report_path: str | Path | None = None,
) -> Path:
    """Write one explicit JSON export; callers choose its destination."""

    target = Path(output_path)
    if target.suffix.lower() != ".json":
        raise ValueError("console export output must have a .json suffix")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_console_export(workspace_root, campaign_report_path=campaign_report_path)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target
