"""Failure-memory compatibility package.

The package form takes precedence over the original module name and re-exports
the implementation from a private module.  The v0.2 public class lowers the
transparent lexical floor for sparse mathematical queries; exact-witness and
failure-class bonuses still determine whether a weak lexical match is useful.
"""

from __future__ import annotations

from typing import Iterable

from .._failure_memory_impl import FailureLesson, FailureMatch
from .._failure_memory_impl import FailureMemory as _FailureMemoryImpl
from ..schema import FailureClass


class FailureMemory(_FailureMemoryImpl):
    def query(
        self,
        statement: str,
        *,
        mechanism_signature: Iterable[str] = (),
        failure_class: FailureClass | None = None,
        top_k: int = 5,
        minimum_score: float = 0.04,
    ) -> list[FailureMatch]:
        return super().query(
            statement,
            mechanism_signature=mechanism_signature,
            failure_class=failure_class,
            top_k=top_k,
            minimum_score=minimum_score,
        )


__all__ = ["FailureLesson", "FailureMatch", "FailureMemory"]
