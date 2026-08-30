from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

from .failure_memory import FailureMatch, FailureMemory
from .metrics import compute_research_metrics
from .schema import (
    ClaimRecord,
    ClaimStatus,
    PublicReasoningStep,
    ResearchRoute,
    RouteStatus,
    utc_now,
)
from .trace import ResearchTrace, TraceValidationError

# A single proposal batch is capped so one runaway or adversarial worker turn
# cannot balloon the claim DAG; a worker that needs more must earn it across
# multiple rounds, each independently falsifiable.
MAX_NEW_CLAIMS_PER_PROPOSAL = 5
MAX_NEW_ROUTES_PER_PROPOSAL = 5


@dataclass(slots=True)
class ResearchRoundPlan:
    round_id: str
    focus_claim_id: str
    focus_statement: str
    selection_reason: str
    dependency_state: dict[str, str]
    retrieved_failures: tuple[dict[str, Any], ...]
    route_actions: tuple[dict[str, Any], ...]
    required_tools: tuple[dict[str, Any], ...]
    acceptance_gate: tuple[str, ...]
    public_summary: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_id": self.round_id,
            "focus_claim_id": self.focus_claim_id,
            "focus_statement": self.focus_statement,
            "selection_reason": self.selection_reason,
            "dependency_state": self.dependency_state,
            "retrieved_failures": list(self.retrieved_failures),
            "route_actions": list(self.route_actions),
            "required_tools": list(self.required_tools),
            "acceptance_gate": list(self.acceptance_gate),
            "public_summary": self.public_summary,
            "created_at": self.created_at,
        }


class ResearchOrchestrator:
    """Plan research rounds without giving language-model output proof authority.

    The orchestrator selects a load-bearing obligation, retrieves relevant past
    failures, demands mechanism-distinct routes, and defines acceptance gates.
    Agent prose remains a proposal until exact evidence is attached and the
    ResearchTrace promotion guard accepts it.
    """

    def __init__(
        self,
        trace: ResearchTrace,
        failure_memory: FailureMemory | None = None,
    ) -> None:
        self.trace = trace
        self.failure_memory = failure_memory or FailureMemory()
        self.failure_memory.ingest_trace(trace)
        # Every accept_agent_proposal call appends one entry here recording
        # what it created/rejected -- observability for the campaign loop,
        # not itself evidence or part of the persisted trace.
        self.creation_log: list[dict[str, Any]] = []

    def select_focus_claim(self) -> tuple[str, str]:
        reachable = self._target_ancestor_closure()
        candidates = [
            claim
            for claim_id, claim in self.trace.claims.items()
            if claim_id in reachable
            and claim.status
            not in {ClaimStatus.PROVED, ClaimStatus.REFUTED, ClaimStatus.RETRACTED}
        ]
        if not candidates:
            raise TraceValidationError("no open claim remains on a target dependency path")

        def score(claim: Any) -> tuple[bool, float, float, str]:
            # A claim whose declared dependencies are still open cannot pass the
            # acceptance gate this round, so ready claims always rank first.
            dependencies_ready = all(
                self.trace.claims[item].status is ClaimStatus.PROVED
                for item in claim.dependencies
            )
            load = claim.weight * (1.0 + len(self.trace.descendants(claim.claim_id)))
            if claim.critical:
                load *= 1.8
            if claim.status is ClaimStatus.CANDIDATE:
                load *= 1.2
            return dependencies_ready, load, claim.weight, claim.claim_id

        selected = max(candidates, key=score)
        reason = (
            "highest load-bearing score among unresolved ancestors of the target; "
            f"critical={selected.critical}, descendants={len(self.trace.descendants(selected.claim_id))}, "
            f"dependencies_ready={all(self.trace.claims[item].status is ClaimStatus.PROVED for item in selected.dependencies)}"
        )
        return selected.claim_id, reason

    def plan_round(self, *, top_failure_matches: int = 5) -> ResearchRoundPlan:
        claim_id, reason = self.select_focus_claim()
        claim = self.trace.claims[claim_id]
        route_signatures = [
            signature
            for route_id in claim.route_ids
            if route_id in self.trace.routes
            for signature in self.trace.routes[route_id].mechanism_signature
        ]
        matches = self.failure_memory.query(
            claim.statement,
            mechanism_signature=route_signatures,
            top_k=top_failure_matches,
        )
        route_actions = self._route_actions(claim_id)
        required_tools = self._required_tools(claim_id, route_actions)
        dependency_state = {
            dependency: self.trace.claims[dependency].status.value
            for dependency in claim.dependencies
        }
        gate = (
            "all declared dependencies are PROVED",
            "at least one proof-capable evidence artifact has exact statement correspondence",
            "critical claims have two independent evidence groups",
            "exact or formal artifacts have a cold-replay command and SHA-256 digest",
            "the falsifier has executed the route kill test",
            "no finite-to-universal or local-to-global scope jump remains",
            "ResearchTrace.promote_claim accepts the claim without override",
        )
        return ResearchRoundPlan(
            round_id=f"ROUND-{uuid.uuid4().hex[:12]}",
            focus_claim_id=claim_id,
            focus_statement=claim.statement,
            selection_reason=reason,
            dependency_state=dependency_state,
            retrieved_failures=tuple(item.to_dict() for item in matches),
            route_actions=tuple(route_actions),
            required_tools=tuple(required_tools),
            acceptance_gate=gate,
            public_summary=(
                f"Focus on {claim_id}.  The round is successful only if a verifier-gated "
                "claim node closes or an exact failure narrows the theorem boundary."
            ),
        )

    def accept_agent_proposal(
        self,
        *,
        role: str,
        payload: Mapping[str, Any],
        step_id: str | None = None,
    ) -> PublicReasoningStep:
        """Record a structured agent proposal as public rationale, never as proof."""

        forbidden = {
            "chain_of_thought",
            "private_chain_of_thought",
            "hidden_reasoning",
            "scratchpad",
            "private_reasoning",
        }
        if forbidden & set(payload):
            raise TraceValidationError(
                "private chain-of-thought fields are not accepted; submit a concise "
                "objective/premises/move/observation/falsification/decision record"
            )
        reasoning = payload.get("public_reasoning", payload)
        if not isinstance(reasoning, Mapping):
            raise TraceValidationError("public_reasoning must be an object")
        required = {
            "objective",
            "premises",
            "proposed_move",
            "observation",
            "falsification",
            "decision",
        }
        missing = required - set(reasoning)
        if missing:
            raise TraceValidationError(f"agent proposal is missing fields: {sorted(missing)}")

        claim_ids = tuple(
            str(item)
            for item in payload.get("linked_claim_ids", self._claim_ids_from_updates(payload))
        )
        route_ids = tuple(str(item) for item in payload.get("linked_route_ids", ()))
        tool_ids = tuple(str(item) for item in payload.get("linked_tool_call_ids", ()))
        step = PublicReasoningStep(
            step_id=step_id or f"STEP-{uuid.uuid4().hex[:12]}",
            role=role,
            objective=str(reasoning["objective"]),
            premises=tuple(str(item) for item in reasoning["premises"]),
            proposed_move=str(reasoning["proposed_move"]),
            observation=str(reasoning["observation"]),
            falsification_test=str(reasoning["falsification"]),
            decision=str(reasoning["decision"]),
            linked_claim_ids=claim_ids,
            linked_route_ids=route_ids,
            linked_tool_call_ids=tool_ids,
            confidence=(
                float(payload["confidence"])
                if payload.get("confidence") is not None
                else None
            ),
        )
        self.trace.add_public_reasoning(step)

        created_claim_ids, created_route_ids, rejected = self._create_proposed_structure(
            role=role, payload=payload
        )
        self.creation_log.append(
            {
                "step_id": step.step_id,
                "role": role,
                "created_claim_ids": created_claim_ids,
                "created_route_ids": created_route_ids,
                "rejected": rejected,
                "timestamp": utc_now(),
            }
        )

        # Proposal actions are intentionally one-way conservative.  They may
        # open, refine, block, or nominate candidates, but never mark PROVED.
        for update in payload.get("claim_updates", []):
            if not isinstance(update, Mapping):
                continue
            claim_id = str(update.get("claim_id", ""))
            action = str(update.get("action", "keep_open"))
            if claim_id not in self.trace.claims:
                continue
            claim = self.trace.claims[claim_id]
            if action in {"propose", "refine"}:
                if update.get("statement") and claim.status is not ClaimStatus.PROVED:
                    self.trace.revise_claim(
                        claim_id,
                        statement=str(update["statement"]),
                        scope=str(update.get("scope", claim.scope)),
                    )
                claim.status = ClaimStatus.CANDIDATE
            elif action in {"block", "refute"}:
                # An agent cannot refute exactly without evidence; both actions
                # therefore become BLOCKED until a counterexample is accepted.
                claim.status = ClaimStatus.BLOCKED
            elif action == "keep_open" and claim.status is ClaimStatus.PROPOSED:
                claim.status = ClaimStatus.OPEN
            claim.updated_at = utc_now()
        self.trace.updated_at = utc_now()
        return step

    def _create_proposed_structure(
        self,
        *,
        role: str,
        payload: Mapping[str, Any],
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[dict[str, Any], ...]]:
        """Let a worker extend the claim DAG -- governed, never self-promoting.

        This is the seam through which 数学结构拆解 (mathematical structure
        decomposition) can be proposed by a worker instead of only hand-authored
        in Python: new_claims/new_routes always enter as PROPOSED, dependencies
        must already exist (no forward references within one batch), and a
        malformed or over-cap item is rejected individually rather than
        failing the whole proposal.  Promotion authority is untouched: created
        claims are exactly as far from PROVED as any hand-written one.
        """

        created_claim_ids: list[str] = []
        created_route_ids: list[str] = []
        rejected: list[dict[str, Any]] = []

        raw_new_claims = payload.get("new_claims", [])
        if not isinstance(raw_new_claims, list):
            raw_new_claims = []
        if len(raw_new_claims) > MAX_NEW_CLAIMS_PER_PROPOSAL:
            rejected.append(
                {
                    "kind": "claim",
                    "spec": None,
                    "reason": (
                        f"per-proposal cap exceeded: {len(raw_new_claims)} > "
                        f"{MAX_NEW_CLAIMS_PER_PROPOSAL}"
                    ),
                }
            )
        for spec in raw_new_claims[:MAX_NEW_CLAIMS_PER_PROPOSAL]:
            if not isinstance(spec, Mapping):
                rejected.append({"kind": "claim", "spec": spec, "reason": "not an object"})
                continue
            try:
                claim_id = str(spec["claim_id"])
                weight = float(spec.get("weight", 1.0))
                if weight <= 0:
                    raise TraceValidationError("claim weight must be positive")
                claim = ClaimRecord(
                    claim_id=claim_id,
                    statement=str(spec["statement"]),
                    scope=str(spec["scope"]),
                    status=ClaimStatus.PROPOSED,
                    dependencies=tuple(str(item) for item in spec.get("dependencies", ())),
                    weight=weight,
                    critical=bool(spec.get("critical", False)),
                    boundary=str(spec.get("boundary", "")),
                    owner=f"agent:{role}",
                )
                self.trace.add_claim(claim)
            except (KeyError, ValueError, TypeError, TraceValidationError) as exc:
                rejected.append({"kind": "claim", "spec": dict(spec), "reason": str(exc)})
                continue
            created_claim_ids.append(claim_id)

        raw_new_routes = payload.get("new_routes", [])
        if not isinstance(raw_new_routes, list):
            raw_new_routes = []
        if len(raw_new_routes) > MAX_NEW_ROUTES_PER_PROPOSAL:
            rejected.append(
                {
                    "kind": "route",
                    "spec": None,
                    "reason": (
                        f"per-proposal cap exceeded: {len(raw_new_routes)} > "
                        f"{MAX_NEW_ROUTES_PER_PROPOSAL}"
                    ),
                }
            )
        for spec in raw_new_routes[:MAX_NEW_ROUTES_PER_PROPOSAL]:
            if not isinstance(spec, Mapping):
                rejected.append({"kind": "route", "spec": spec, "reason": "not an object"})
                continue
            try:
                route_id = str(spec["route_id"])
                route = ResearchRoute(
                    route_id=route_id,
                    name=str(spec["name"]),
                    hypothesis=str(spec["hypothesis"]),
                    mechanism_signature=tuple(str(item) for item in spec["mechanism_signature"]),
                    kill_test=str(spec["kill_test"]),
                    status=RouteStatus.PROPOSED,
                    claim_ids=tuple(str(item) for item in spec.get("claim_ids", ())),
                    expected_discriminator=str(spec.get("expected_discriminator", "")),
                    rationale=f"proposed by agent:{role}",
                )
                self.trace.add_route(route)
            except (KeyError, ValueError, TypeError, TraceValidationError) as exc:
                rejected.append({"kind": "route", "spec": dict(spec), "reason": str(exc)})
                continue
            created_route_ids.append(route_id)

        return tuple(created_claim_ids), tuple(created_route_ids), tuple(rejected)

    def round_snapshot(self) -> dict[str, Any]:
        metrics = compute_research_metrics(self.trace)
        return {
            "run_id": self.trace.run_id,
            "release_state": metrics["release_state"],
            "metrics": metrics,
            "next_plan": self.plan_round().to_dict()
            if metrics["target_logical_closure"] < 1.0
            and metrics["release_state"] != "REFUTED_EXACT"
            else None,
        }

    def _target_ancestor_closure(self) -> set[str]:
        result: set[str] = set()
        stack = [
            item for item in self.trace.contract.target_claim_ids if item in self.trace.claims
        ]
        while stack:
            claim_id = stack.pop()
            if claim_id in result:
                continue
            result.add(claim_id)
            stack.extend(self.trace.claims[claim_id].dependencies)
        return result

    def _route_actions(self, claim_id: str) -> list[dict[str, Any]]:
        claim = self.trace.claims[claim_id]
        routes = [
            self.trace.routes[item]
            for item in claim.route_ids
            if item in self.trace.routes
        ]
        actions: list[dict[str, Any]] = []
        active = [route for route in routes if route.status is RouteStatus.ACTIVE]
        for route in active:
            actions.append(
                {
                    "route_id": route.route_id,
                    "action": "execute_kill_test_before_deeper_proof_search",
                    "mechanism_signature": list(route.mechanism_signature),
                    "kill_test": route.kill_test,
                    "expected_discriminator": route.expected_discriminator,
                }
            )
        if len(active) < 2:
            actions.append(
                {
                    "route_id": None,
                    "action": "open_mechanism_distinct_route",
                    "requirement": (
                        "new invariant, representation, obstruction, or proof calculus; "
                        "renaming the current route is rejected"
                    ),
                }
            )
        if not routes:
            actions.append(
                {
                    "route_id": None,
                    "action": "create_first_route_with_kill_test",
                    "requirement": "state the mechanism signature and cheapest exact falsifier",
                }
            )
        return actions

    def _required_tools(
        self,
        claim_id: str,
        route_actions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        claim = self.trace.claims[claim_id]
        tools: list[dict[str, Any]] = [
            {
                "role": "falsifier",
                "purpose": "attack scope, quantifiers, boundary cases, and hidden assumptions",
                "required_output": "minimal witness or exact PASS record",
            },
            {
                "role": "verifier",
                "purpose": "independently reconstruct every accepted certificate",
                "required_output": "replay command, environment digest, output digest, statement correspondence",
            },
        ]
        if claim.critical:
            tools.append(
                {
                    "role": "independent_verifier",
                    "purpose": "avoid generator/checker common-mode error",
                    "required_output": "second evidence group with distinct implementation or proof formalism",
                }
            )
        if any(action.get("action", "").startswith("execute_kill") for action in route_actions):
            tools.append(
                {
                    "role": "route_kill_test",
                    "purpose": "reject an attractive false route before expensive expansion",
                    "required_output": "discriminating exact result linked to the route",
                }
            )
        return tools

    @staticmethod
    def _claim_ids_from_updates(payload: Mapping[str, Any]) -> tuple[str, ...]:
        result: list[str] = []
        for update in payload.get("claim_updates", []):
            if isinstance(update, Mapping) and update.get("claim_id"):
                result.append(str(update["claim_id"]))
        return tuple(dict.fromkeys(result))
