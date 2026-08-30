"""SMT (z3) exact-tool templates: bounded verification without a proof assistant.

This is the W2-7 middle rung from docs/IMPROVEMENT_PLAN_V03.md: between pure
enumeration (exact_tools.py) and a full Lean pipeline sit decidable-fragment
and bounded claims -- "for every x in [0, N] the formula holds", "a witness
with these properties exists" -- that an SMT solver settles symbolically.

Trust semantics are deliberately asymmetric, following the repo's
generator/checker-independence doctrine and the SOLVER_UNKNOWN_PROMOTION
failure class:

- ``unknown`` (including timeout) is a hard block: ToolStatus.ERROR and no
  evidence, ever.  An inconclusive solver run must never look like progress.
- A ``sat`` model is never trusted from z3 alone: it is re-checked by an
  independent pure-Python integer evaluator in this module (no z3 involved).
  Only a model that survives that second, independent check can become
  EXACT_CERTIFICATE evidence (existential claims) or refute a universal
  claim.  If the two checkers disagree, the result is ERROR -- checker
  disagreement is a NON_INDEPENDENT_CHECKER incident, not evidence for
  either side.
- An ``unsat`` verdict supporting a universal claim has no independently
  checkable object (no DRAT/proof-term path here yet), so its evidence is
  EXACT_COMPUTATION with producer == verifier == z3 and an explicit
  limitation recorded; the existing trace validation surfaces exactly this
  self-verification, and a critical claim still cannot close on it alone.
- A counterexample against a universal claim is reported as a FAILing tool
  call with the verified model in its output -- deliberately NOT as an
  EvidenceRecord.  Evidence attached to a claim counts as supporting it in
  the promotion gate, so recording refutation there would be a laundering
  channel.  Wiring counterexamples into FailureRecord cascades is the
  FalsificationEngine work item (W2-2), not this module.

Formulas arrive as a small JSON AST over declared integer variables with
optional bounds -- never as solver-syntax strings from a worker -- and both
the z3 translation and the independent evaluator consume that same AST.

z3 is an optional dependency (the ``formal`` extra).  The templates are
registered unconditionally; executing them without z3 installed raises
ExactToolUnavailableError, which the campaign reports without crashing.
"""

from __future__ import annotations

import importlib
import json
import shlex
from typing import Any, Mapping

from .exact_tools import (
    ExactToolArgumentError,
    ExactToolResult,
    ExactToolUnavailableError,
    _new_id,
)
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

_MAX_NODES = 2_000
_MAX_DEPTH = 64
_MAX_VARIABLES = 32
_DEFAULT_TIMEOUT_MS = 10_000
_MAX_TIMEOUT_MS = 600_000

_BOOL_OPS = {"and", "or", "not", "implies"}
_CMP_OPS = {"le", "lt", "ge", "gt", "eq", "ne"}
_TERM_OPS = {"add", "sub", "mul", "neg"}


def _load_z3() -> Any:
    try:
        return importlib.import_module("z3")
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ExactToolUnavailableError(
            "z3-solver is not installed; install the 'formal' extra "
            "(pip install 'matharc-research[formal]') to use SMT templates"
        ) from exc


# ---------------------------------------------------------------------------
# Variable declarations and formula AST
# ---------------------------------------------------------------------------


def _parse_variables(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise ExactToolArgumentError("'variables' must be a non-empty array")
    if len(raw) > _MAX_VARIABLES:
        raise ExactToolArgumentError(f"at most {_MAX_VARIABLES} variables are supported")
    seen: set[str] = set()
    variables: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping) or "name" not in item:
            raise ExactToolArgumentError("each variable needs at least a 'name'")
        name = str(item["name"])
        if not name.isidentifier():
            raise ExactToolArgumentError(f"variable name is not an identifier: {name!r}")
        if name in seen:
            raise ExactToolArgumentError(f"duplicate variable name: {name!r}")
        seen.add(name)
        lower = item.get("lower")
        upper = item.get("upper")
        if lower is not None and not isinstance(lower, int):
            raise ExactToolArgumentError(f"lower bound of {name!r} must be an integer")
        if upper is not None and not isinstance(upper, int):
            raise ExactToolArgumentError(f"upper bound of {name!r} must be an integer")
        if lower is not None and upper is not None and lower > upper:
            raise ExactToolArgumentError(f"empty bound interval for {name!r}: [{lower}, {upper}]")
        variables.append({"name": name, "lower": lower, "upper": upper})
    return variables


def _validate_formula(node: Any, names: frozenset[str]) -> None:
    count = 0

    def visit(item: Any, depth: int) -> None:
        nonlocal count
        count += 1
        if count > _MAX_NODES:
            raise ExactToolArgumentError(f"formula exceeds {_MAX_NODES} nodes")
        if depth > _MAX_DEPTH:
            raise ExactToolArgumentError(f"formula exceeds depth {_MAX_DEPTH}")
        if not isinstance(item, Mapping):
            raise ExactToolArgumentError(f"formula node must be an object: {item!r}")
        if "var" in item:
            name = str(item["var"])
            if name not in names:
                raise ExactToolArgumentError(f"undeclared variable in formula: {name!r}")
            return
        if "const" in item:
            if not isinstance(item["const"], int):
                raise ExactToolArgumentError(f"'const' must be an integer: {item['const']!r}")
            return
        op = item.get("op")
        args = item.get("args")
        if not isinstance(op, str) or not isinstance(args, list):
            raise ExactToolArgumentError(f"formula node needs 'op' and 'args': {item!r}")
        arity_ok = (
            (op in {"not", "neg"} and len(args) == 1)
            or (op in _CMP_OPS | {"implies", "sub"} and len(args) == 2)
            or (op in {"and", "or", "add", "mul"} and len(args) >= 2)
        )
        if op not in _BOOL_OPS | _CMP_OPS | _TERM_OPS or not arity_ok:
            raise ExactToolArgumentError(f"unsupported op/arity: {op!r} with {len(args)} args")
        for arg in args:
            visit(arg, depth + 1)

    visit(node, 0)


def _is_term(node: Mapping[str, Any]) -> bool:
    if "var" in node or "const" in node:
        return True
    return str(node.get("op")) in _TERM_OPS


def _eval_term(node: Mapping[str, Any], assignment: Mapping[str, int]) -> int:
    if "var" in node:
        return assignment[str(node["var"])]
    if "const" in node:
        return int(node["const"])
    op = str(node["op"])
    args = [_eval_term(arg, assignment) for arg in node["args"]]
    if op == "add":
        return sum(args)
    if op == "mul":
        product = 1
        for value in args:
            product *= value
        return product
    if op == "sub":
        return args[0] - args[1]
    if op == "neg":
        return -args[0]
    raise ExactToolArgumentError(f"not an integer term: {op!r}")


def eval_formula(node: Mapping[str, Any], assignment: Mapping[str, int]) -> bool:
    """Independently evaluate a validated formula at an integer assignment.

    Pure Python integer arithmetic; shares no code with the z3 translation,
    so it can serve as the second, independent checker of a z3 model.
    """

    op = str(node.get("op"))
    if op == "and":
        return all(eval_formula(arg, assignment) for arg in node["args"])
    if op == "or":
        return any(eval_formula(arg, assignment) for arg in node["args"])
    if op == "not":
        return not eval_formula(node["args"][0], assignment)
    if op == "implies":
        return (not eval_formula(node["args"][0], assignment)) or eval_formula(
            node["args"][1], assignment
        )
    if op in _CMP_OPS:
        left = _eval_term(node["args"][0], assignment)
        right = _eval_term(node["args"][1], assignment)
        if op == "le":
            return left <= right
        if op == "lt":
            return left < right
        if op == "ge":
            return left >= right
        if op == "gt":
            return left > right
        if op == "eq":
            return left == right
        return left != right
    raise ExactToolArgumentError(f"not a boolean formula node: {node!r}")


def _render(node: Mapping[str, Any]) -> str:
    if "var" in node:
        return str(node["var"])
    if "const" in node:
        return str(node["const"])
    op = str(node["op"])
    parts = [_render(arg) for arg in node["args"]]
    symbol = {
        "and": " and ",
        "or": " or ",
        "implies": " -> ",
        "add": " + ",
        "mul": " * ",
        "sub": " - ",
        "le": " <= ",
        "lt": " < ",
        "ge": " >= ",
        "gt": " > ",
        "eq": " = ",
        "ne": " != ",
    }.get(op)
    if op in {"not", "neg"}:
        return f"{'not ' if op == 'not' else '-'}({parts[0]})"
    if symbol is None:
        raise ExactToolArgumentError(f"unsupported op: {op!r}")
    return "(" + symbol.join(parts) + ")"


def _domain_text(variables: list[dict[str, Any]]) -> str:
    pieces = []
    for item in variables:
        lower = item["lower"] if item["lower"] is not None else "-inf"
        upper = item["upper"] if item["upper"] is not None else "+inf"
        pieces.append(f"{item['name']} in [{lower}, {upper}]")
    return ", ".join(pieces)


# ---------------------------------------------------------------------------
# z3 translation and the patchable solver seam
# ---------------------------------------------------------------------------


def _to_z3(z3mod: Any, node: Mapping[str, Any], z3vars: Mapping[str, Any]) -> Any:
    if "var" in node:
        return z3vars[str(node["var"])]
    if "const" in node:
        return z3mod.IntVal(int(node["const"]))
    op = str(node["op"])
    args = [_to_z3(z3mod, arg, z3vars) for arg in node["args"]]
    if op == "and":
        return z3mod.And(*args)
    if op == "or":
        return z3mod.Or(*args)
    if op == "not":
        return z3mod.Not(args[0])
    if op == "implies":
        return z3mod.Implies(args[0], args[1])
    if op == "add":
        return z3mod.Sum(args)
    if op == "mul":
        product = args[0]
        for value in args[1:]:
            product = product * value
        return product
    if op == "sub":
        return args[0] - args[1]
    if op == "neg":
        return -args[0]
    if op == "le":
        return args[0] <= args[1]
    if op == "lt":
        return args[0] < args[1]
    if op == "ge":
        return args[0] >= args[1]
    if op == "gt":
        return args[0] > args[1]
    if op == "eq":
        return args[0] == args[1]
    if op == "ne":
        return args[0] != args[1]
    raise ExactToolArgumentError(f"unsupported op: {op!r}")


def _run_solver(
    variables: list[dict[str, Any]],
    goal: Mapping[str, Any],
    timeout_ms: int,
) -> tuple[str, dict[str, int] | None]:
    """Solve ``bounds AND goal``; return ("sat"|"unsat"|"unknown", model).

    Kept as a module-level seam so tests can patch it to exercise the
    ``unknown`` branch deterministically.
    """

    z3mod = _load_z3()
    z3vars = {item["name"]: z3mod.Int(item["name"]) for item in variables}
    solver = z3mod.Solver()
    solver.set("timeout", timeout_ms)
    for item in variables:
        if item["lower"] is not None:
            solver.add(z3vars[item["name"]] >= z3mod.IntVal(item["lower"]))
        if item["upper"] is not None:
            solver.add(z3vars[item["name"]] <= z3mod.IntVal(item["upper"]))
    solver.add(_to_z3(z3mod, goal, z3vars))
    verdict = solver.check()
    if verdict == z3mod.sat:
        raw = solver.model()
        model = {
            name: raw.eval(z3var, model_completion=True).as_long()
            for name, z3var in z3vars.items()
        }
        return "sat", model
    if verdict == z3mod.unsat:
        return "unsat", None
    return "unknown", None


def _model_in_bounds(variables: list[dict[str, Any]], model: Mapping[str, int]) -> bool:
    for item in variables:
        value = model[item["name"]]
        if item["lower"] is not None and value < item["lower"]:
            return False
        if item["upper"] is not None and value > item["upper"]:
            return False
    return True


# ---------------------------------------------------------------------------
# Shared parsing and record assembly
# ---------------------------------------------------------------------------


def _parse_common(
    arguments: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    try:
        variables = _parse_variables(arguments["variables"])
        formula = arguments["formula"]
    except KeyError as exc:
        raise ExactToolArgumentError(f"SMT template requires {exc}") from exc
    if not isinstance(formula, Mapping):
        raise ExactToolArgumentError("'formula' must be an object")
    names = frozenset(item["name"] for item in variables)
    _validate_formula(formula, names)
    if _is_term(formula):
        raise ExactToolArgumentError("'formula' must be boolean-valued, not an integer term")
    raw_timeout = arguments.get("timeout_ms", _DEFAULT_TIMEOUT_MS)
    if not isinstance(raw_timeout, int) or raw_timeout < 1:
        raise ExactToolArgumentError("'timeout_ms' must be a positive integer")
    timeout_ms = min(raw_timeout, _MAX_TIMEOUT_MS)
    return variables, dict(formula), timeout_ms


def _tool_call(
    *,
    template: str,
    claim_id: str,
    status: ToolStatus,
    input_digest: str,
    output_digest: str,
    replay_command: str,
    started: str,
    ended: str,
    expected_discriminator: str,
    independence_group: str,
) -> ToolCallRecord:
    return ToolCallRecord(
        call_id=_new_id("EXACT-SMT"),
        tool=f"exact:{template}",
        purpose=f"SMT bounded check for claim {claim_id}.",
        status=status,
        input_digest_sha256=input_digest,
        output_digest_sha256=output_digest,
        linked_claim_ids=(claim_id,),
        independence_group=independence_group,
        replay_command=replay_command,
        started_at=started,
        ended_at=ended,
        environment_digest_sha256=_smt_environment_digest(),
        expected_discriminator=expected_discriminator,
    )


def _smt_environment_digest() -> str:
    try:
        z3mod = _load_z3()
        version = str(z3mod.get_version_string())
    except ExactToolUnavailableError:
        version = "unavailable"
    return digest_json({"solver": "z3", "version": version, "module": "matharc.v02.smt_tools"})


def _replay_command(template: str, arguments: Mapping[str, Any]) -> str:
    payload = canonical_json({"template": template, "arguments": dict(arguments)})
    code = f"from matharc.v02.smt_tools import _replay; _replay({payload!r})"
    return "python -c " + shlex.quote(code)


def _replay(payload_json: str) -> None:  # pragma: no cover - exercised via replay commands
    payload = json.loads(payload_json)
    template = str(payload["template"])
    arguments = payload["arguments"]
    if template == "smt_universal_no_counterexample":
        result = smt_universal_no_counterexample(claim_id="REPLAY", arguments=arguments)
    elif template == "smt_existential_witness":
        result = smt_existential_witness(claim_id="REPLAY", arguments=arguments)
    else:
        raise ExactToolArgumentError(f"unknown SMT template: {template!r}")
    print(
        json.dumps(
            {
                "status": result.tool_call.status.value,
                "output_digest_sha256": result.tool_call.output_digest_sha256,
            },
            ensure_ascii=False,
        )
    )


def _output(
    template: str,
    variables: list[dict[str, Any]],
    formula: Mapping[str, Any],
    timeout_ms: int,
    verdict: str,
    model: Mapping[str, int] | None,
    independent_model_check: bool | None,
) -> dict[str, Any]:
    return {
        "schema": "matharc.v02.smt-check.1",
        "template": template,
        "solver": "z3",
        "verdict": verdict,
        "model": dict(model) if model is not None else None,
        "independent_model_check": independent_model_check,
        "variables": variables,
        "formula": dict(formula),
        "formula_rendered": _render(formula),
        "domain": _domain_text(variables),
        "timeout_ms": timeout_ms,
    }


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


def smt_universal_no_counterexample(
    *, claim_id: str, arguments: Mapping[str, Any]
) -> ExactToolResult:
    """Check "for all declared variables within bounds, formula holds".

    Solves ``bounds AND NOT formula``: unsat supports the bounded universal
    claim (solver-trusted, recorded as such); a sat model is independently
    re-checked and, if confirmed, refutes the claim (FAIL, no evidence);
    unknown is a hard ERROR with no evidence.
    """

    template = "smt_universal_no_counterexample"
    variables, formula, timeout_ms = _parse_common(arguments)
    negated = {"op": "not", "args": [formula]}
    started = utc_now()
    input_digest = digest_json(
        {"template": template, "variables": variables, "formula": formula, "timeout_ms": timeout_ms}
    )
    replay = _replay_command(template, arguments)
    verdict, model = _run_solver(variables, negated, timeout_ms)
    ended = utc_now()
    discriminator = (
        "unsat of the negated formula supports the bounded claim; a sat model must "
        "survive the independent evaluator; unknown never produces evidence"
    )

    if verdict == "unknown":
        output = _output(template, variables, formula, timeout_ms, verdict, None, None)
        call = _tool_call(
            template=template,
            claim_id=claim_id,
            status=ToolStatus.ERROR,
            input_digest=input_digest,
            output_digest=digest_json(output),
            replay_command=replay,
            started=started,
            ended=ended,
            expected_discriminator=discriminator,
            independence_group="smt:z3",
        )
        return ExactToolResult(tool_call=call, evidence=None)

    if verdict == "sat":
        assert model is not None
        confirmed = _model_in_bounds(variables, model) and not eval_formula(formula, model)
        output = _output(template, variables, formula, timeout_ms, verdict, model, confirmed)
        call = _tool_call(
            template=template,
            claim_id=claim_id,
            # A confirmed countermodel is a decisive FAIL; a model the
            # independent evaluator rejects is a checker disagreement and
            # must surface as ERROR, never as a result for either side.
            status=ToolStatus.FAIL if confirmed else ToolStatus.ERROR,
            input_digest=input_digest,
            output_digest=digest_json(output),
            replay_command=replay,
            started=started,
            ended=ended,
            expected_discriminator=discriminator,
            independence_group="smt:z3-model+independent-int-evaluator",
        )
        # Deliberately no EvidenceRecord: evidence attached to a claim counts
        # toward proving it, so a counterexample must not enter that channel.
        return ExactToolResult(tool_call=call, evidence=None)

    output = _output(template, variables, formula, timeout_ms, verdict, None, None)
    output_digest = digest_json(output)
    call = _tool_call(
        template=template,
        claim_id=claim_id,
        status=ToolStatus.PASS,
        input_digest=input_digest,
        output_digest=output_digest,
        replay_command=replay,
        started=started,
        ended=ended,
        expected_discriminator=discriminator,
        independence_group="smt:z3",
    )
    evidence = EvidenceRecord(
        evidence_id=_new_id("EVIDENCE-SMT-U"),
        claim_ids=(claim_id,),
        kind=EvidenceKind.EXACT_COMPUTATION,
        status=EvidenceStatus.ACCEPTED,
        summary=(
            f"z3 reports no counterexample to {_render(formula)} over {_domain_text(variables)}."
        ),
        artifact_uri="",
        digest_sha256=output_digest,
        producer="smt:z3",
        verifier="smt:z3",
        independence_group="smt:z3",
        replay_command=replay,
        statement_correspondence=(
            f"The bounded universal statement 'for all {_domain_text(variables)}: "
            f"{_render(formula)}' is exactly the claim's statement; it says nothing "
            "outside the declared bounds."
        ),
        limitations=(
            "unsat verdict is solver-internal; no independently checked proof object "
            "(DRAT or proof term) accompanies it",
            "valid only within the declared variable bounds",
        ),
    )
    return ExactToolResult(tool_call=call, evidence=evidence)


def smt_existential_witness(*, claim_id: str, arguments: Mapping[str, Any]) -> ExactToolResult:
    """Check "some assignment within bounds satisfies formula" with a verified witness.

    A sat model becomes EXACT_CERTIFICATE evidence only after the independent
    pure-Python evaluator confirms it; unsat is a FAIL with no evidence
    (refutation would be solver-trusted); unknown is a hard ERROR.
    """

    template = "smt_existential_witness"
    variables, formula, timeout_ms = _parse_common(arguments)
    started = utc_now()
    input_digest = digest_json(
        {"template": template, "variables": variables, "formula": formula, "timeout_ms": timeout_ms}
    )
    replay = _replay_command(template, arguments)
    verdict, model = _run_solver(variables, formula, timeout_ms)
    ended = utc_now()
    discriminator = (
        "a witness model must satisfy the formula under the independent evaluator; "
        "unsat and unknown never produce evidence for the existential claim"
    )

    if verdict == "sat":
        assert model is not None
        confirmed = _model_in_bounds(variables, model) and eval_formula(formula, model)
        output = _output(template, variables, formula, timeout_ms, verdict, model, confirmed)
        output_digest = digest_json(output)
        call = _tool_call(
            template=template,
            claim_id=claim_id,
            status=ToolStatus.PASS if confirmed else ToolStatus.ERROR,
            input_digest=input_digest,
            output_digest=output_digest,
            replay_command=replay,
            started=started,
            ended=ended,
            expected_discriminator=discriminator,
            independence_group="smt:z3-model+independent-int-evaluator",
        )
        if not confirmed:
            return ExactToolResult(tool_call=call, evidence=None)
        evidence = EvidenceRecord(
            evidence_id=_new_id("EVIDENCE-SMT-E"),
            claim_ids=(claim_id,),
            kind=EvidenceKind.EXACT_CERTIFICATE,
            status=EvidenceStatus.ACCEPTED,
            summary=(
                f"Witness {dict(model)} satisfies {_render(formula)} over "
                f"{_domain_text(variables)}; confirmed by the independent evaluator."
            ),
            artifact_uri="",
            digest_sha256=output_digest,
            producer="smt:z3",
            verifier="independent-int-evaluator",
            independence_group="smt:z3-model+independent-int-evaluator",
            replay_command=replay,
            statement_correspondence=(
                f"The existential statement 'some {_domain_text(variables)} satisfies "
                f"{_render(formula)}' is exactly the claim's statement, witnessed by "
                f"{dict(model)}."
            ),
        )
        return ExactToolResult(tool_call=call, evidence=evidence)

    output = _output(template, variables, formula, timeout_ms, verdict, None, None)
    call = _tool_call(
        template=template,
        claim_id=claim_id,
        status=ToolStatus.FAIL if verdict == "unsat" else ToolStatus.ERROR,
        input_digest=input_digest,
        output_digest=digest_json(output),
        replay_command=replay,
        started=started,
        ended=ended,
        expected_discriminator=discriminator,
        independence_group="smt:z3",
    )
    return ExactToolResult(tool_call=call, evidence=None)
