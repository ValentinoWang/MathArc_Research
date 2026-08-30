"""Small independent checker for the RUP subset of LRAT proofs.

The checker deliberately shares no resolution-generation code with
``lrat_tools``. It accepts addition-only LRAT lines whose positive hints form
an explicit reverse-unit-propagation chain ending in contradiction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


class LratCheckError(ValueError):
    """Raised when an LRAT proof object is malformed or invalid."""


@dataclass(frozen=True, slots=True)
class LratStep:
    clause_id: int
    clause: tuple[int, ...]
    hints: tuple[int, ...]


def _normalize_clause(raw: Sequence[int], num_variables: int) -> tuple[int, ...]:
    literals: list[int] = []
    seen: set[int] = set()
    for literal in raw:
        if isinstance(literal, bool) or not isinstance(literal, int):
            raise LratCheckError("CNF literals must be integers")
        if literal == 0 or abs(literal) > num_variables:
            raise LratCheckError(
                f"literal {literal!r} is outside 1..{num_variables} or is zero"
            )
        if literal in seen:
            raise LratCheckError(f"duplicate literal {literal} in clause")
        if -literal in seen:
            raise LratCheckError("tautological clauses are not canonical proof objects")
        seen.add(literal)
        literals.append(literal)
    return tuple(sorted(literals, key=lambda item: (abs(item), item < 0)))


def parse_lrat(proof_text: str, num_variables: int) -> tuple[LratStep, ...]:
    """Parse the addition-only, positive-hint RUP subset of LRAT."""

    steps: list[LratStep] = []
    for line_number, raw_line in enumerate(proof_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("c "):
            continue
        if line.startswith("d "):
            raise LratCheckError("deletion lines are outside the supported LRAT subset")
        try:
            tokens = [int(item) for item in line.split()]
        except ValueError as exc:
            raise LratCheckError(f"line {line_number} contains a non-integer token") from exc
        if len(tokens) < 4 or tokens[0] <= 0:
            raise LratCheckError(f"line {line_number} is not an LRAT addition line")
        try:
            first_zero = tokens.index(0, 1)
            second_zero = tokens.index(0, first_zero + 1)
        except ValueError as exc:
            raise LratCheckError(f"line {line_number} lacks both LRAT terminators") from exc
        if second_zero != len(tokens) - 1:
            raise LratCheckError(f"line {line_number} has tokens after the hint terminator")
        hints = tuple(tokens[first_zero + 1 : second_zero])
        if not hints or any(item <= 0 for item in hints):
            raise LratCheckError(f"line {line_number} needs positive RUP hint IDs")
        if len(set(hints)) != len(hints):
            raise LratCheckError(f"line {line_number} repeats a hint ID")
        steps.append(
            LratStep(
                clause_id=tokens[0],
                clause=_normalize_clause(tokens[1:first_zero], num_variables),
                hints=hints,
            )
        )
    return tuple(steps)


def _literal_value(literal: int, assignment: Mapping[int, bool]) -> bool | None:
    value = assignment.get(abs(literal))
    if value is None:
        return None
    return value if literal > 0 else not value


def _rup_conflict(
    clauses: Mapping[int, tuple[int, ...]],
    candidate: tuple[int, ...],
    hints: tuple[int, ...],
) -> bool:
    assignment: dict[int, bool] = {}

    # RUP checks F entails C by unit-propagating F under the negation of C.
    for literal in candidate:
        variable = abs(literal)
        required = literal < 0
        previous = assignment.get(variable)
        if previous is not None and previous != required:
            return False
        assignment[variable] = required

    for hint_index, hint in enumerate(hints):
        try:
            clause = clauses[hint]
        except KeyError as exc:
            raise LratCheckError(f"RUP hint references unknown clause {hint}") from exc
        values = [_literal_value(literal, assignment) for literal in clause]
        if any(value is True for value in values):
            return False
        unresolved = [
            literal for literal, value in zip(clause, values, strict=True) if value is None
        ]
        if not unresolved:
            return hint_index == len(hints) - 1
        if len(unresolved) != 1:
            return False
        unit = unresolved[0]
        variable = abs(unit)
        required = unit > 0
        previous = assignment.get(variable)
        if previous is not None and previous != required:
            return hint_index == len(hints) - 1
        assignment[variable] = required
    return False


def check_lrat_proof(
    *,
    num_variables: int,
    clauses: Sequence[Sequence[int]],
    proof_text: str,
) -> dict[str, int | str | bool | None]:
    """Validate a CNF and an addition-only LRAT/RUP refutation."""

    if isinstance(num_variables, bool) or not isinstance(num_variables, int):
        raise LratCheckError("num_variables must be an integer")
    if not 1 <= num_variables <= 64:
        raise LratCheckError("num_variables must be between 1 and 64")
    if not clauses:
        raise LratCheckError("CNF must contain at least one clause")

    active: dict[int, tuple[int, ...]] = {}
    empty_clause_id: int | None = None
    for clause_id, raw_clause in enumerate(clauses, start=1):
        clause = _normalize_clause(raw_clause, num_variables)
        active[clause_id] = clause
        if not clause and empty_clause_id is None:
            empty_clause_id = clause_id

    steps = parse_lrat(proof_text, num_variables)
    last_clause_id = len(active)
    for step in steps:
        if step.clause_id <= last_clause_id:
            raise LratCheckError("LRAT addition IDs must be strictly increasing")
        if not _rup_conflict(active, step.clause, step.hints):
            raise LratCheckError(f"clause {step.clause_id} fails its RUP hint chain")
        active[step.clause_id] = step.clause
        last_clause_id = step.clause_id
        if not step.clause:
            empty_clause_id = step.clause_id

    if empty_clause_id is None:
        raise LratCheckError("LRAT proof does not derive the empty clause")

    return {
        "schema": "matharc.v03.lrat-rup-check.1",
        "valid": True,
        "input_clause_count": len(clauses),
        "added_clause_count": len(steps),
        "empty_clause_id": empty_clause_id,
        "proof_sha256": hashlib.sha256(proof_text.encode("utf-8")).hexdigest(),
    }
