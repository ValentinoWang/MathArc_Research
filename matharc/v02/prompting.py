"""Provider-agnostic worker prompts for the v0.2 research loop.

The role definitions and the eight non-negotiable rules are ported from
matharc/codex_runtime.py (the v0.1 OpenAI Codex CLI adapter) so that every
model bridge -- Codex CLI, Claude Code CLI, or any future adapter -- speaks
the same worker contract.  Nothing here has proof authority: the schema this
module defines is forced onto the *proposal*, and the proposal still has to
pass ResearchOrchestrator.accept_agent_proposal and, eventually,
ResearchTrace.promote_claim.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from .metrics import compute_research_metrics
from .orchestrator import ResearchRoundPlan
from .trace import ResearchTrace

ROLE_DEFINITIONS: dict[str, dict[str, str]] = {
    "strategist": {
        "label": "研究策略师",
        "mission": (
            "Identify the next load-bearing obligation, open mechanism-distinct "
            "routes, and state a cheap falsification test."
        ),
    },
    "prover": {
        "label": "证明构造器",
        "mission": (
            "Construct one atomic lemma, derivation, certificate, or exact "
            "reduction; never promote from plausibility or finite testing."
        ),
    },
    "falsifier": {
        "label": "反例攻击者",
        "mission": (
            "Attack scope, quantifiers, hidden assumptions, boundary cases, and "
            "checker semantics; prefer a minimal exact counterexample."
        ),
    },
    "verifier": {
        "label": "证据与验证工程师",
        "mission": (
            "Design replayable exact checkers, statement correspondence, "
            "hashes, trust boundaries, and independent reconstruction."
        ),
    },
    "synthesizer": {
        "label": "研究综合器",
        "mission": (
            "State the strongest verified result, all unresolved load-bearing "
            "obligations, and the exact claim boundary."
        ),
    },
}

RESEARCH_RULES_MARKER = "NON-NEGOTIABLE RESEARCH RULES:"


def _role_preamble(role: str) -> str:
    if role not in ROLE_DEFINITIONS:
        raise ValueError(f"unknown role: {role}; available={sorted(ROLE_DEFINITIONS)}")
    spec = ROLE_DEFINITIONS[role]
    return (
        "You are an agent worker inside MathArc Research v0.2.\n"
        f"ROLE: {spec['label']} ({role})\nMISSION: {spec['mission']}\n\n"
        f"{RESEARCH_RULES_MARKER}\n"
        "1. You may propose, investigate, falsify, or design evidence; you may not self-assign PROVED.\n"
        "2. Never lift finite, local, numerical, or restricted evidence to a stronger scope without an explicit bridge.\n"
        "3. Distinguish PASS, FAIL, COUNTEREXAMPLE, UNKNOWN, TIMEOUT, and ERROR.\n"
        "4. Prefer one atomic load-bearing increment over broad persuasive prose.\n"
        "5. State a cheap falsification test before expensive work.\n"
        "6. Treat generator/checker independence, statement correspondence, hashes, and replay commands as first-class.\n"
        "7. Expose only a concise public reasoning summary, not private token-level chain-of-thought.\n"
        "8. new_claims/new_routes you create always enter as PROPOSED and are not evidence by themselves.\n"
        "9. When a tool_request executes a declared route kill test, include that route_id so the result is attributed to the correct mechanism.\n"
        "10. The final response must match the supplied JSON schema exactly.\n\n"
    )


def build_trace_view(trace: ResearchTrace, plan: ResearchRoundPlan) -> dict[str, Any]:
    """Build the bounded, token-budgeted view a worker receives for one round.

    Deliberately scoped to the focus claim, its declared dependencies, its
    routes, its accepted evidence, and recent relevant failures -- not the
    entire trace -- so prompt size stays bounded as a research trace grows
    past a handful of claims.
    """

    focus = trace.claims[plan.focus_claim_id]
    return {
        "run_id": trace.run_id,
        "contract": trace.contract.to_dict(),
        "focus_claim": focus.to_dict(),
        "dependencies": [trace.claims[item].to_dict() for item in focus.dependencies],
        "routes": [
            trace.routes[item].to_dict() for item in focus.route_ids if item in trace.routes
        ],
        "accepted_evidence": [
            trace.evidence[item].to_dict()
            for item in focus.evidence_ids
            if item in trace.evidence
        ],
        "recent_failures": [
            item.to_dict()
            for item in trace.failures[-10:]
            if item.claim_id == plan.focus_claim_id or item.route_id in focus.route_ids
        ],
        "metrics": compute_research_metrics(trace),
        "forbidden_authority": ["PROVED", "PROVED_AND_AUDITED"],
    }


def build_worker_prompt(
    *,
    role: str,
    trace_view: Mapping[str, Any],
    plan: ResearchRoundPlan | None = None,
    user_message: str = "",
) -> str:
    """Assemble one complete worker prompt: role preamble + bounded state + ask."""

    sections = [_role_preamble(role)]
    if plan is not None:
        sections.append("ROUND PLAN:\n" + json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
    if trace_view:
        sections.append(
            "FROZEN RESEARCH STATE (bounded to the focus claim):\n"
            + json.dumps(dict(trace_view), ensure_ascii=False, indent=2)
        )
    ask = user_message.strip() or (
        "Advance the focus claim: attach evidence, open or close a route, refine "
        "the claim, or propose a new sub-claim/route through new_claims/new_routes. "
        "State a cheap falsification test before any expensive step."
    )
    sections.append("USER REQUEST:\n" + ask)
    return "\n\n".join(sections)


# JSON Schema forced onto every structured worker response.  It mirrors the
# v0.1 AGENT_OUTPUT_SCHEMA (matharc/codex_runtime.py) and extends it with
# new_claims/new_routes so a worker can propose problem decomposition
# (数学结构拆解) through the same governed channel that
# ResearchOrchestrator.accept_agent_proposal enforces.  Kept flat (no $ref) to
# stay compatible with CLI --json-schema structured-output validation.
PROPOSAL_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "public_reasoning", "claim_boundary"],
    "properties": {
        "status": {
            "type": "string",
            "enum": ["progress", "blocked", "falsified", "candidate", "error"],
        },
        "executive_summary": {"type": "string"},
        "usage_report": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "input_tokens": {"type": "integer", "minimum": 0},
                "output_tokens": {"type": "integer", "minimum": 0},
            },
        },
        "public_reasoning": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "objective",
                "premises",
                "proposed_move",
                "observation",
                "falsification",
                "decision",
            ],
            "properties": {
                "objective": {"type": "string"},
                "premises": {"type": "array", "items": {"type": "string"}},
                "proposed_move": {"type": "string"},
                "observation": {"type": "string"},
                "falsification": {"type": "string"},
                "decision": {"type": "string"},
            },
        },
        "claim_updates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["claim_id", "action"],
                "properties": {
                    "claim_id": {"type": "string"},
                    "action": {
                        "type": "string",
                        "enum": ["propose", "refine", "block", "refute", "keep_open"],
                    },
                    "statement": {"type": "string"},
                    "scope": {"type": "string"},
                },
            },
        },
        "new_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["claim_id", "statement", "scope"],
                "properties": {
                    "claim_id": {"type": "string"},
                    "statement": {"type": "string"},
                    "scope": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "weight": {"type": "number"},
                    "critical": {"type": "boolean"},
                    "boundary": {"type": "string"},
                },
            },
        },
        "new_routes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["route_id", "name", "hypothesis", "mechanism_signature", "kill_test"],
                "properties": {
                    "route_id": {"type": "string"},
                    "name": {"type": "string"},
                    "hypothesis": {"type": "string"},
                    "mechanism_signature": {"type": "array", "items": {"type": "string"}},
                    "kill_test": {"type": "string"},
                    "claim_ids": {"type": "array", "items": {"type": "string"}},
                    "expected_discriminator": {"type": "string"},
                },
            },
        },
        "tool_requests": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["tool", "purpose"],
                "properties": {
                    "tool": {"type": "string"},
                    "purpose": {"type": "string"},
                    "route_id": {"type": "string"},
                    "arguments": {"type": "object"},
                },
            },
        },
        "risks": {"type": "array", "items": {"type": "string"}},
        "next_actions": {"type": "array", "items": {"type": "string"}},
        "claim_boundary": {"type": "string"},
    },
}
