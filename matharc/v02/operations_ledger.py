"""Read-only composition of a frozen research workspace and operations ledger."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

from matharc.operations import OperationsDomainStore, OperationsLedger

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


class WorkspaceBoundOperationsLedger(OperationsDomainStore):
    """Read-only-console-compatible operations domain bound to one workspace.

    The domain implementation remains independent from research code.  This
    adapter supplies the frozen workspace provenance at construction time so a
    persisted operations store cannot be projected for a sibling workspace.
    """

    def __init__(self, root: str | Path, workspace_provenance: Mapping[str, str]) -> None:
        super().__init__(root, workspace_provenance=workspace_provenance)


def open_workspace_operations_domain_ledger(
    workspace_root: str | Path,
    ledger_root: str | Path,
) -> WorkspaceBoundOperationsLedger:
    """Open an operations-domain ledger bound to a validated workspace."""

    root = Path(workspace_root).resolve()
    target = Path(ledger_root).resolve()
    if target.is_relative_to(root):
        raise ValueError("operations ledger must be outside the research workspace")
    workspace = ResearchWorkspace.load(root)
    audit = workspace.audit()
    if not audit.valid:
        raise ValueError("refusing an invalid research workspace")
    if not (target / OperationsDomainStore._FILENAME).is_file():
        raise ValueError("workspace-bound operations ledger is missing")
    provenance = {
        "run_id": workspace.trace.run_id,
        "state_digest_sha256": workspace.state_digest(),
        "event_head_hash": workspace.events.head_hash,
        "workspace_root": str(root),
    }
    return WorkspaceBoundOperationsLedger(target, provenance)
