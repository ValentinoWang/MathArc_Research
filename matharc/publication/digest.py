from __future__ import annotations

from typing import Any

from ..v02.schema import digest_json


def sha256_json(value: Any) -> str:
    """Return the canonical SHA-256 used by all MathArc publication records."""
    return digest_json(value)


__all__ = ["sha256_json"]
