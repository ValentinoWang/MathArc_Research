"""Bounded CNF resolution producer with an independently checked LRAT object.

This is a deliberately narrow V3 first slice. It handles canonical
propositional CNF only. It does not translate or upgrade the existing Z3
integer-arithmetic UNSAT path.
"""

from __future__ import annotations

import argparse
import base64
import json
import shlex
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from .exact_tools import ExactToolArgumentError, ExactToolResult, _new_id
from .lrat_checker import LratCheckError, check_lrat_proof
from .schema import (
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ToolCallRecord,
    ToolStatus,
    canonical_json,
    digest_json,
    utc_now,
)

_MAX_VARIABLES = 64
_MAX_INITIAL_CLAUSES = 256
_MAX_CLAUSE_LENGTH = 64
_DEFAULT_MAX_DERIVED = 4_096
_MAX_DERIVED = 20_000
_DEFAULT_MAX_RESOLUTION_PAIRS = 100_000
_MAX_RESOLUTION_PAIRS = 5_000_000


def _canonical_clause(raw: Any, num_variables: int) -> tuple[int, ...]:
    if not isinstance(raw, list):
        raise ExactToolArgumentError("each CNF clause must be an array")
    if len(raw) > _MAX_CLAUSE_LENGTH:
        raise ExactToolArgumentError(
            f"CNF clauses may contain at most {_MAX_CLAUSE_LENGTH} literals"
        )
    literals: list[int] = []
    seen: set[int] = set()
    for literal in raw:
        if isinstance(literal, bool) or not isinstance(literal, int):
            raise ExactToolArgumentError("CNF literals must be integers")
        if literal == 0 or abs(literal) > num_variables:
            raise ExactToolArgumentError(
                f"literal {literal!r} is outside 1..{num_variables} or is zero"
            )
        if literal in seen:
            raise ExactToolArgumentError(f"duplicate literal {literal} in clause")
        if -literal in seen:
            raise ExactToolArgumentError("tautological CNF clauses are not canonical")
        seen.add(literal)
        literals.append(literal)
    return tuple(sorted(literals, key=lambda item: (abs(item), item < 0)))


def _parse_arguments(
    arguments: Mapping[str, Any],
) -> tuple[int, tuple[tuple[int, ...], ...], int, int]:
    num_variables = arguments.get("num_variables")
    if isinstance(num_variables, bool) or not isinstance(num_variables, int):
        raise ExactToolArgumentError("num_variables must be an integer")
    if not 1 <= num_variables <= _MAX_VARIABLES:
        raise ExactToolArgumentError(
            f"num_variables must be between 1 and {_MAX_VARIABLES}"
        )
    raw_clauses = arguments.get("clauses")
    if not isinstance(raw_clauses, list) or not raw_clauses:
        raise ExactToolArgumentError("clauses must be a non-empty array")
    if len(raw_clauses) > _MAX_INITIAL_CLAUSES:
        raise ExactToolArgumentError(
            f"at most {_MAX_INITIAL_CLAUSES} initial clauses are supported"
        )
    clauses = tuple(
        sorted(
            (_canonical_clause(item, num_variables) for item in raw_clauses),
            key=lambda item: (len(item), item),
        )
    )
    if len(set(clauses)) != len(clauses):
        raise ExactToolArgumentError("duplicate CNF clauses are not canonical")

    max_derived = arguments.get("max_derived_clauses", _DEFAULT_MAX_DERIVED)
    if isinstance(max_derived, bool) or not isinstance(max_derived, int):
        raise ExactToolArgumentError("max_derived_clauses must be an integer")
    if not 1 <= max_derived <= _MAX_DERIVED:
        raise ExactToolArgumentError(
            f"max_derived_clauses must be between 1 and {_MAX_DERIVED}"
        )
    max_resolution_pairs = arguments.get(
        "max_resolution_pairs", _DEFAULT_MAX_RESOLUTION_PAIRS
    )
    if isinstance(max_resolution_pairs, bool) or not isinstance(max_resolution_pairs, int):
        raise ExactToolArgumentError("max_resolution_pairs must be an integer")
    if not 1 <= max_resolution_pairs <= _MAX_RESOLUTION_PAIRS:
        raise ExactToolArgumentError(
            f"max_resolution_pairs must be between 1 and {_MAX_RESOLUTION_PAIRS}"
        )
    return num_variables, clauses, max_derived, max_resolution_pairs


def _resolvents(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    right_set = set(right)
    derived: list[tuple[int, ...]] = []
    for pivot in left:
        if -pivot not in right_set:
            continue
        candidate = (set(left) - {pivot}) | (right_set - {-pivot})
        if any(-literal in candidate for literal in candidate):
            continue
        derived.append(tuple(sorted(candidate, key=lambda item: (abs(item), item < 0))))
    return tuple(dict.fromkeys(derived))


def _produce_lrat(
    clauses: tuple[tuple[int, ...], ...],
    max_derived: int,
    max_resolution_pairs: int,
) -> tuple[str, str, int | None, int]:
    clause_ids: dict[tuple[int, ...], int] = {}
    by_id: dict[int, tuple[int, ...]] = {}
    ordered_ids: list[int] = []
    for clause_id, clause in enumerate(clauses, start=1):
        clause_ids[clause] = clause_id
        by_id[clause_id] = clause
        ordered_ids.append(clause_id)
        if not clause:
            return "unsat", "", clause_id, 0

    proof_lines: list[str] = []
    derived_count = 0
    resolution_pairs = 0
    left_index = 0
    while left_index < len(ordered_ids):
        left_id = ordered_ids[left_index]
        right_index = left_index + 1
        while right_index < len(ordered_ids):
            if resolution_pairs >= max_resolution_pairs:
                return (
                    "resource_limit",
                    "\n".join(proof_lines) + "\n",
                    None,
                    resolution_pairs,
                )
            right_id = ordered_ids[right_index]
            resolution_pairs += 1
            for resolvent in _resolvents(by_id[left_id], by_id[right_id]):
                if resolvent in clause_ids:
                    continue
                if derived_count >= max_derived:
                    return (
                        "resource_limit",
                        "\n".join(proof_lines) + "\n",
                        None,
                        resolution_pairs,
                    )
                clause_id = len(by_id) + 1
                clause_ids[resolvent] = clause_id
                by_id[clause_id] = resolvent
                ordered_ids.append(clause_id)
                derived_count += 1
                literals = " ".join(str(item) for item in resolvent)
                prefix = f"{clause_id} {literals} 0" if literals else f"{clause_id} 0"
                proof_lines.append(f"{prefix} {left_id} {right_id} 0")
                if not resolvent:
                    return (
                        "unsat",
                        "\n".join(proof_lines) + "\n",
                        clause_id,
                        resolution_pairs,
                    )
            right_index += 1
        left_index += 1
    return (
        "saturated_without_empty",
        "\n".join(proof_lines) + "\n",
        None,
        resolution_pairs,
    )


def build_cnf_lrat_artifact(arguments: Mapping[str, Any]) -> dict[str, Any]:
    """Build and independently check a bounded CNF/LRAT evidence artifact."""

    num_variables, clauses, max_derived, max_resolution_pairs = _parse_arguments(arguments)
    producer_status, proof_text, empty_clause_id, resolution_pairs = _produce_lrat(
        clauses,
        max_derived,
        max_resolution_pairs,
    )
    checker: dict[str, Any]
    if producer_status == "unsat":
        try:
            checker = check_lrat_proof(
                num_variables=num_variables,
                clauses=clauses,
                proof_text=proof_text,
            )
        except LratCheckError as exc:
            checker = {
                "schema": "matharc.v03.lrat-rup-check.1",
                "valid": False,
                "error": str(exc),
            }
    else:
        checker = {
            "schema": "matharc.v03.lrat-rup-check.1",
            "valid": False,
            "error": "producer did not derive an empty clause",
        }
    return {
        "schema": "matharc.v03.cnf-lrat-evidence.1",
        "cnf": {
            "format": "canonical-dimacs-literals",
            "num_variables": num_variables,
            "clauses": [list(item) for item in clauses],
        },
        "producer": {
            "algorithm": "deterministic-resolution-closure-v1",
            "status": producer_status,
            "max_derived_clauses": max_derived,
            "max_resolution_pairs": max_resolution_pairs,
            "resolution_pairs_examined": resolution_pairs,
            "empty_clause_id": empty_clause_id,
        },
        "proof": {
            "format": "LRAT-RUP-addition-subset",
            "text": proof_text,
        },
        "checker": checker,
        "claim_boundary": (
            "This object proves only unsatisfiability of the embedded propositional CNF. "
            "It does not translate or strengthen any Z3 integer-arithmetic verdict."
        ),
    }


def cnf_lrat_unsat(*, claim_id: str, arguments: Mapping[str, Any]) -> ExactToolResult:
    """Produce CNF UNSAT evidence only after an independent LRAT/RUP check."""

    started = utc_now()
    artifact = build_cnf_lrat_artifact(arguments)
    ended = utc_now()
    artifact_json = canonical_json(artifact)
    artifact_digest = digest_json(artifact)
    producer_status = str(artifact["producer"]["status"])
    checker_valid = bool(artifact["checker"].get("valid"))
    if producer_status == "unsat" and checker_valid:
        status = ToolStatus.PASS
    elif producer_status == "saturated_without_empty":
        status = ToolStatus.FAIL
    else:
        status = ToolStatus.ERROR

    replay_arguments = canonical_json(dict(arguments))
    replay_command = "python -m matharc.v02.lrat_tools --arguments-json " + shlex.quote(
        replay_arguments
    )
    independence_group = "sat:cnf-lrat:resolution-producer+independent-rup-checker-v1"
    tool_call = ToolCallRecord(
        call_id=_new_id("EXACT-LRAT"),
        tool="exact:cnf_lrat_unsat",
        purpose=f"Generate and independently check a CNF LRAT refutation for {claim_id}.",
        status=status,
        input_digest_sha256=digest_json(dict(arguments)),
        output_digest_sha256=artifact_digest,
        linked_claim_ids=(claim_id,),
        independence_group=independence_group,
        replay_command=replay_command,
        started_at=started,
        ended_at=ended,
        environment_digest_sha256=digest_json(
            {
                "producer": "matharc.v02.lrat_tools",
                "checker": "matharc.v02.lrat_checker",
                "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            }
        ),
        expected_discriminator=(
            "the producer derives an empty clause and the separate LRAT/RUP checker "
            "accepts every hinted addition"
        ),
    )
    if status is not ToolStatus.PASS:
        return ExactToolResult(tool_call=tool_call, evidence=None)

    artifact_uri = "data:application/vnd.matharc.cnf-lrat+json;base64," + base64.b64encode(
        artifact_json.encode("utf-8")
    ).decode("ascii")
    evidence = EvidenceRecord(
        evidence_id=_new_id("EVIDENCE-LRAT"),
        claim_ids=(claim_id,),
        kind=EvidenceKind.EXACT_CERTIFICATE,
        status=EvidenceStatus.ACCEPTED,
        summary="The embedded propositional CNF has an independently checked LRAT refutation.",
        artifact_uri=artifact_uri,
        digest_sha256=artifact_digest,
        producer="sat:deterministic-resolution-closure-v1",
        verifier="lrat-checker:independent-rup-v1",
        independence_group=independence_group,
        replay_command=replay_command,
        statement_correspondence=(
            "The evidence establishes UNSAT only for the exact canonical CNF embedded "
            "in the content-addressed artifact."
        ),
        assumptions_checked=(
            "all literals are nonzero integers within the declared variable range",
            "every LRAT addition passes its explicit RUP hint chain",
            "the checked proof derives the empty clause",
        ),
        limitations=(
            "propositional CNF only; no SMT or integer-arithmetic translation is implied",
            "the deterministic resolution producer is bounded and intended for small certificates",
            "the checker supports the addition-only positive-hint RUP subset of LRAT",
        ),
    )
    return ExactToolResult(tool_call=tool_call, evidence=evidence)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arguments-json", required=True)
    args = parser.parse_args(argv)
    raw = json.loads(args.arguments_json)
    if not isinstance(raw, Mapping):
        raise SystemExit("arguments JSON must be an object")
    artifact = build_cnf_lrat_artifact(raw)
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0 if artifact["checker"].get("valid") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
