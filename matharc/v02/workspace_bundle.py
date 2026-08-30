from __future__ import annotations

import json
from pathlib import Path

from .workspace_demo import build_workspace_demo
from .workspace_visualization import render_workspace_dashboard


def write_full_workspace_bundle(root: str | Path) -> dict[str, Path]:
    target = Path(root)
    workspace = build_workspace_demo(target)
    manifest = workspace.save()
    dashboard = render_workspace_dashboard(
        workspace,
        target / "workspace-dashboard.html",
        title="MathArc Research v0.2 · Full Research Observatory",
    )
    replay = target / "reproduce.sh"
    replay.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "ROOT=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
        "python examples/workspace_v02.py --out-dir \"$ROOT\" --verify\n",
        encoding="utf-8",
    )
    replay.chmod(0o755)
    report = target / "bundle-report.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "run_id": workspace.trace.run_id,
                "workspace_manifest": manifest.name,
                "dashboard": dashboard.name,
                "replay": replay.name,
                "state_digest_sha256": workspace.state_digest(),
                "event_head_hash": workspace.events.head_hash,
                "audit": workspace.audit().to_dict(),
                "claim_boundary": (
                    "The demo validates the MathArc workspace protocol on one deterministic theorem. "
                    "It is not a measured superiority result against external agents."
                ),
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
        "dashboard": dashboard,
        "replay": replay,
        "report": report,
        "event_ledger": target / "events.json",
        "audit": target / "audit.json",
        "object_registry": target / "objects.json",
        "source_registry": target / "sources.json",
        "artifact_manifest": target / "artifacts" / "manifest.json",
    }
