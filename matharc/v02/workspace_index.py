"""Read-only discovery of valid research workspaces below an explicit root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workspace import ResearchWorkspace


@dataclass(frozen=True, slots=True)
class WorkspaceIndexEntry:
    workspace_root: str
    run_id: str
    state_digest_sha256: str
    event_head_hash: str

    def to_dict(self) -> dict[str, str]:
        return {
            "workspace_root": self.workspace_root,
            "run_id": self.run_id,
            "state_digest_sha256": self.state_digest_sha256,
            "event_head_hash": self.event_head_hash,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceIndexResult:
    scan_root: str
    workspaces: tuple[WorkspaceIndexEntry, ...]
    invalid_candidates: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "scan_root": self.scan_root,
            "workspaces": [item.to_dict() for item in self.workspaces],
            "invalid_candidates": [dict(item) for item in self.invalid_candidates],
        }


class WorkspaceIndex:
    """Build an index without creating, repairing, or changing a workspace."""

    @staticmethod
    def scan(root: str | Path) -> WorkspaceIndexResult:
        scan_root = Path(root).resolve()
        if not scan_root.is_dir():
            raise ValueError("workspace index scan root must be a directory")
        manifests = sorted(
            path for path in scan_root.rglob("workspace.json") if path.is_file()
        )
        entries: list[WorkspaceIndexEntry] = []
        invalid: list[dict[str, str]] = []
        seen: set[Path] = set()
        for manifest in manifests:
            candidate = manifest.parent.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                workspace = ResearchWorkspace.load(candidate)
                audit = workspace.audit()
                if not audit.valid:
                    raise ValueError("workspace audit failed")
                entries.append(
                    WorkspaceIndexEntry(
                        workspace_root=str(candidate),
                        run_id=workspace.trace.run_id,
                        state_digest_sha256=workspace.state_digest(),
                        event_head_hash=workspace.events.head_hash,
                    )
                )
            except (OSError, ValueError, KeyError) as exc:
                invalid.append({"workspace_root": str(candidate), "reason": str(exc)})
        entries.sort(key=lambda item: (item.run_id, item.workspace_root))
        invalid.sort(key=lambda item: item["workspace_root"])
        return WorkspaceIndexResult(str(scan_root), tuple(entries), tuple(invalid))
