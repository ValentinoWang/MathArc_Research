from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_CLAIM = re.compile(r"\\claimid\s*\{([^{}]+)\}")
_REVISION = re.compile(r"\\claimrevision\s*\{(\d+)\}")
_COMBINED = re.compile(r"\\matharcclaim\s*\{([^{}]+)\}\s*\{(\d+)\}")
_MACRO = re.compile(r"\\(?:matharcclaim|claimid|claimrevision)\b")


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


def parse_latex_claims_text(text: str) -> dict[str, int]:
    """Parse combined claims or strictly adjacent legacy claim macros."""
    result: dict[str, int] = {}
    covered: list[tuple[int, int]] = []
    for match in _COMBINED.finditer(text):
        claim_id = match.group(1).strip()
        if claim_id in result:
            raise ValueError(f"duplicate LaTeX claim id: {claim_id}")
        result[claim_id] = int(match.group(2))
        covered.append(match.span())
    tokens = list(_MACRO.finditer(text))
    for index, token in enumerate(tokens):
        if any(start <= token.start() < end for start, end in covered):
            continue
        name = token.group(0)
        if name == r"\matharcclaim":
            raise ValueError("malformed matharcclaim macro; expected {id}{revision}")
        if name == r"\claimid":
            claim = _CLAIM.match(text, token.start())
            if claim is None:
                raise ValueError("malformed claimid macro")
            next_token = tokens[index + 1] if index + 1 < len(tokens) else None
            if next_token is None or next_token.group(0) != r"\claimrevision":
                raise ValueError("claimid must be immediately followed by claimrevision")
            if text[claim.end():next_token.start()].strip():
                raise ValueError("claimid must be immediately followed by claimrevision")
            revision = _REVISION.match(text, next_token.start())
            if revision is None:
                raise ValueError("malformed claimrevision macro")
            claim_id = claim.group(1).strip()
            if claim_id in result:
                raise ValueError(f"duplicate LaTeX claim id: {claim_id}")
            result[claim_id] = int(revision.group(1))
        elif name == r"\claimrevision":
            previous = tokens[index - 1] if index else None
            if previous is None or previous.group(0) != r"\claimid":
                raise ValueError("claimrevision must follow claimid")
    return result


def parse_latex_claims(path: str | Path, *, text: str | None = None) -> dict[str, int]:
    return parse_latex_claims_text(Path(path).read_text(encoding="utf-8") if text is None else text)


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
