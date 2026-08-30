from __future__ import annotations

from typing import Any

from .engine import ResearchEngine
from .metrics import compute_metrics
from .models import ClaimStatus, ResearchRun


def validate_run(run: ResearchRun) -> dict[str, Any]:
    errors = ResearchEngine(run).validate()
    warnings: list[str] = []
    if not run.reasoning_cards:
        warnings.append("public structured reasoning trace is empty")
    if not run.tool_calls:
        warnings.append("tool-call ledger is empty")
    root = run.claims.get(run.contract.root_claim_id)
    if root and root.status is ClaimStatus.VERIFIED and run.release_state != "MACHINE_VERIFIED":
        warnings.append("root is verified but certificate debt prevents final release")
    metrics = compute_metrics(run)
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "run_id": run.run_id,
        "release_state": run.release_state,
        "certificate_debt": metrics["certificate_debt"],
        "theorem_closure_binary": metrics["theorem_closure_binary"],
    }
