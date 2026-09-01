from __future__ import annotations

import uuid
import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from .failure_memory import FailureMatch, FailureMemory
from .metrics import compute_research_metrics
from .schema import (
    ClaimRecord,
    ClaimStatus,
    FailureClass,
    PublicReasoningStep,
    ResearchRoute,
    RouteStatus,
    SpawnDecisionRecord,
    SpawnDecisionStatus,
    SpawnDescriptor,
    SpawnRequest,
    utc_now,
)
from .trace import ResearchTrace, TraceValidationError
from .transformation_catalog import (
    TransformationCatalog,
    TransformationCatalogError,
    default_transformation_catalog,
)

# A single proposal batch is capped so one runaway or adversarial worker turn
# cannot balloon the claim DAG; a worker that needs more must earn it across
# multiple rounds, each independently falsifiable.
MAX_NEW_CLAIMS_PER_PROPOSAL = 5
MAX_NEW_ROUTES_PER_PROPOSAL = 5
MAX_SPAWN_REQUESTS_PER_ROUND = 5
MAX_SPAWN_DEPTH = 1
MAX_SPAWN_BUDGET_PER_REQUEST = 10.0
MAX_SPAWN_BUDGET_PER_ROUND = 20.0

# Compatibility aliases for callers that used the shorter governance names.
MAX_SPAWNS_PER_ROUND = MAX_SPAWN_REQUESTS_PER_ROUND
MAX_REQUESTED_SPAWN_BUDGET = MAX_SPAWN_BUDGET_PER_REQUEST


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
    transformation_directives: tuple[dict[str, Any], ...] = ()

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
            "transformation_directives": list(self.transformation_directives),
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
        transformation_catalog: TransformationCatalog | None = None,
        *,
        catalog: TransformationCatalog | None = None,
    ) -> None:
        self.trace = trace
        self.failure_memory = failure_memory or FailureMemory()
        self.failure_memory.ingest_trace(trace)
        if transformation_catalog is not None and catalog is not None:
            raise ValueError("provide only one transformation catalog")
        self.transformation_catalog = (
            transformation_catalog
            or catalog
            or default_transformation_catalog()
        )
        if not isinstance(self.transformation_catalog, TransformationCatalog):
            raise ValueError("transformation_catalog must be a TransformationCatalog")
        # Every accept_agent_proposal call appends one entry here recording
        # what it created/rejected -- observability for the campaign loop,
        # not itself evidence or part of the persisted trace.
        self.creation_log: list[dict[str, Any]] = []
        self._spawn_log: list[SpawnDecisionRecord] = []
        self._approved_spawn_descriptors: list[SpawnDescriptor] = []
        self._spawn_round_id = "UNSCOPED"
        self._spawn_count = 0
        self._spawn_budget = 0.0
        self._spawn_request_ids: set[str] = set()

    @property
    def spawn_log(self) -> tuple[SpawnDecisionRecord, ...]:
        """An immutable view of every approved or rejected spawn decision."""

        return tuple(self._spawn_log)

    @property
    def approved_spawn_descriptors(self) -> tuple[SpawnDescriptor, ...]:
        """Descriptors approved so far; no executor is invoked for them."""

        return tuple(self._approved_spawn_descriptors)

    def begin_round(self, round_id: str) -> None:
        if not isinstance(round_id, str) or not round_id.strip():
            raise ValueError("round_id must be non-empty")
        self._spawn_round_id = round_id.strip()
        self._spawn_count = 0
        self._spawn_budget = 0.0
        self._spawn_request_ids = set()

    start_round = begin_round

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
        transformation_directives = self._transformation_directives(claim_id)
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
            transformation_directives=tuple(transformation_directives),
        )

    def accept_agent_proposal(
        self,
        *,
        role: str,
        payload: Mapping[str, Any],
        step_id: str | None = None,
        round_id: str | None = None,
    ) -> PublicReasoningStep:
        """Record a structured agent proposal as public rationale, never as proof."""

        if round_id is not None and round_id != self._spawn_round_id:
            self.begin_round(round_id)

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
        confidence = self._proposal_confidence(payload)
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
            confidence=confidence,
        )
        self.trace.add_public_reasoning(step)

        created_claim_ids, created_route_ids, rejected = self._create_proposed_structure(
            role=role, payload=payload
        )
        self._record_spawn_requests(role=role, payload=payload, step_id=step.step_id)
        # Proposal actions are intentionally one-way conservative.  They may
        # open, refine, block, or nominate candidates, but never mark PROVED.
        rejected_updates: list[dict[str, Any]] = []
        for update in payload.get("claim_updates", []):
            if not isinstance(update, Mapping):
                continue
            claim_id = str(update.get("claim_id", ""))
            action = str(update.get("action", "keep_open"))
            if claim_id not in self.trace.claims:
                continue
            claim = self.trace.claims[claim_id]
            if claim.status in {
                ClaimStatus.PROVED,
                ClaimStatus.REFUTED,
                ClaimStatus.RETRACTED,
            }:
                rejected_updates.append(
                    {
                        "kind": "claim_update",
                        "spec": dict(update),
                        "reason": (
                            f"agent proposal cannot alter protected claim state: "
                            f"{claim_id} is {claim.status.value}"
                        ),
                    }
                )
                continue
            if action in {"propose", "refine"}:
                if update.get("statement"):
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
        self.creation_log.append(
            {
                "step_id": step.step_id,
                "role": role,
                "created_claim_ids": created_claim_ids,
                "created_route_ids": created_route_ids,
                "derived_route_linkages": [
                    {
                        "route_id": route_id,
                        "failure_id": self.trace.routes[route_id].derived_from_failure,
                        "transformation_id": self.trace.routes[route_id].transformation_id,
                    }
                    for route_id in created_route_ids
                    if route_id in self.trace.routes
                    and self.trace.routes[route_id].derived_from_failure is not None
                ],
                "rejected": [*rejected, *rejected_updates],
                "timestamp": utc_now(),
            }
        )
        self.trace.updated_at = utc_now()
        return step

    @staticmethod
    def _proposal_confidence(payload: Mapping[str, Any]) -> float | None:
        value = payload.get("confidence")
        if value is None:
            return None
        if isinstance(value, bool):
            raise TraceValidationError("confidence must be a finite value in [0, 1]")
        try:
            confidence = float(value)
        except (TypeError, ValueError) as exc:
            raise TraceValidationError(
                "confidence must be a finite value in [0, 1]"
            ) from exc
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise TraceValidationError("confidence must be a finite value in [0, 1]")
        return confidence

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
                if not math.isfinite(weight) or weight <= 0:
                    raise TraceValidationError("claim weight must be a finite positive number")
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
                    parent_route_id=(
                        str(spec["parent_route_id"])
                        if spec.get("parent_route_id") is not None
                        else None
                    ),
                    expected_discriminator=str(spec.get("expected_discriminator", "")),
                    rationale=f"proposed by agent:{role}",
                    created_by=f"agent:{role}",
                    derived_from_failure=(
                        str(
                            spec.get(
                                "derived_from_failure",
                                spec.get("derived_from_failure_id"),
                            )
                        )
                        if spec.get("derived_from_failure", spec.get("derived_from_failure_id"))
                        is not None
                        else None
                    ),
                    transformation_id=(
                        str(spec["transformation_id"])
                        if spec.get("transformation_id") is not None
                        else None
                    ),
                )
                self._validate_derived_route_request(route)
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

    def _transformation_directives(self, claim_id: str) -> list[dict[str, Any]]:
        claim = self.trace.claims[claim_id]
        directives: list[dict[str, Any]] = []
        for failure in self.trace.failures:
            if failure.claim_id != claim_id and failure.route_id not in claim.route_ids:
                continue
            failed_route = self.trace.routes.get(failure.route_id)
            mechanism = failed_route.mechanism_signature if failed_route is not None else ()
            try:
                candidates = self.transformation_catalog.directives_for(
                    failure,
                    failed_mechanism_signature=mechanism,
                )
            except TransformationCatalogError:
                # A malformed failure/catalog pairing must not become a guessed
                # directive. The catalog remains a fail-closed input boundary.
                candidates = ()
            for directive in candidates:
                directive = dict(directive)
                directive["route_id"] = failure.route_id
                directives.append(directive)
        return directives

    def _validate_derived_route_request(self, route: ResearchRoute) -> None:
        failure_id = route.derived_from_failure
        transformation_id = route.transformation_id
        if failure_id is None and transformation_id is None:
            return
        if failure_id is None or transformation_id is None:
            raise TraceValidationError(
                "derived route requires both derived_from_failure and transformation_id"
            )
        failure = next(
            (item for item in self.trace.failures if item.failure_id == failure_id),
            None,
        )
        if failure is None:
            raise TraceValidationError(f"unknown derived failure: {failure_id}")
        if not isinstance(failure.failure_class, FailureClass):
            raise TraceValidationError(
                f"failure {failure_id} has an invalid failure class"
            )
        try:
            entry = self.transformation_catalog.get(transformation_id)
        except TransformationCatalogError as exc:
            raise TraceValidationError(str(exc)) from exc
        if failure.failure_class not in entry.applicable_failure_classes:
            raise TraceValidationError(
                f"transformation {transformation_id} is not applicable to "
                f"failure {failure_id} ({failure.failure_class})"
            )
        if route.parent_route_id is None:
            route.parent_route_id = failure.route_id
        elif route.parent_route_id != failure.route_id:
            raise TraceValidationError(
                f"derived route parent must be failed route {failure.route_id}"
            )

    def _record_spawn_requests(
        self,
        *,
        role: str,
        payload: Mapping[str, Any],
        step_id: str,
    ) -> None:
        if "spawn_requests" not in payload:
            return
        raw_requests = payload.get("spawn_requests")
        if not isinstance(raw_requests, list):
            self._append_spawn_decision(
                request_id=f"SPAWN-{self._spawn_round_id}-invalid",
                status=SpawnDecisionStatus.REJECTED,
                brief="",
                request_role=role,
                requested_budget=0.0,
                depth=-1,
                reason="spawn_requests must be an array",
                step_id=step_id,
            )
            return

        for index, raw_request in enumerate(raw_requests):
            request_id = self._spawn_request_id(raw_request, index)
            if self._spawn_count >= MAX_SPAWN_REQUESTS_PER_ROUND:
                self._append_spawn_decision(
                    request_id=request_id,
                    status=SpawnDecisionStatus.REJECTED,
                    brief=self._raw_spawn_text(raw_request, "brief"),
                    request_role=self._raw_spawn_text(raw_request, "role") or role,
                    requested_budget=self._raw_spawn_budget(raw_request),
                    depth=self._raw_spawn_depth(raw_request),
                    reason=(
                        f"per-round spawn cap exceeded: {MAX_SPAWN_REQUESTS_PER_ROUND}"
                    ),
                    step_id=step_id,
                )
                continue
            self._spawn_count += 1
            try:
                normalized = dict(raw_request) if isinstance(raw_request, Mapping) else raw_request
                if isinstance(normalized, Mapping):
                    normalized = dict(normalized)
                    normalized.setdefault("request_id", request_id)
                request = SpawnRequest.from_dict(normalized)
                if request.request_id in self._spawn_request_ids:
                    raise ValueError(f"duplicate spawn request_id: {request.request_id}")
                self._spawn_request_ids.add(request.request_id)
                if request.depth > MAX_SPAWN_DEPTH:
                    raise ValueError(f"spawn depth exceeds cap {MAX_SPAWN_DEPTH}")
                if request.budget > MAX_SPAWN_BUDGET_PER_REQUEST:
                    raise ValueError(
                        "spawn budget exceeds per-request cap "
                        f"{MAX_SPAWN_BUDGET_PER_REQUEST}"
                    )
                if self._spawn_budget + request.budget > MAX_SPAWN_BUDGET_PER_ROUND:
                    raise ValueError(
                        "spawn budget exceeds per-round cap "
                        f"{MAX_SPAWN_BUDGET_PER_ROUND}"
                    )
            except (TypeError, ValueError, KeyError) as exc:
                self._append_spawn_decision(
                    request_id=request_id,
                    status=SpawnDecisionStatus.REJECTED,
                    brief=self._raw_spawn_text(raw_request, "brief"),
                    request_role=self._raw_spawn_text(raw_request, "role") or role,
                    requested_budget=self._raw_spawn_budget(raw_request),
                    depth=self._raw_spawn_depth(raw_request),
                    reason=str(exc),
                    step_id=step_id,
                )
                continue

            descriptor = SpawnDescriptor(
                request_id=request.request_id,
                brief=request.brief,
                role=request.role,
                budget=request.budget,
                depth=request.depth,
                round_id=self._spawn_round_id,
                step_id=step_id,
            )
            self._spawn_budget += request.budget
            self._approved_spawn_descriptors.append(descriptor)
            self._append_spawn_decision(
                request_id=request.request_id,
                status=SpawnDecisionStatus.APPROVED,
                brief=request.brief,
                request_role=request.role,
                requested_budget=request.budget,
                depth=request.depth,
                reason="approved descriptor only; no task or process execution",
                step_id=step_id,
                descriptor=descriptor,
            )

    def _append_spawn_decision(
        self,
        *,
        request_id: str,
        status: SpawnDecisionStatus,
        brief: str,
        request_role: str,
        requested_budget: float,
        depth: int,
        reason: str,
        step_id: str,
        descriptor: SpawnDescriptor | None = None,
    ) -> None:
        self._spawn_log.append(
            SpawnDecisionRecord(
                request_id=request_id,
                status=status,
                brief=brief,
                role=request_role,
                requested_budget=requested_budget,
                depth=depth,
                reason=reason,
                round_id=self._spawn_round_id,
                step_id=step_id,
                descriptor=descriptor,
            )
        )

    def _spawn_request_id(self, raw_request: Any, index: int) -> str:
        if isinstance(raw_request, Mapping):
            for key in ("request_id", "spawn_id"):
                value = raw_request.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return f"SPAWN-{self._spawn_round_id}-{len(self._spawn_log) + index + 1}"

    @staticmethod
    def _raw_spawn_text(raw_request: Any, key: str) -> str:
        if isinstance(raw_request, Mapping):
            value = raw_request.get(key)
            if isinstance(value, str):
                return value.strip()
        return ""

    @staticmethod
    def _raw_spawn_budget(raw_request: Any) -> float:
        if not isinstance(raw_request, Mapping):
            return 0.0
        value = raw_request.get("budget", raw_request.get("requested_budget", 0.0))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0.0
        numeric = float(value)
        return numeric if math.isfinite(numeric) and numeric >= 0.0 else 0.0

    @staticmethod
    def _raw_spawn_depth(raw_request: Any) -> int:
        if isinstance(raw_request, Mapping):
            value = raw_request.get("depth")
            if isinstance(value, int):
                return value
        return -1

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
