"""Read-only composition of a frozen research workspace and operations ledger."""

from __future__ import annotations

import hashlib
from pathlib import Path

from matharc.operations import OperationsLedger

from .schema import canonical_json
from .workspace import ResearchWorkspace


def workspace_replay_digest(workspace_root: str | Path) -> str:
    """Derive an operations binding from a fully validated workspace snapshot."""

    workspace = ResearchWorkspace.load(Path(workspace_root).resolve())
    audit = workspace.audit()
    if not audit.valid:
        raise ValueError("refusing an invalid research workspace")
    payload = {
        "schema_version": "1.0",
        # The replay state can be byte-identical for two independently
        # materialized workspaces (for example, the deterministic demo).
        # Bind operations to the selected workspace identity as well, so a
        # ledger cannot be reused by a sibling workspace with the same state.
        "workspace_root": str(Path(workspace_root).resolve()),
        "run_id": workspace.trace.run_id,
        "state_digest_sha256": workspace.state_digest(),
        "event_head_hash": workspace.events.head_hash,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def open_workspace_operations_ledger(
    workspace_root: str | Path,
    ledger_path: str | Path,
) -> OperationsLedger:
    """Open an isolated ledger whose provenance is derived, never asserted."""

    root = Path(workspace_root).resolve()
    target = Path(ledger_path).resolve()
    if target.is_relative_to(root):
        raise ValueError("operations ledger must be outside the research workspace")
    return OperationsLedger(target, workspace_replay_digest(root))
