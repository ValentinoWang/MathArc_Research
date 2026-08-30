from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_CLAIM = re.compile(r"\\claimid\s*\{([^{}]+)\}")
_REVISION = re.compile(r"\\claimrevision\s*\{(\d+)\}")


def parse_claim_map(path: str | Path) -> dict[str, int]:
    """Read a JSON claim map with explicit integer revisions."""
    import json
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("claim map must be an object")
    raw = value.get("claims", value)
    if not isinstance(raw, dict):
        raise ValueError("claim map claims must be an object")
    result: dict[str, int] = {}
    for claim_id, item in raw.items():
        if isinstance(item, dict):
            result[str(claim_id)] = int(item["revision"])
        else:
            result[str(claim_id)] = int(item)
    return result


def parse_latex_claims(path: str | Path) -> dict[str, int]:
    text = Path(path).read_text(encoding="utf-8")
    ids = list(_CLAIM.finditer(text))
    revisions = list(_REVISION.finditer(text))
    if len(ids) != len(revisions):
        raise ValueError("each LaTeX claimid must have exactly one claimrevision")
    return {match.group(1).strip(): int(revisions[index].group(1))
            for index, match in enumerate(ids)}


def check_bidirectional_claims(claim_map: dict[str, int], latex_claims: dict[str, int]) -> list[str]:
    errors: list[str] = []
    for claim_id in sorted(set(claim_map) - set(latex_claims)):
        errors.append(f"claim map claim {claim_id} is absent from LaTeX")
    for claim_id in sorted(set(latex_claims) - set(claim_map)):
        errors.append(f"LaTeX claim {claim_id} is absent from claim map")
    for claim_id in sorted(set(claim_map) & set(latex_claims)):
        if claim_map[claim_id] != latex_claims[claim_id]:
            errors.append(f"claim {claim_id} revision mismatch: map={claim_map[claim_id]} latex={latex_claims[claim_id]}")
    return errors
