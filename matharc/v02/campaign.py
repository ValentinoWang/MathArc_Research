"""Autonomous multi-round research campaign.

ResearchSession (session.py) runs exactly one plan -> worker -> accept round.
ResearchCampaign repeats that cycle, dispatches allowlisted exact tools,
records evidence, attempts promotion only through ResearchTrace.promote_claim,
meters cost, and persists the trace.

v0.3 adds evidence-gain accounting: stagnation is no longer inferred only
from weighted proof closure. A round resets the stagnation counter only when
it creates a new semantic evidence/certificate signature, promotes a claim,
kills a mechanism, records a scope-narrowing event, or creates a new typed
route evaluation. Re-running the same checker with the same output does not
manufacture progress merely because it receives a new evidence ID.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .budget import BudgetLedger
from .exact_tools import (
    ExactToolRegistry,
    ExactToolUnavailableError,
    UnknownExactToolError,
    default_exact_tool_registry,
)
from .falsification import (
    FalsificationContractError,
    evaluation_from_tool_call,
    get_kill_test_spec,
    iter_route_evaluations,
    promotion_route_blockers,
    record_route_evaluation,
)
from .metrics import compute_research_metrics
from .orchestrator import ResearchOrchestrator
from .prompting import build_trace_view
from .schema import (
    EvidenceKind,
    EvidenceStatus,
    RouteStatus,
    ToolStatus,
    utc_now,
)
from .trace import PromotionError, ResearchTrace, TraceValidationError, save_trace
from .workers import ProposalWorker

_TERMINAL_RELEASE_STATES = frozenset(
    {
        "PROVED_AND_AUDITED",
        "PROVED_WITH_AUDIT_DEBT",
        "REFUTED",
        "REFUTED_EXACT",
    }
)
_POSITIVE_EVIDENCE_EXCLUSIONS = frozenset(
    {
        EvidenceKind.NUMERICAL_EXPERIMENT,
        EvidenceKind.HEURISTIC,
        EvidenceKind.COUNTEREXAMPLE,
    }
)
_EXACT_OR_FORMAL_KINDS = frozenset(
    {
        EvidenceKind.FORMAL_PROOF,
        EvidenceKind.CHECKED_DERIVATION,
        EvidenceKind.EXACT_CERTIFICATE,
        EvidenceKind.EXACT_COMPUTATION,
    }
)


def _semantic_state(trace: ResearchTrace) -> dict[str, set[Any]]:
    positive_evidence: set[tuple[str, str, str, str]] = set()
    exact_evidence: set[tuple[str, str, str, str]] = set()
    counterexamples: set[tuple[str, str, str, str]] = set()
    for evidence in trace.evidence.values():
        if evidence.status is not EvidenceStatus.ACCEPTED:
            continue
        signature = (
            evidence.kind.value,
            evidence.digest_sha256,
            evidence.independence_group,
            evidence.statement_correspondence,
        )
        if evidence.kind is EvidenceKind.COUNTEREXAMPLE:
            counterexamples.add(signature)
            continue
        if evidence.kind not in _POSITIVE_EVIDENCE_EXCLUSIONS:
            positive_evidence.add(signature)
        if evidence.kind in _EXACT_OR_FORMAL_KINDS:
            exact_evidence.add(signature)

    route_evaluations: set[tuple[str, str, str, str, str, str]] = set()
    try:
        records = iter_route_evaluations(trace)
    except FalsificationContractError:
        records = ()
    for record in records:
        tool = trace.tool_calls.get(record.tool_call_id)
        route_evaluations.add(
            (
                record.route_id,
                record.claim_id,
                record.kill_test_spec_digest,
                record.outcome.value,
                record.tested_scope,
                tool.output_digest_sha256 if tool is not None else "",
            )
        )

    scope_events = trace.metadata.get("v03_scope_narrowing_events", [])
    scope_signatures: set[str] = set()
    if isinstance(scope_events, list):
        for value in scope_events:
            scope_signatures.add(repr(value))

    return {
        "proved_claims": {
            claim.claim_id
            for claim in trace.claims.values()
            if claim.status.value == "PROVED"
        },
        "killed_routes": {
            route.route_id
            for route in trace.routes.values()
            if route.status in {RouteStatus.BLOCKED, RouteStatus.FALSIFIED}
        },
        "positive_evidence": positive_evidence,
        "exact_evidence": exact_evidence,
        "counterexamples": counterexamples,
        "route_evaluations": route_evaluations,
        "scope_events": scope_signatures,
    }


def _evidence_gain(
    before: Mapping[str, set[Any]],
    after: Mapping[str, set[Any]],
) -> dict[str, Any]:
    promoted = len(after["proved_claims"] - before["proved_claims"])
    killed = len(after["killed_routes"] - before["killed_routes"])
    scope_narrowed = len(after["scope_events"] - before["scope_events"])
    positive_evidence = len(after["positive_evidence"] - before["positive_evidence"])
    certificate_maturity = len(after["exact_evidence"] - before["exact_evidence"])
    counterexamples = len(after["counterexamples"] - before["counterexamples"])
    route_evaluations = len(after["route_evaluations"] - before["route_evaluations"])
    has_gain = any(
        value > 0
        for value in (
            promoted,
            killed,
            scope_narrowed,
            positive_evidence,
            certificate_maturity,
            counterexamples,
            route_evaluations,
        )
    )
    return {
        "promoted": promoted,
        "killed_mechanisms": killed,
        "scope_narrowed": scope_narrowed,
        "new_positive_evidence": positive_evidence,
        "certificate_maturity": certificate_maturity,
        "new_counterexamples": counterexamples,
        "new_route_evaluations": route_evaluations,
        "has_gain": has_gain,
        "semantics": (
            "Counts new semantic signatures, not new IDs. Replaying the same "
            "checker output in the same independence group is zero gain."
        ),
    }


def _budget_spent(budget: BudgetLedger | None) -> dict[str, float | int]:
    if budget is None:
        return {
            "model_calls": 0,
            "tool_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "tool_wall_seconds": 0.0,
            "cost_usd": 0.0,
        }
    return {
        "model_calls": budget.model_call_count,
        "tool_calls": budget.tool_call_count,
        "input_tokens": budget.spent_input_tokens,
        "output_tokens": budget.spent_output_tokens,
        "tool_wall_seconds": budget.spent_wall_seconds,
        "cost_usd": budget.spent_cost_usd,
    }


def _cost_delta(
    before: Mapping[str, float | int],
    after: Mapping[str, float | int],
) -> dict[str, float | int]:
    return {
        key: after[key] - before[key]
        for key in before
    }


@dataclass(slots=True)
class CampaignReport:
    rounds: tuple[dict[str, Any], ...]
    stop_reason: str
    final_metrics: dict[str, Any]
    budget: dict[str, Any] | None
    creation_log: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rounds": list(self.rounds),
            "stop_reason": self.stop_reason,
            "final_metrics": self.final_metrics,
            "budget": self.budget,
            "creation_log": list(self.creation_log),
        }


class ResearchCampaign:
    """Run a research trace through repeated rounds until it stops making progress."""

    def __init__(
        self,
        trace: ResearchTrace,
        workers: Iterable[ProposalWorker],
        *,
        orchestrator: ResearchOrchestrator | None = None,
        tool_registry: ExactToolRegistry | None = None,
        budget: BudgetLedger | None = None,
        max_rounds: int = 20,
        max_rounds_without_gain: int = 5,
        persist_path: str | Path | None = None,
        on_round_complete: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> None:
        self.trace = trace
        self.workers = tuple(workers)
        if not self.workers:
            raise ValueError("a research campaign requires at least one worker")
        roles = [worker.role for worker in self.workers]
        if len(set(roles)) != len(roles):
            raise ValueError("worker roles must be unique within a campaign")
        self.orchestrator = orchestrator or ResearchOrchestrator(trace)
        self.tool_registry = tool_registry or default_exact_tool_registry()
        self.budget = budget
        self.max_rounds = max_rounds
        self.max_rounds_without_gain = max_rounds_without_gain
        self.persist_path = Path(persist_path) if persist_path is not None else None
        self.on_round_complete = on_round_complete
        self._last_report: CampaignReport | None = None

    @property
    def last_report(self) -> CampaignReport | None:
        """The exact report object produced by this campaign's latest run."""

        return self._last_report

    def run(self) -> CampaignReport:
        rounds: list[dict[str, Any]] = []
        rounds_without_gain = 0
        stop_reason = "max_rounds_reached"

        for round_index in range(1, self.max_rounds + 1):
            metrics_before = compute_research_metrics(self.trace)
            if metrics_before["release_state"] in _TERMINAL_RELEASE_STATES:
                stop_reason = f"release_state_terminal:{metrics_before['release_state']}"
                break
            if self.budget is not None and self.budget.exhausted():
                stop_reason = "budget_exhausted"
                break

            round_record = self._run_one_round(round_index)
            rounds.append(round_record)
            if self.persist_path is not None:
                save_trace(self.trace, self.persist_path)
            if self.on_round_complete is not None:
                self.on_round_complete(round_record)

            if bool(round_record["evidence_gain"]["has_gain"]):
                rounds_without_gain = 0
            else:
                rounds_without_gain += 1
            if rounds_without_gain >= self.max_rounds_without_gain:
                stop_reason = "no_gain_rounds_exhausted"
                break
        final_metrics = compute_research_metrics(self.trace)
        report = CampaignReport(
            rounds=tuple(rounds),
            stop_reason=stop_reason,
            final_metrics=final_metrics,
            budget=self.budget.to_dict() if self.budget is not None else None,
            creation_log=tuple(self.orchestrator.creation_log),
        )
        self._last_report = report
        return report

    def _run_one_round(self, round_index: int) -> dict[str, Any]:
        metrics_before = compute_research_metrics(self.trace)
        semantic_before = _semantic_state(self.trace)
        budget_before = _budget_spent(self.budget)
        plan = self.orchestrator.plan_round()
        trace_view = build_trace_view(self.trace, plan)
        trace_view["available_exact_tools"] = list(self.tool_registry.template_ids())
        trace_view["structured_kill_tests"] = {
            route_id: spec.to_dict()
            for route_id in self.trace.claims[plan.focus_claim_id].route_ids
            if (spec := get_kill_test_spec(self.trace, route_id)) is not None
        }
        creation_log_before = len(self.orchestrator.creation_log)
        worker_reports: list[dict[str, Any]] = []

        for worker in self.workers:
            execution = worker.execute(plan, trace_view)
            self.trace.add_tool_call(execution.tool_call)
            if self.budget is not None:
                self.budget.charge_tool_call(execution.tool_call)
                if execution.model_usage is not None:
                    self.budget.charge_model_usage(execution.model_usage)

            worker_report: dict[str, Any] = {
                "role": worker.role,
                "call_id": execution.tool_call.call_id,
                "status": execution.tool_call.status.value,
                "proposal_recorded": False,
                "executed_tools": [],
                "usage_reconciliation": None,
                "error": execution.raw_stderr.strip(),
            }
            if execution.tool_call.status is ToolStatus.PASS and execution.proposal is not None:
                proposal = dict(execution.proposal)
                if self.budget is not None and execution.model_usage is not None:
                    reported_usage = proposal.get("usage_report")
                    if isinstance(reported_usage, Mapping):
                        accepted = self.budget.reconcile_self_report(
                            source=execution.tool_call.call_id,
                            reported=reported_usage,
                            metered=execution.model_usage,
                        )
                        event = {
                            "call_id": execution.tool_call.call_id,
                            "role": worker.role,
                            "consistent": accepted,
                            "reported": dict(reported_usage),
                            "metered": dict(execution.model_usage),
                            "timestamp": utc_now(),
                        }
                        worker_report["usage_reconciliation"] = event
                        history = self.trace.metadata.setdefault("usage_reconciliation", [])
                        if isinstance(history, list):
                            history.append(event)
                            self.trace.updated_at = utc_now()
                linked_calls = list(proposal.get("linked_tool_call_ids", []))
                linked_calls.append(execution.tool_call.call_id)
                proposal["linked_tool_call_ids"] = list(dict.fromkeys(linked_calls))
                linked_claims = list(proposal.get("linked_claim_ids", []))
                if plan.focus_claim_id not in linked_claims:
                    linked_claims.append(plan.focus_claim_id)
                proposal["linked_claim_ids"] = linked_claims
                try:
                    self.orchestrator.accept_agent_proposal(role=worker.role, payload=proposal)
                    worker_report["proposal_recorded"] = True
                except TraceValidationError as exc:
                    worker_report["error"] = (
                        f"{worker_report['error']}\nproposal rejected: {exc}".strip()
                    )
                for request in proposal.get("tool_requests", []):
                    if not isinstance(request, Mapping):
                        continue
                    worker_report["executed_tools"].append(
                        self._dispatch_tool_request(plan.focus_claim_id, request)
                    )
            worker_reports.append(worker_report)

        metrics_after = compute_research_metrics(self.trace)
        semantic_after = _semantic_state(self.trace)
        budget_after = _budget_spent(self.budget)
        return {
            "round_index": round_index,
            "plan": plan.to_dict(),
            "workers": worker_reports,
            "creations": list(self.orchestrator.creation_log[creation_log_before:]),
            "metrics_before": metrics_before,
            "metrics_after": metrics_after,
            "evidence_gain": _evidence_gain(semantic_before, semantic_after),
            "cost_delta": _cost_delta(budget_before, budget_after),
        }

    def _run_route_evaluation(
        self,
        *,
        claim_id: str,
        route_id: str,
        tool_call: Any,
    ) -> dict[str, Any] | None:
        if route_id not in self.trace.routes:
            return {
                "status": "ROUTE_EVALUATION_REJECTED",
                "reason": f"unknown route {route_id}",
            }
        route = self.trace.routes[route_id]
        if claim_id not in route.claim_ids:
            return {
                "status": "ROUTE_EVALUATION_REJECTED",
                "reason": f"route {route_id} is not linked to claim {claim_id}",
            }
        if get_kill_test_spec(self.trace, route_id) is None:
            return None
        try:
            record = evaluation_from_tool_call(
                self.trace,
                evaluation_id=f"ROUTE-EVAL-{tool_call.call_id}",
                route_id=route_id,
                claim_id=claim_id,
                tool_call=tool_call,
            )
            record_route_evaluation(self.trace, record)
        except FalsificationContractError as exc:
            return {"status": "ROUTE_EVALUATION_REJECTED", "reason": str(exc)}
        return {
            "status": "ROUTE_EVALUATION_RECORDED",
            "evaluation_id": record.evaluation_id,
            "outcome": record.outcome.value,
            "tested_scope": record.tested_scope,
        }

    def _dispatch_tool_request(
        self,
        claim_id: str,
        request: Mapping[str, Any],
    ) -> dict[str, Any]:
        template_id = str(request.get("tool", ""))
        route_id = str(request.get("route_id", "")).strip()
        arguments = request.get("arguments", {})
        if not isinstance(arguments, Mapping):
            arguments = {}
        try:
            result = self.tool_registry.execute(template_id, claim_id=claim_id, arguments=arguments)
        except UnknownExactToolError as exc:
            return {"template_id": template_id, "status": "REJECTED_UNKNOWN_TOOL", "reason": str(exc)}
        except ExactToolUnavailableError as exc:
            return {"template_id": template_id, "status": "REJECTED_TOOL_UNAVAILABLE", "reason": str(exc)}
        except (KeyError, ValueError, TypeError) as exc:
            return {"template_id": template_id, "status": "REJECTED_BAD_ARGUMENTS", "reason": str(exc)}

        try:
            self.trace.add_tool_call(result.tool_call)
        except TraceValidationError as exc:
            return {
                "template_id": template_id,
                "status": "REJECTED_DUPLICATE_CALL",
                "reason": str(exc),
            }
        if self.budget is not None:
            self.budget.charge_tool_call(result.tool_call)

        route_evaluation = (
            self._run_route_evaluation(
                claim_id=claim_id,
                route_id=route_id,
                tool_call=result.tool_call,
            )
            if route_id
            else None
        )

        if result.evidence is None:
            return {
                "template_id": template_id,
                "call_id": result.tool_call.call_id,
                "status": result.tool_call.status.value,
                "route_evaluation": route_evaluation,
            }

        try:
            self.trace.add_evidence(result.evidence)
        except TraceValidationError as exc:
            return {
                "template_id": template_id,
                "call_id": result.tool_call.call_id,
                "status": "EVIDENCE_REJECTED",
                "reason": str(exc),
                "route_evaluation": route_evaluation,
            }

        structured_routes = [
            item
            for item in self.trace.claims[claim_id].route_ids
            if get_kill_test_spec(self.trace, item) is not None
        ]
        blockers = promotion_route_blockers(self.trace, claim_id) if structured_routes else ()
        if blockers:
            promoted = False
            promotion_blockers = list(blockers)
        else:
            promotion_blockers = []
            try:
                self.trace.promote_claim(claim_id)
                promoted = True
            except PromotionError:
                promoted = False
        return {
            "template_id": template_id,
            "call_id": result.tool_call.call_id,
            "evidence_id": result.evidence.evidence_id,
            "status": "EVIDENCE_ACCEPTED",
            "route_evaluation": route_evaluation,
            "promotion_blockers": promotion_blockers,
            "promoted": promoted,
        }
