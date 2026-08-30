"""Allowlisted exact-tool execution for the v0.2 campaign loop.

A worker's tool_requests reference a template_id and typed arguments -- never
a raw shell command -- and only templates registered here can run.  Each
execution produces a real ToolCallRecord and, when the check passes, a real
EvidenceRecord; both are digest-carrying and (for these pure-function exact
checks) genuinely cold-replayable.

This is deliberately small: two templates wrapping matharc.polynomial's
dependency-free exact arithmetic (the same logic matharc/tools.py wraps for
v0.1).  It is a first, real instance of the "unified evaluator interface"
the improvement plan calls for (docs/IMPROVEMENT_PLAN_V03.md, W3-2/W2-7), not
that interface itself -- a generic Evaluator protocol with cost/tier
declarations, SAT/SMT/CAS adapters, and a dual-implementation verifier
synthesis gate remain future work.
"""

from __future__ import annotations

import shlex
import sys
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from matharc.polynomial import PolynomialError, identity_certificate, parse_polynomial

from .schema import (
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ToolCallRecord,
    ToolStatus,
    digest_json,
    utc_now,
)


class UnknownExactToolError(ValueError):
    """Raised when a proposal references a tool template outside the allowlist."""


class ExactToolArgumentError(ValueError):
    """Raised when a proposal's tool_request arguments are malformed."""


class ExactToolUnavailableError(ValueError):
    """Raised when a registered template's optional backend is not installed."""


@dataclass(slots=True)
class ExactToolResult:
    tool_call: ToolCallRecord
    evidence: EvidenceRecord | None


_ExactToolFn = Callable[..., ExactToolResult]


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# These exact tools are pure stdlib Fraction arithmetic (matharc.polynomial):
# no OS, filesystem, or third-party state affects the result, so the
# environment digest only needs to capture the interpreter's major.minor
# version, not a full environment snapshot.
_ENVIRONMENT_DIGEST = digest_json(
    {"module": "matharc.polynomial", "python": f"{sys.version_info.major}.{sys.version_info.minor}"}
)


def _polynomial_identity(
    *, claim_id: str, arguments: Mapping[str, Any]
) -> ExactToolResult:
    try:
        lhs = str(arguments["lhs"])
        rhs = str(arguments["rhs"])
    except KeyError as exc:
        raise ExactToolArgumentError(f"polynomial_identity requires {exc}") from exc
    variable = str(arguments.get("variable", "n"))
    started = utc_now()
    input_digest = digest_json({"lhs": lhs, "rhs": rhs, "variable": variable})
    try:
        output = identity_certificate(lhs, rhs, variable)
    except PolynomialError as exc:
        raise ExactToolArgumentError(str(exc)) from exc
    ended = utc_now()
    output_digest = digest_json(output)
    valid = bool(output["valid"])
    replay_command = "python -c " + shlex.quote(
        "from matharc.polynomial import identity_certificate as f; "
        f"print(f({lhs!r}, {rhs!r}, {variable!r}))"
    )
    independence_group = "exact:polynomial_identity:matharc.polynomial"
    tool_call = ToolCallRecord(
        call_id=_new_id("EXACT-POLY"),
        tool="exact:polynomial_identity",
        purpose=f"Exact coefficient-wise identity check for claim {claim_id}.",
        status=ToolStatus.PASS if valid else ToolStatus.FAIL,
        input_digest_sha256=input_digest,
        output_digest_sha256=output_digest,
        linked_claim_ids=(claim_id,),
        independence_group=independence_group,
        replay_command=replay_command,
        started_at=started,
        ended_at=ended,
        environment_digest_sha256=_ENVIRONMENT_DIGEST,
        expected_discriminator="difference_coefficients are all exactly zero",
    )
    evidence = None
    if valid:
        evidence = EvidenceRecord(
            evidence_id=_new_id("EVIDENCE-POLY"),
            claim_ids=(claim_id,),
            kind=EvidenceKind.EXACT_CERTIFICATE,
            status=EvidenceStatus.ACCEPTED,
            summary=f"Exact polynomial identity holds: {lhs} = {rhs} over {variable}.",
            artifact_uri="",
            digest_sha256=output_digest,
            producer="exact-tool:polynomial_identity",
            verifier="exact-tool:polynomial_identity",
            independence_group=independence_group,
            replay_command=replay_command,
            statement_correspondence=(
                f"The identity '{lhs} = {rhs}' over {variable} is exactly the claim's statement."
            ),
        )
    return ExactToolResult(tool_call=tool_call, evidence=evidence)


def _induction_certificate(
    *, claim_id: str, arguments: Mapping[str, Any]
) -> ExactToolResult:
    try:
        certificate = arguments["certificate"]
    except KeyError as exc:
        raise ExactToolArgumentError("induction_certificate requires 'certificate'") from exc
    if not isinstance(certificate, Mapping):
        raise ExactToolArgumentError("certificate must be an object")
    variable = str(certificate.get("variable", "n"))
    try:
        base = certificate["base"]
        step = certificate["step"]
        base_n = int(base["at"])
        base_lhs_expr = str(base["lhs"])
        base_rhs_expr = str(base["rhs"])
        step_lhs = str(step["lhs"])
        step_rhs = str(step["rhs"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ExactToolArgumentError(f"malformed induction certificate: {exc}") from exc
    started = utc_now()
    input_digest = digest_json(dict(certificate))
    try:
        base_lhs = parse_polynomial(base_lhs_expr, variable).evaluate(base_n)
        base_rhs = parse_polynomial(base_rhs_expr, variable).evaluate(base_n)
        step_check = identity_certificate(step_lhs, step_rhs, variable)
    except PolynomialError as exc:
        raise ExactToolArgumentError(str(exc)) from exc
    ended = utc_now()
    base_valid = base_lhs == base_rhs
    step_valid = bool(step_check["valid"])
    valid = base_valid and step_valid
    output = {
        "schema": "matharc.v02.induction-certificate.1",
        "variable": variable,
        "base": {"at": base_n, "lhs_value": str(base_lhs), "rhs_value": str(base_rhs), "valid": base_valid},
        "step": step_check,
        "valid": valid,
        "principle": "ordinary mathematical induction on natural numbers",
    }
    output_digest = digest_json(output)
    replay_command = "python -c " + shlex.quote(
        "from matharc.v02.exact_tools import _induction_certificate as f; "
        f"print(f(claim_id={claim_id!r}, arguments={{'certificate': {dict(certificate)!r}}}))"
    )
    independence_group = "exact:induction_certificate:matharc.polynomial"
    tool_call = ToolCallRecord(
        call_id=_new_id("EXACT-IND"),
        tool="exact:induction_certificate",
        purpose=f"Exact base+step induction check for claim {claim_id}.",
        status=ToolStatus.PASS if valid else ToolStatus.FAIL,
        input_digest_sha256=input_digest,
        output_digest_sha256=output_digest,
        linked_claim_ids=(claim_id,),
        independence_group=independence_group,
        replay_command=replay_command,
        started_at=started,
        ended_at=ended,
        environment_digest_sha256=_ENVIRONMENT_DIGEST,
        expected_discriminator="base values agree exactly and the step difference is exactly zero",
    )
    evidence = None
    if valid:
        evidence = EvidenceRecord(
            evidence_id=_new_id("EVIDENCE-IND"),
            claim_ids=(claim_id,),
            kind=EvidenceKind.EXACT_CERTIFICATE,
            status=EvidenceStatus.ACCEPTED,
            summary=(
                f"Base case at {variable}={base_n} holds and the induction step "
                f"'{step_lhs} = {step_rhs}' is an exact polynomial identity."
            ),
            artifact_uri="",
            digest_sha256=output_digest,
            producer="exact-tool:induction_certificate",
            verifier="exact-tool:induction_certificate",
            independence_group=independence_group,
            replay_command=replay_command,
            statement_correspondence=(
                "The certificate's base case and induction step are exactly the "
                "claim's base and step obligations."
            ),
        )
    return ExactToolResult(tool_call=tool_call, evidence=evidence)


class ExactToolRegistry:
    """Allowlist of template_id -> exact-tool implementation."""

    def __init__(self, tools: Mapping[str, _ExactToolFn] | None = None) -> None:
        self._tools: dict[str, _ExactToolFn] = dict(
            tools
            if tools is not None
            else {
                "polynomial_identity": _polynomial_identity,
                "induction_certificate": _induction_certificate,
            }
        )

    def template_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def register(self, template_id: str, fn: _ExactToolFn) -> None:
        if template_id in self._tools:
            raise ValueError(f"duplicate exact tool template: {template_id!r}")
        self._tools[template_id] = fn

    def execute(
        self,
        template_id: str,
        *,
        claim_id: str,
        arguments: Mapping[str, Any],
    ) -> ExactToolResult:
        try:
            fn = self._tools[template_id]
        except KeyError as exc:
            raise UnknownExactToolError(
                f"unknown exact tool template {template_id!r}; available={self.template_ids()}"
            ) from exc
        return fn(claim_id=claim_id, arguments=arguments)


def default_exact_tool_registry() -> ExactToolRegistry:
    # Imported lazily to avoid a module cycle (smt_tools reuses this module's
    # result/error types).  The SMT templates are registered even when z3 is
    # absent: executing one then raises ExactToolUnavailableError, which the
    # campaign reports per request instead of crashing the round.
    from .lrat_tools import cnf_lrat_unsat
    from .smt_tools import smt_existential_witness, smt_universal_no_counterexample

    registry = ExactToolRegistry()
    registry.register("smt_universal_no_counterexample", smt_universal_no_counterexample)
    registry.register("smt_existential_witness", smt_existential_witness)
    registry.register("cnf_lrat_unsat", cnf_lrat_unsat)
    return registry
